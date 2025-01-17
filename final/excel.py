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

with open('fire_incident_results.json', 'r') as file:
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
    if has_invalid_characters(description):
        continue
    
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
