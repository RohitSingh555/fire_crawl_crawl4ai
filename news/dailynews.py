from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from openpyxl import Workbook
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller
from urllib.parse import urlparse
import json

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

def scrape_articles():
    articles = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article'))
    )

    for article in articles:
        try:
            title_element = article.find_element(By.CSS_SELECTOR, 'a.article-title')
            title = title_element.get_attribute('title')
            article_url = title_element.get_attribute('href')

            try:
                description_element = article.find_element(By.CSS_SELECTOR, 'div.excerpt')
                description = description_element.text.strip()
            except:
                description = 'No description available'

            try:
                date_element = article.find_element(By.CSS_SELECTOR, 'time')
                date = date_element.text.strip()
            except:
                date = 'No date available'

            ws.append([title, description, date, article_url])

            domain = urlparse(article_url).netloc
            if domain not in url_dict:
                url_dict[domain] = []
            url_dict[domain].append(article_url)

        except Exception as e:
            print(f"Error extracting data for an article: {e}")

def scrape_page(page_number):
    url = f"https://www.dailynews.com/page/{page_number}/?s=fire&orderby=date&order=desc"
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'article'))
    )
    scrape_articles()

for page in range(1, 6):
    print(f"Scraping page {page}...")
    scrape_page(page)

wb.save('dailynews_fire_articles_page_1_to_5.xlsx')

with open('dailynews_fire_urls.json', 'w') as json_file:
    json.dump(url_dict, json_file, indent=4)

driver.quit()

print("Scraping complete and data saved to dailynews_fire_articles_page_1_to_5.xlsx")
print("URLs saved to dailynews_fire_urls.json.")
