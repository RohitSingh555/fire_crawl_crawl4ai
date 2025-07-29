import json
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import urlparse
from dateutil import parser
import re

def extract_channel(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc.split('.')[1]

def has_invalid_characters(text):
    if isinstance(text, str):
        if re.search(r'[^\x00-\x7F]+', text) or '\ufffd' in text:
            return True
    return False

with open('all_jsons/fire_incident_results.json', 'r') as file:
    fire_incident_results = json.load(file)


today = datetime.today()
yesterday = today - timedelta(days=1)

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%d-%m-%Y")
    except ValueError:
        try:
            return parser.parse(date_str)
        except:
            return None

filtered_results = []
for item in fire_incident_results:
    date_str = item.get("Date")
    parsed_date = parse_date(date_str)
    
    title = item.get("Title")
    if not title or title == "No Title Found":
        continue

    url = item.get("URL")
   
    description = item.get("Description", "")
    
    if parsed_date and (parsed_date.date() == today.date() or parsed_date.date() == yesterday.date()):
        channel = extract_channel(url)

        filtered_results.append({
            "Title": title,
            "Description": item["Description"],
            "Date": date_str,
            "URL": url,
            "Channel": channel,
        })

df = pd.DataFrame(filtered_results)

output_filename = "filtered_fire_incidents2.xlsx"
df.to_excel(output_filename, index=False)

print(f"Excel file saved as {output_filename}")

# Send POST request with the Excel file
import requests
import json

url = 'http://localhost:8000/api/excel-uploads'
from_url = 'https://example.com/upload'  # Hardcoded value
extra = 'Sent from the scraper which scrapes websites'  # Hardcoded info

# Prepare JSON data with the scraped articles
json_data = {
    "items": []
}

for item in filtered_results:
    # Parse the date to ISO format
    date_str = item.get("Date", "")
    published_date = None
    if date_str:
        parsed_date = parse_date(date_str)
        if parsed_date:
            published_date = parsed_date.isoformat()
    
    # Create item structure matching the curl example
    json_item = {
        "title": item.get("Title", ""),
        "content": item.get("Description", ""),
        "published_date": published_date,
        "url": item.get("URL", ""),
        "source": item.get("Channel", ""),
        "fire_related_score": 0.8,  # Default score for fire-related articles
        "verification_result": "yes",  # Default verification
        "verified_at": datetime.now().isoformat(),
        "state": "",  # Could be extracted from content if needed
        "county": "",  # Could be extracted from content if needed
        "city": "",  # Could be extracted from content if needed
        "country": "USA",  # Default country
        "latitude": None,  # Could be extracted from content if needed
        "longitude": None,  # Could be extracted from content if needed
        "image_url": "",  # Could be extracted from content if needed
        "tags": "fire,emergency,news",  # Default tags
        "reporter_name": ""  # Could be extracted from content if needed
    }
    json_data["items"].append(json_item)

with open(output_filename, 'rb') as f:
    files = {'file': (output_filename, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    data = {
        'from_url': from_url, 
        'extra': extra,
        'json_data': json.dumps(json_data)
    }
    try:
        response = requests.post(url, files=files, data=data)
        print(f"POST request sent. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        print(f"Sent {len(json_data['items'])} items in JSON data")
    except Exception as e:
        print(f"Failed to send POST request: {e}")
