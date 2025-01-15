import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd

# List of websites with search URLs for "fire"
search_urls = [
    "https://www.wdsu.com/search?q=fire"
]

# Function to crawl and fetch fire-related articles
def crawl_fire_articles(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }
    articles_data = []

    try:
        # Send a request to the URL
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            if "wdsu" in url:
                articles = soup.find_all('li', class_='search-page--result')
                for article in articles:
                    title = article.find('h2').get_text(strip=True)
                    description = article.find('p').get_text(strip=True) if article.find('p') else 'No description available'
                    article_url = urljoin(url, article.find('a')['href'])
                    published_date = article.find('span').get_text(strip=True) if article.find('span') else 'Not available'
                    articles_data.append([title, description, published_date, article_url])


            else:
                print(f"No specific logic implemented for {url}")

        else:
            print(f"Failed to retrieve {url}. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error crawling {url}: {e}")
    return articles_data

all_articles = []

# Crawl each search URL
for url in search_urls:
    print(f"Crawling: {url}")
    articles = crawl_fire_articles(url)
    all_articles.extend(articles)

# Convert the data into a Pandas DataFrame
columns = ["Title", "Description", "Published Date", "URL"]
df = pd.DataFrame(all_articles, columns=columns)

# Save the DataFrame to an Excel file
output_file = "fire_news_articles.xlsx"
df.to_excel(output_file, index=False)

print(f"Crawling completed. Fire-related articles saved to '{output_file}'.")
