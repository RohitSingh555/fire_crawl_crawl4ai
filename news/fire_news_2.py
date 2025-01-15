from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from datetime import datetime
import json

# Set up the Chrome WebDriver
driver = webdriver.Chrome()

def scrape_data(url):
    driver.get(url)

    try:
        # Wait for the meta description to load
        description_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "meta[name='description']"))
        )
        description = description_element.get_attribute("content")
    except:
        description = "No description found."

    # Fetch the title
    title = driver.title

    # Get the current date and time for when this was fetched
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S-%z")

    # Return the data as a dictionary
    return {
        "Title": title,
        "URL": url,
        "Date": current_datetime,
        "Description": description
    }

# Load the URLs from the 'urls_and_dates.json' file
with open('urls_and_dates.json', 'r') as json_file:
    urls_data = json.load(json_file)

# List to hold all the scraped data
all_data = []

# Loop through each URL and scrape the data
for entry in urls_data:
    url = entry["url"]
    data = scrape_data(url)
    all_data.append(data)

# Create a DataFrame from the scraped data
df = pd.DataFrame(all_data)

# Save the data to an Excel file
df.to_excel('scraped_data.xlsx', index=False)

# Close the browser
driver.quit()

print("Scraping complete. Data saved to scraped_data.xlsx.")
