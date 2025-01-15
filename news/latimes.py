import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from openpyxl import Workbook
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.chrome import ChromeDriverManager

# Install ChromeDriver
chromedriver_autoinstaller.install()

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=chrome_options)

# Set up the output Excel file
wb = Workbook()
ws = wb.active
ws.append(['Title', 'Description', 'Date', 'URL'])

# Function to scrape the articles
def scrape_page(page_num):
    url = f'https://www.latimes.com/search?q=Fire&f0=00000163-01e2-d9e5-adef-33e2984a0000&s=1&p={page_num}'
    driver.get(url)
    time.sleep(3)  # Wait for the page to load

    # Find the list of articles
    articles = driver.find_elements(By.CSS_SELECTOR, 'ul.search-results-module-results-menu li')

    for article in articles:
        try:
            # Title and URL extraction
            title_element = article.find_element(By.CSS_SELECTOR, 'h3.promo-title a')
            title = title_element.text
            article_url = title_element.get_attribute('href')

            # Description extraction
            description = article.find_element(By.CSS_SELECTOR, 'p.promo-description').text

            # Date extraction
            date = article.find_element(By.CSS_SELECTOR, 'time.promo-timestamp').text

            # Append the data to the Excel sheet
            ws.append([title, description, date, article_url])

        except Exception as e:
            print(f"Error extracting data for an article: {e}")

# Loop through pages 1 to 3 (can adjust the range as needed)
for page in range(1, 4):  # Adjust the range to scrape more pages if needed
    print(f"Scraping page {page}")
    scrape_page(page)

# Save the Excel file
wb.save('latimes_fire_articles.xlsx')

# Close the browser
driver.quit()

print("Scraping complete and data saved to latimes_fire_articles.xlsx")
