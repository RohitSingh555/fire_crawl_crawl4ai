from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import time

def fetch_news_from_site(url, search_term="fire"):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(url + search_term)
    time.sleep(3)
    
    articles = []

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Example for ABC News (similar logic can be applied for other sites)
    for item in soup.find_all('article'):
        title_tag = item.find('h2')
        if title_tag:
            title = title_tag.get_text(strip=True)
            link = title_tag.find('a')['href']
            description = item.find('p').get_text(strip=True) if item.find('p') else 'No description available'
            
            # Published date extraction (if available)
            published_date = "Not available"
            date_tag = item.find('time')
            if date_tag and date_tag.get('datetime'):
                published_date = date_tag['datetime']

            articles.append({
                'Title': title,
                'Link': link,
                'Description': description,
                'Published Date': published_date
            })

    driver.quit()
    return articles

def get_news_from_multiple_sources():
    news_channels = [
        ("ABC News", "https://abcnews.go.com/search?searchtext="),
        ("CBS News", "https://www.cbsnews.com/search?q="),
        ("Fox News", "https://www.foxnews.com/search-results/search?q="),
        
        ("NBC News", "https://www.nbcnews.com/search/?q="),
        ("USA Today", "https://www.usatoday.com/search/?q="),
        ("New York Times", "https://www.nytimes.com/search?query=")
    ]
    
    all_articles = []

    # Iterate through each news channel and fetch articles
    for channel, url in news_channels:
        print(f"Fetching news from {channel}...")
        articles = fetch_news_from_site(url)
        for article in articles:
            article['Channel'] = channel  # Add channel name for reference
        all_articles.extend(articles)
    
    return all_articles

def save_to_excel(articles, filename="us_news_fire.xlsx"):
    # Convert articles to DataFrame
    df = pd.DataFrame(articles)

    # Save DataFrame to Excel file
    df.to_excel(filename, index=False)
    print(f"Data saved to {filename}")

# Fetch news from multiple sources
articles = get_news_from_multiple_sources()

# Save the articles to an Excel file
save_to_excel(articles)
