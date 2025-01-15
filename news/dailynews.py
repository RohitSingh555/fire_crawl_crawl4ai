from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from openpyxl import Workbook
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller

# Install ChromeDriver
chromedriver_autoinstaller.install()

# Set Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# Initialize WebDriver
driver = webdriver.Chrome(options=chrome_options)

# Set up the output Excel file
wb = Workbook()
ws = wb.active
ws.append(['Title', 'Description', 'Date', 'URL'])

# Function to scrape articles from the current page
def scrape_articles():
    # Print page HTML for debugging
    print(driver.page_source)

    # Wait for the article elements to load
    articles = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article'))
    )

    for article in articles:
        try:
            # Title and URL extraction
            title_element = article.find_element(By.CSS_SELECTOR, 'a.article-title')
            title = title_element.get_attribute('title')
            article_url = title_element.get_attribute('href')

            # Description extraction with fallback
            try:
                description_element = article.find_element(By.CSS_SELECTOR, 'div.excerpt')
                description = description_element.text.strip()
            except:
                description = 'No description available'

            # Date extraction
            try:
                date_element = article.find_element(By.CSS_SELECTOR, 'time')
                date = date_element.text.strip()
            except:
                date = 'No date available'

            # Append the data to the Excel sheet
            ws.append([title, description, date, article_url])

        except Exception as e:
            print(f"Error extracting data for an article: {e}")

# Function to navigate to the page URL and scrape
def scrape_page(page_number):
    url = f"https://www.dailynews.com/page/{page_number}/?s=fire&orderby=date&order=desc"
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'article'))
    )
    scrape_articles()

# Loop through pages 1 to 5
for page in range(1, 6):
    print(f"Scraping page {page}...")
    scrape_page(page)

# Save the data to an Excel file
wb.save('dailynews_fire_articles_page_1_to_5.xlsx')

# Close the browser
driver.quit()

print("Scraping complete and data saved to dailynews_fire_articles_page_1_to_5.xlsx")
