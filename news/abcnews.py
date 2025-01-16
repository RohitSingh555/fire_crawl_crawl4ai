import time 
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import re

chromedriver_autoinstaller.install()

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=chrome_options)

def convert_relative_to_absolute(date_str):
    today = datetime.today()
    days_ago_match = re.match(r'(\d+)\s*days?\s*ago', date_str)
    if days_ago_match:
        days_ago = int(days_ago_match.group(1))
        return today - timedelta(days=days_ago)
    
    day_ago_match = re.match(r'1\s*day?\s*ago', date_str)
    if day_ago_match:
        return today - timedelta(days=1)
    
    hours_ago_match = re.match(r'(\d+)\s*hours?\s*ago', date_str)
    if hours_ago_match:
        hours_ago = int(hours_ago_match.group(1))
        return today - timedelta(hours=hours_ago)
    
    return today

def is_today_or_yesterday(date):
    today = datetime.today().strftime('%Y-%m-%d')
    yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    return date == today or date == yesterday

def fetch_fox_news(url):
    driver.get(url)
    time.sleep(5)
    articles = driver.find_elements(By.CSS_SELECTOR, 'article.article')
    article_data = []
    
    for article in articles:
        try:
            title = article.find_element(By.CSS_SELECTOR, 'h2.title').text.strip()
            link = article.find_element(By.CSS_SELECTOR, 'h2.title a').get_attribute('href')
        except Exception as e:
            title = 'No title'
            link = 'No link'
        
        try:
            description = article.find_element(By.CSS_SELECTOR, 'p.dek').text.strip()
        except Exception as e:
            description = 'No description available'
        
        try:
            relative_date = article.find_element(By.CSS_SELECTOR, 'span.time').text.strip()
            date = convert_relative_to_absolute(relative_date).strftime('%Y-%m-%d')
        except Exception as e:
            date = 'No date available'
        
        if title and link and is_today_or_yesterday(date):
            article_data.append({
                'Title': title,
                'Link': link,
                'Description': description,
                'Date': date,
                'Channel': 'Fox News'
            })
    
    if article_data:
        return pd.DataFrame(article_data)
    else:
        print("No articles found for Fox News.")
        return None

def scrape_abc_news_selenium(url_base, start_page, end_page):
    all_article_data = []
    today_date = datetime.today().strftime('%Y-%m-%d')
    
    for page in range(start_page, end_page + 1):
        url = f"{url_base}&page={page}"
        driver.get(url)
        time.sleep(5)
        
        articles = driver.find_elements(By.CSS_SELECTOR, 'section.ContentRoll__Item')
        article_data = []

        for article in articles:
            try:
                title = article.find_element(By.CSS_SELECTOR, 'h2 a').text.strip()
                link = article.find_element(By.CSS_SELECTOR, 'h2 a').get_attribute('href')
            except Exception as e:
                title = 'No title'
                link = 'No link'

            try:
                description = article.find_element(By.CSS_SELECTOR, 'div.ContentRoll__Desc').text.strip()
            except Exception as e:
                description = 'No description available'

            date = today_date

            if title and link and is_today_or_yesterday(date):
                article_data.append({
                    'Title': title,
                    'Link': link,
                    'Description': description,
                    'Date': date,
                    'Channel': 'ABC News'
                })

        if article_data:
            all_article_data.extend(article_data)
        else:
            print(f"No articles found for page {page}.")
    
    if all_article_data:
        return pd.DataFrame(all_article_data)
    else:
        print("No articles found for the given page range.")
        return None

def scrape_azfamily_fire_news(url):
    driver.get(url)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    articles = soup.find_all('div', class_='queryly_item_row')
    article_data = []

    for article in articles:
        try:
            title = article.find('div', class_='queryly_item_title').text.strip()
            link = article.find('a')['href']
        except Exception as e:
            title = 'No title'
            link = 'No link'
        
        try:
            description = article.find('div', class_='queryly_item_description').text.strip()
        except Exception as e:
            description = 'No description available'
        
        try:
            date_element = article.find('div', style="margin-top:6px;color:#555;font-size:12px;")
            date = date_element.text.strip() if date_element else 'No date available'
        except Exception as e:
            date = 'No date available'

        if title and link and is_today_or_yesterday(date):
            article_data.append({
                'Title': title,
                'Link': 'https://www.azfamily.com' + link,
                'Description': description,
                'Date': date,
                'Channel': 'AZ Family'
            })

    if article_data:
        return pd.DataFrame(article_data)
    else:
        print("No articles found for AZ Family News.")
        return None

def save_to_excel(fox_news_df, abc_news_df, azfamily_news_df):
    all_articles = pd.concat([fox_news_df, abc_news_df, azfamily_news_df], ignore_index=True)
    all_articles.to_excel('combined_news_data.xlsx', index=False)
    print("Data saved to combined_news_data.xlsx")

import json

def extract_urls_and_save_to_json(fox_news_df, abc_news_df, azfamily_news_df):
    url_dict = {}

    if fox_news_df is not None:
        for _, row in fox_news_df.iterrows():
            channel_url = row['Link'].split('/')[2]  
            if channel_url not in url_dict:
                url_dict[channel_url] = []
            url_dict[channel_url].append(row['Link'])

    if abc_news_df is not None:
        for _, row in abc_news_df.iterrows():
            channel_url = row['Link'].split('/')[2]  
            if channel_url not in url_dict:
                url_dict[channel_url] = []
            url_dict[channel_url].append(row['Link'])

    if azfamily_news_df is not None:
        for _, row in azfamily_news_df.iterrows():
            channel_url = row['Link'].split('/')[2]  
            if channel_url not in url_dict:
                url_dict[channel_url] = []
            url_dict[channel_url].append(row['Link'])

    with open('news_urls.json', 'w') as json_file:
        json.dump(url_dict, json_file, indent=4)
    print("URLs saved to news_urls.json")



fox_news_url = 'https://www.foxnews.com/search-results/search?q=fire'
abc_news_url_base = 'https://abcnews.go.com/search?searchtext=fire&section=US&sort=date'
azfamily_url = 'https://www.azfamily.com/search/?query=fire'

fox_news_df = fetch_fox_news(fox_news_url)
abc_news_df = scrape_abc_news_selenium(abc_news_url_base, 1, 5)
azfamily_news_df = scrape_azfamily_fire_news(azfamily_url)
extract_urls_and_save_to_json(fox_news_df, abc_news_df, azfamily_news_df)

save_to_excel(fox_news_df, abc_news_df, azfamily_news_df)
