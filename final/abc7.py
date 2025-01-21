import requests
import json
from datetime import datetime, timedelta

# URL for the API to fetch articles and videos
url = "https://abc7.com/proxy/distro/search/?query=fire&apiEnv=production&platform=web&brand=kabc&types=article%2Cvideo%2Cphotogallery&limit=20&offset=15"

# Make a GET request to fetch the data
response = requests.get(url)

if response.status_code == 200:
    # Load the response JSON
    data = response.json()
    
    # Current date and yesterday's date for filtering
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    # Function to check if the date is today's or yesterday's
    def is_today_or_yesterday(date_string):
        date_obj = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
        return date_obj.date() == today.date() or date_obj.date() == yesterday.date()

    # Dictionary to store publisher URLs
    publisher_urls = {}

    # Define a publisher name (you can adjust based on the source, here 'ABC7' is used)
    publisher_name = "https://www.abc7.com"

    # Filter the articles/videos based on date
    filtered_links = []
    for item in data.get('results', []):
        # Check if the 'created' field exists and if the article/video is from today or yesterday
        created_date = item['data'].get('created')
        if created_date and is_today_or_yesterday(created_date):
            link = item['data'].get('webUrl') or item['data'].get('locator')
            if link:
                filtered_links.append(link)

    # Store the filtered links for this publisher
    publisher_urls[publisher_name] = filtered_links

    # Output the results as JSON
    output_data = json.dumps(publisher_urls, indent=4)

    # Print the filtered output
    print(output_data)

    # Save the output to a file
    with open('output1.json', 'w') as f:
        f.write(output_data)

else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")
