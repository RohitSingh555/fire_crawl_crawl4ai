import requests
import json
from datetime import datetime, timedelta

# URL for the API to fetch articles
url = "https://api.mantis-intelligence.com/reach/search?search_text_all=fire&search_text=&search_text_none=&mantis_categories=&tags=&domains=coventrytelegraph&excluded_domains=&author=&start=0&limit=100&sort=date&indexAlias=12-months"

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
        date_obj = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ")  # Adjusting for microseconds in the date string
        return date_obj.date() == today.date() or date_obj.date() == yesterday.date()

    # Dictionary to store publisher URLs
    publisher_urls = {}

    # Define a publisher name (Coventry Telegraph)
    publisher_name = "https://www.coventrytelegraph.net"

    # Filter the articles based on date and extract URLs
    filtered_links = []
    for article in data.get('articleData', []):
        # Check if the 'lastModified' field exists and if the article is from today or yesterday
        last_modified = article.get('lastModified')
        if last_modified and is_today_or_yesterday(last_modified):
            link = article.get('url')
            if link:
                # Add the full URL with the base domain (coventrytelegraph.net)
                full_url = f"{link}"
                filtered_links.append(full_url)

    # Store the filtered links for this publisher
    publisher_urls[publisher_name] = filtered_links

    # Output the results as JSON
    output_data = json.dumps(publisher_urls, indent=4)

    # Print the filtered output
    print(output_data)

    # Save the output to a file
    with open('output3.json', 'w') as f:
        f.write(output_data)

else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")
