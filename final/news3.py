import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
from urllib.parse import urlparse, urljoin
import json
import pandas as pd
import time
import random

# Initialize Excel workbook
wb = Workbook()
ws = wb.active
ws.append(['Title', 'Description', 'Date', 'URL'])

url_dict = {}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36"
]

websites = [
    "https://www.dcnewsnow.com/?submit=&s=fire",
    "https://www.texasobserver.org/?s=fire&button&daterange=pastweek",
]

# Function to scrape articles from Los Angeles Times
def scrape_latimes(page_num):
    url = f'https://www.latimes.com/search?q=Fire&f0=00000163-01e2-d9e5-adef-33e2984a0000&s=1&p={page_num}'
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.latimes.com/'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve LATimes page {page_num}, status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.select('ul.search-results-module-results-menu li')

    for article in articles:
        try:
            title_element = article.select_one('h3.promo-title a')
            title = title_element.text.strip() if title_element else ""
            article_url = title_element['href'] if title_element else ""
            parsed_url = urlparse(article_url)
            domain = parsed_url.netloc
            if domain not in url_dict:
                url_dict[domain] = []
            url_dict[domain].append(article_url)
            ws.append([article_url])
        except Exception as e:
            print(f"Error extracting data for a LATimes article: {e}")

# Function to scrape articles from Daily News
def scrape_dailynews(page_number):
    url = f"https://www.dailynews.com/page/{page_number}/?s=fire&orderby=date&order=desc"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve DailyNews page {page_number}, status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    articles = soup.find_all('article')

    for article in articles:
        try:
            title_element = article.find('a', class_='article-title')
            title = title_element.get('title') if title_element else ""
            article_url = title_element.get('href') if title_element else ""
            ws.append([article_url])
            domain = urlparse(article_url).netloc
            if domain not in url_dict:
                url_dict[domain] = []
            url_dict[domain].append(article_url)

        except Exception as e:
            print(f"Error extracting data for a DailyNews article: {e}")

def fetch_articles(url, session):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }

    try:
        response = session.get(url, headers=headers, timeout=10)
        if response.status_code == 403:
            print(f"403 Error encountered at {url}. Retrying...")
            time.sleep(random.uniform(3, 5))
            response = session.get(url, headers=headers, timeout=10)

        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - {url}")
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err} - {url}")
    return None

def extract_articles(soup, base_url):
    articles = []
    if not soup:
        return articles

    for item in soup.find_all('article'):
        title = item.find('h2').get_text(strip=True) if item.find('h2') else None
        description = item.find('p').get_text(strip=True) if item.find('p') else None
        date = item.find('time').get_text(strip=True) if item.find('time') else None
        link = item.find('a', href=True)['href'] if item.find('a', href=True) else None

        if title and description and date and link:
            link = urljoin(base_url, link)
            articles.append({
                'Title': title,
                'Description': description,
                'Published Date': date,
                'URL': link
            })

    return articles

def scrape_fire_news(websites):
    all_articles = []
    session = requests.Session()

    for website in websites:
        print(f"Scraping {website}...")
        soup = fetch_articles(website, session)
        articles = extract_articles(soup, website)
        for article in articles:
            ws.append([article['URL']])
            article_url = article['URL']
            domain = urlparse(article_url).netloc
            if domain not in url_dict:
                url_dict[domain] = []
            url_dict[domain].append(article_url)

        time.sleep(random.uniform(1, 3))

    return all_articles

for page in range(1, 4):
    print(f"Scraping LATimes page {page}...")
    scrape_latimes(page)

for page in range(1, 6):
    print(f"Scraping Daily News page {page}...")
    scrape_dailynews(page)

scrape_fire_news(websites)

with open('combined_fire_urls.json', 'w') as json_file:
    json.dump(url_dict, json_file, indent=4)

print("Scraping complete and data saved to combined_fire_articles.xlsx")
print("URLs saved to combined_fire_urls.json.")
