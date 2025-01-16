import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin, urlparse
import time
import random
import json

websites = [
    "https://www.dcnewsnow.com/?submit=&s=fire",
    "https://www.texasobserver.org/?s=fire&button&daterange=pastweek",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36"
]

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
    url_dict = {}
    session = requests.Session()

    for website in websites:
        print(f"Scraping {website}...")
        soup = fetch_articles(website, session)
        articles = extract_articles(soup, website)
        all_articles.extend(articles)

        for article in articles:
            article_url = article['URL']
            domain = urlparse(article_url).netloc
            if domain not in url_dict:
                url_dict[domain] = []
            url_dict[domain].append(article_url)

        time.sleep(random.uniform(1, 3))

    return all_articles, url_dict

fire_news_articles, url_dict = scrape_fire_news(websites)

df = pd.DataFrame(fire_news_articles)
df.to_excel("fire_news_articles.xlsx", index=False)
print("Scraping completed. Articles saved to 'fire_news_articles.xlsx'.")

with open('fire_news_urls.json', 'w') as json_file:
    json.dump(url_dict, json_file, indent=4)
print("URLs saved to 'fire_news_urls.json'.")
