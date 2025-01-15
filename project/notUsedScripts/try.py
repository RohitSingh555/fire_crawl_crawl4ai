from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import os
import time
import json
import openai
import logging
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# List of websites to scrape
websites = [
    "https://www.latimes.com",
    "https://www.dailynews.com",
]

def get_driver():
    """Initialize a headless Chrome driver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def fetch_page_content(url):
    """Fetch the main article content, title, description, and date from a URL."""
    driver = get_driver()
    driver.get(url)
    time.sleep(3)

    title = driver.title

    description = ""
    try:
        description = driver.find_element(By.XPATH, '//meta[@name="description"]').get_attribute('content')
    except Exception as e:
        print(f"No meta description found for {url}: {e}")

    date = ""
    try:
        date = driver.find_element(By.XPATH, '//time').text
    except Exception as e:
        print(f"No date found for {url}: {e}")

    # Extract main content using a specific selector (update as needed)
    try:
        # For example, this can be the main article body, usually in a <div> with specific class names
        body_content = driver.find_element(By.CSS_SELECTOR, 'div.article-body').text
    except Exception as e:
        print(f"No main article content found for {url}: {e}")
        body_content = ""

    driver.quit()

    return title, description, date, body_content, url

def extract_fire_news(page_content):
    """Use GPT to extract fire-related news from the given content."""
    print(page_content)
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Extract all fire-related news articles from the following content. Each article should include title, date, description, and URL.\n\n{page_content}"}
    ]
    
    try:
        ai_response =client.chat.completions.create(
            model='gpt-4',
            messages=messages,
            max_tokens=1500,
            temperature=0.7,
            n=1,
            stop=None
        )

        answer = ai_response.choices[0].message['content'].strip()

        logging.info(f"AI response: {answer}")
        print(answer)
        return json.loads(answer)
    
    except Exception as e:
        logging.error(f"Error extracting fire news: {e}")
        return None

def scrape_fire_news():
    """Scrape news from the websites and extract fire-related information."""
    fire_news = []
    for website in websites:
        print(f"Scraping {website}")
        title, description, date, page_content, url = fetch_page_content(website)

        if page_content:
            extracted_news = extract_fire_news(page_content)
            if extracted_news:
                article_info = {
                    "title": title,
                    "description": description,
                    "date": date,
                    "url": url,
                    "extracted_news": extracted_news
                }
                fire_news.append(article_info)
        time.sleep(3)
    return fire_news

def save_to_json(fire_news):
    """Save the extracted fire news to a JSON file."""
    with open('fire_news.json', 'w') as f:
        json.dump(fire_news, f, indent=4)
    print("Saved fire news to 'fire_news.json'.")

if __name__ == "__main__":
    fire_news = scrape_fire_news()
    save_to_json(fire_news)
