from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import time
import json  # Import json module to save data

# Initialize WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode (no browser window)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# URL of the page that contains the table with URLs and dates
page_url = 'https://firenews.com/wp-sitemap-posts-post-3.xml'

# Fetch the page with Selenium
driver.get(page_url)

# Wait for the page to load
time.sleep(2)

# Extract the page content
page_source = driver.page_source

# Close the WebDriver
driver.quit()

# Use BeautifulSoup to parse the page content
soup = BeautifulSoup(page_source, 'html.parser')

# Print out the first 1000 characters of the page source to inspect the structure
print("Page content preview:")
print(page_source[:1000])

# Get the current date and the date 7 days ago, make it timezone-aware
tz = pytz.timezone('US/Eastern')
today = datetime.now(tz)  # Offset-aware datetime with timezone information
seven_days_ago = today - timedelta(days=7)

# Try to find the table and its rows
table = soup.find('table')  # Modify this selector based on actual page structure
if table:
    rows = table.find_all('tr')

    # Prepare lists to hold extracted URLs and dates
    urls = []
    dates = []

    # Loop through the rows and extract the URL and date from each row
    for row in rows:
        cols = row.find_all('td')
        if len(cols) > 1:
            url = cols[0].get_text(strip=True)  # Assuming URL is in the first column
            date_str = cols[1].get_text(strip=True)  # Assuming date is in the second column

            # Convert date string to datetime object and make it timezone-aware
            try:
                date = datetime.fromisoformat(date_str)  # Assuming the date is in ISO 8601 format
            except ValueError:
                continue  # If date format is invalid, skip this row
            
            # Check if the date is within the last 7 days
            if date >= seven_days_ago:
                urls.append(url)  # Add URL to the list
                dates.append(date)
    
    # Create a dictionary of URLs and their corresponding dates
    data = [{"url": url, "date": date.isoformat()} for url, date in zip(urls, dates)]

    # Save the data to a JSON file
    with open('urls_and_dates.json', 'w') as json_file:
        json.dump(data, json_file, indent=4)

    print("Data saved to 'urls_and_dates.json'")

else:
    print("No table found on the page.")
