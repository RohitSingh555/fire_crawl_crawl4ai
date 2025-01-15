import requests
from readability import Readability
from bs4 import BeautifulSoup
from datetime import datetime
import json

# List of websites to scrape (you can add more)
websites = [
    "https://www.latimes.com",
    "https://www.dailynews.com",
    "https://www.laweekly.com",
    "https://www.ladowntownnews.com",
    "https://www.glendalenewspress.com",
    "https://www.burbankleader.com",
]

# Function to extract readable content from a URL
def extract_readable_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Use readability-lxml to extract content
        read = Readability(response.content)
        doc = read.doc()  # Extract readable content
        
        # Get the title, date, and content
        title = soup.title.string if soup.title else "No title"
        description = doc['content']  # Extract the main content
        date = None  # Try to extract date (if any) from the article's meta tags
        
        for meta in soup.find_all('meta'):
            if 'date' in meta.attrs.get('name', '').lower():
                date = meta.attrs.get('content', None)
                break
        
        # If no date is found, use the current date
        if not date:
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            "url": url,
            "title": title,
            "description": description,
            "date": date
        }
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

# Scrape news from all websites and filter for fire-related news
def scrape_fire_news():
    fire_news = []
    
    for website in websites:
        print(f"Scraping {website}...")
        news_article = extract_readable_content(website)
        
        if news_article:
            # Check if the article is related to fire using simple keyword search (you can enhance this)
            if 'fire' in news_article['title'].lower() or 'fire' in news_article['description'].lower():
                fire_news.append(news_article)
    
    return fire_news

# Save the results to a JSON file
def save_to_json(data, filename='fire_news.json'):
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# Main function to run the script
if __name__ == "__main__":
    print("Starting the fire news scraping...")
    fire_news = scrape_fire_news()
    
    if fire_news:
        print(f"Found {len(fire_news)} fire-related articles.")
        save_to_json(fire_news)
    else:
        print("No fire-related news found.")

