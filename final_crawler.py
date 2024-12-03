import json
import requests
from bs4 import BeautifulSoup
import time
import logging
import os
from datetime import datetime, timedelta
from openai import OpenAI
from threading import Lock
import re
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

fire_keywords = [
    'fire', 'blaze', 'burn', 'wildfire', 'inferno', 'smoke', 'flames', 'arson',
    'brushfire', 'house-fire', 'forest-fire', 'building-fire', 'firefighters'
]

output_file = f'fire_incidents_{datetime.today().strftime("%Y-%m-%d")}.json'
output_lock = Lock()
processed_urls = set()

def load_cleaned_websites():
    try:
        with open('cleaned_websites.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [entry['url'] for entry in data if 'url' in entry]
    except Exception as e:
        logging.error(f"Error loading cleaned websites: {e}")
        return []

def get_today_and_yesterday_dates():
    today = datetime.today().strftime('%d-%m-%Y')
    yesterday = (datetime.today() - timedelta(days=1)).strftime('%d-%m-%Y')
    return today, yesterday

def process_article(article_url):
    try:
        if article_url in processed_urls: 
            return None

        processed_urls.add(article_url)

        headers = {'User-Agent': 'MyFireNewsCrawler/1.0'}
        response = requests.get(article_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else ''
        content_paragraphs = soup.find_all('p')
        content = ' '.join([para.get_text(strip=True) for para in content_paragraphs])

        if not title or not content:
            logging.warning(f"Title or content not found for {article_url}")
            return None

        max_content_length = 2000
        truncated_content = content[:max_content_length]

        messages = [
            {"role": "system", "content": "You are an AI tasked with determining if a news article describes a specific fire incident. "
                    "The article must involve accidental or unintended fires affecting homes, houses, apartments, buildings, or people. "
                    "These may include fires caused by electrical faults, negligence, accidents, or natural causes (e.g., forest fires reaching homes). "},
            {"role": "user", "content": f"Title: {title}\n\nContent: {truncated_content}\n\nURL: {article_url}\n\nExtract the publication date, Published date (anything that provides the information about the date of the incident) from the content or URL, if possible. If the date is found in the URL, return it in the format 'dd-mm-yyyy'. If the date is found in the content, convert the date into the format 'dd-mm-yyyy'. If the date cannot be determined, respond with 'Date not available'. Also, determine if the article is related to a fire incident and answer with 'yes' or 'no'."}
        ]

        ai_response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=messages,
            max_tokens=155,
            temperature=0.1,
            n=1,
            stop=None,
        )

        ai_content = ai_response.choices[0].message.content.strip()
        date = "Date not available"
        is_related_to_fire = "no"

        if ai_content:
            lines = ai_content.split('\n')
            for line in lines:
                if "Publication date" in line:
                    date_match = re.search(r'(\d{2}-\d{2}-\d{4})', line)  
                    if date_match:
                        date = date_match.group(1)
                elif "Related to fire incident" in line:
                    if 'yes' in line.lower():
                        is_related_to_fire = 'yes'
                    elif 'no' in line.lower():
                        is_related_to_fire = 'no'

        if is_related_to_fire != 'yes':
            logging.info(f"Article at {article_url} is not related to fire incident, skipping save.")
            return None

        if date == "Date not available":
            date_match = re.search(r'(\d{4}/\d{2}/\d{2})', article_url)  
            if date_match:
                date = datetime.strptime(date_match.group(1), '%Y/%m/%d').strftime('%d-%m-%Y')
            logging.warning(f"Date not available for article: {article_url}, using URL date: {date}")

        # Check if the date is today's or yesterday's date
        today, yesterday = get_today_and_yesterday_dates()
        if date != today and date != yesterday:
            logging.info(f"Article at {article_url} has an outdated date ({date}), skipping save.")
            return None

        if any(keyword in truncated_content.lower() for keyword in fire_keywords):
            summary = truncated_content[:500]
            return {"title": title, "summary": summary, "url": article_url, "date": date, "is_it_related_to_fire_incident": "yes"}

        return None
    except Exception as e:
        logging.error(f"Error processing {article_url}: {e}")
        return None

def save_result(entry):
    with output_lock:
        try:
            if not os.path.exists(output_file):
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)

            with open(output_file, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                if not any(d['url'] == entry['url'] for d in data):
                    data.append(entry)
                    f.seek(0)
                    json.dump(data, f, indent=4, ensure_ascii=False)
                    f.truncate()
                    logging.info(f"Result saved: {entry['url']}")
                else:
                    logging.info(f"Duplicate entry found for {entry['url']}, skipping save.")
        except Exception as e:
            logging.error(f"Error saving result: {e}")

def main():
    # Load URLs from cleaned_websites.json
    urls = load_cleaned_websites()

    # Process each URL
    for website in urls:
        logging.info(f"Processing URL: {website}")
        result = process_article(website)
        if result:
            save_result(result)
        time.sleep(2)

if __name__ == "__main__":
    main()
