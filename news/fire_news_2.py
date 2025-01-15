from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from datetime import datetime

# Initialize Selenium WebDriver (make sure to have the correct driver installed)
driver = webdriver.Chrome()  # Use the appropriate WebDriver for your browser

# Function to scrape data from a single URL
def scrape_data(url):
    # Open the URL
    driver.get(url)

    # Wait until the description is available (adjust this selector based on your findings)
    try:
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

    # Create the JSON object
    data = {
        "title": title,
        "description": description,
        "url": url,
        "date": current_datetime
    }

    return data

# Load the URLs and dates from the 'urls_and_dates.json' file
with open('urls_and_dates.json', 'r') as json_file:
    urls_data = json.load(json_file)

# List to hold all the scraped data
all_data = []

# Loop through each URL and scrape data
for entry in urls_data:
    url = entry["url"]
    data = scrape_data(url)
    all_data.append(data)

# Output the data as JSON to a new file 'scraped_data.json'
with open('scraped_data.json', 'w') as json_file:
    json.dump(all_data, json_file, indent=4)

# Close the browser
driver.quit()
