import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import time
import random

# List of websites to scrape
websites = [
    "https://www.dcnewsnow.com/?submit=&s=fire",
    "https://www.texasobserver.org/?s=fire&button&daterange=pastweek",
]

# User-Agent List for Randomization
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36"
]

# Function to fetch and parse articles from a given URL
def fetch_articles(url, session):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),  # Random User-Agent
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }
    
    try:
        response = session.get(url, headers=headers, timeout=10)
        # Check for 403 error and retry if encountered
        if response.status_code == 403:
            print(f"403 Error encountered at {url}. Retrying...")
            time.sleep(random.uniform(3, 5))  # Sleep before retry
            response = session.get(url, headers=headers, timeout=10)

        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - {url}")
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err} - {url}")
    return None

# Function to extract articles based on website structure
def extract_articles(soup, base_url):
    articles = []
    if not soup:
        return articles

    # Example extraction logic for a generic news website
    for item in soup.find_all('article'):
        title = item.find('h2').get_text(strip=True) if item.find('h2') else None
        description = item.find('p').get_text(strip=True) if item.find('p') else None
        date = item.find('time').get_text(strip=True) if item.find('time') else None
        link = item.find('a', href=True)['href'] if item.find('a', href=True) else None
        
        # Only add the article if all fields are valid
        if title and description and date and link:
            link = urljoin(base_url, link)
            articles.append({
                'Title': title,
                'Description': description,
                'Published Date': date,
                'URL': link
            })
    
    return articles

# Main function to iterate over websites and compile articles
def scrape_fire_news(websites):
    all_articles = []
    session = requests.Session()  # Use session to maintain cookies and headers

    for website in websites:
        print(f"Scraping {website}...")
        soup = fetch_articles(website, session)
        articles = extract_articles(soup, website)
        all_articles.extend(articles)
        # Random sleep to prevent being blocked
        time.sleep(random.uniform(1, 3))

    return all_articles

# Execute the scraping process
fire_news_articles = scrape_fire_news(websites)

# Save the articles to an Excel file
df = pd.DataFrame(fire_news_articles)
df.to_excel("fire_news_articles.xlsx", index=False)
print("Scraping completed. Articles saved to 'fire_news_articles.xlsx'.")
