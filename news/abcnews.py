import time
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.chrome import ChromeDriverManager

# Install ChromeDriver
chromedriver_autoinstaller.install()

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=chrome_options)

# Fetch Fox News articles
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
            date = article.find_element(By.CSS_SELECTOR, 'span.time').text.strip()
        except Exception as e:
            date = 'No date available'
        
        if title and link:
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

# Fetch ABC News articles
def scrape_abc_news_selenium(url):
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

        try:
            date = article.find_element(By.CSS_SELECTOR, 'div.ContentRoll__Date--recent').text.strip()
        except Exception as e:
            date = 'No date available'

        if title and link:
            article_data.append({
                'Title': title,
                'Link': link,
                'Description': description,
                'Date': date,
                'Channel': 'ABC News'
            })

    if article_data:
        return pd.DataFrame(article_data)
    else:
        print("No articles found for ABC News.")
        return None

# Fetch AZ Family News articles based on a search query
def scrape_azfamily_fire_news(url):
    driver.get(url)
    time.sleep(5)  # Wait for the page to load completely
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
        
        # Extract date from inline style
        try:
            date_element = article.find('div', style="margin-top:6px;color:#555;font-size:12px;")
            date = date_element.text.strip() if date_element else 'No date available'
        except Exception as e:
            date = 'No date available'

        if title and link:
            article_data.append({
                'Title': title,
                'Link': 'https://www.azfamily.com' + link,  # Full URL
                'Description': description,
                'Date': date,
                'Channel': 'AZ Family'
            })

    if article_data:
        return pd.DataFrame(article_data)
    else:
        print("No articles found for AZ Family News.")
        return None

# Save data to Excel
def save_to_excel(fox_news_df, abc_news_df, azfamily_news_df):
    if fox_news_df is not None and abc_news_df is not None and azfamily_news_df is not None:
        all_articles = pd.concat([fox_news_df, abc_news_df, azfamily_news_df], ignore_index=True)
        all_articles.to_excel('combined_news_data.xlsx', index=False)
        print("Data saved to combined_news_data.xlsx")
    else:
        print("Error: One or more dataframes are empty.")

# URLs
fox_news_url = 'https://www.foxnews.com/search-results/search?q=fire'
abc_news_url = 'https://abcnews.go.com/search?searchtext=fire&after=today&section=US'
azfamily_url = 'https://www.azfamily.com/search/?query=fire'

# Fetch data from all sources
fox_news_df = fetch_fox_news(fox_news_url)
abc_news_df = scrape_abc_news_selenium(abc_news_url)
azfamily_news_df = scrape_azfamily_fire_news(azfamily_url)

# Save the data to Excel
save_to_excel(fox_news_df, abc_news_df, azfamily_news_df)

# Quit the driver
driver.quit()
