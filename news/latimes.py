import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from openpyxl import Workbook
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
from urllib.parse import urlparse

chromedriver_autoinstaller.install()

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=chrome_options)

wb = Workbook()
ws = wb.active
ws.append(['Title', 'Description', 'Date', 'URL'])

url_dict = {}

def scrape_page(page_num):
    url = f'https://www.latimes.com/search?q=Fire&f0=00000163-01e2-d9e5-adef-33e2984a0000&s=1&p={page_num}'
    driver.get(url)
    time.sleep(3)

    articles = driver.find_elements(By.CSS_SELECTOR, 'ul.search-results-module-results-menu li')

    for article in articles:
        try:
            title_element = article.find_element(By.CSS_SELECTOR, 'h3.promo-title a')
            title = title_element.text
            article_url = title_element.get_attribute('href')

            parsed_url = urlparse(article_url)
            domain = parsed_url.netloc

            if domain not in url_dict:
                url_dict[domain] = []
            url_dict[domain].append(article_url)

            description = article.find_element(By.CSS_SELECTOR, 'p.promo-description').text

            date = article.find_element(By.CSS_SELECTOR, 'time.promo-timestamp').text

            ws.append([title, description, date, article_url])

        except Exception as e:
            print(f"Error extracting data for an article: {e}")

for page in range(1, 4):
    print(f"Scraping page {page}")
    scrape_page(page)

wb.save('latimes_fire_articles.xlsx')

with open('latimes_article_urls.json', 'w') as json_file:
    json.dump(url_dict, json_file, indent=4)

driver.quit()

print("Scraping complete, data saved to latimes_fire_articles.xlsx and latimes_article_urls.json")
