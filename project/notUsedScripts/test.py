import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller

# Automatically download the correct ChromeDriver
chromedriver_autoinstaller.install()

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run browser in headless mode (no UI)
chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
chrome_options.add_argument("--no-sandbox")  # Bypass OS security model (for some systems)

# Initialize the WebDriver (This will use the automatically installed ChromeDriver)
driver = webdriver.Chrome(options=chrome_options)

# URL of the ABC News search results for fire-related stories
# url = 'https://abcnews.go.com/search?searchtext=fire&after=today&section=US'
# url = 'https://www.dallasobserver.com/dallas/Search?keywords=fire'

# Function to scrape news articles from ABC News
def scrape_abc_news_selenium(url):
    # Open the webpage
    driver.get(url)

    # Wait for the page to fully load (you may need to adjust this based on your connection speed)
    time.sleep(5)

    # Find all article containers or links that represent articles on the page
    articles = driver.find_elements(By.CSS_SELECTOR, 'a[href*="abcnews.go.com"]')

    # Store the article titles, links, descriptions, and publication dates
    article_data = []
    for article in articles:
        title = article.text.strip()
        link = article.get_attribute('href')
        
        # Try to find the description and date (may need to inspect the page structure more thoroughly)
        description = ''
        date = ''
        
        # In some cases, descriptions might be found within nearby elements like paragraph tags
        try:
            description = article.find_element(By.XPATH, './following-sibling::p').text.strip()
        except:
            description = 'No description available'
        
        # Date might be located in a different place; typically, you'd check for time elements
        try:
            date = article.find_element(By.XPATH, './following-sibling::span').text.strip()
        except:
            date = 'No date available'
        
        # Skip empty titles or links
        if title and link:
            article_data.append({
                'Title': title,
                'Link': link,
                'Description': description,
                'Date': date
            })

    # Return the article data as a pandas DataFrame
    if article_data:
        df = pd.DataFrame(article_data)
        return df
    else:
        print("No articles found.")
        return None

# Scrape the data
news_df = scrape_abc_news_selenium(url)

# Check if any data was scraped and print it
if news_df is not None:
    print(news_df)

    # Optionally, save the data to a CSV file
    news_df.to_csv('abc_news_articles_selenium.csv', index=False)
    print("Data saved to abc_news_articles_selenium.csv")

# Close the browser session
driver.quit()
