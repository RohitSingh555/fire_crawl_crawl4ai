import json
import requests
from bs4 import BeautifulSoup
import time
import logging
import os
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Lock

load_dotenv()

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

fire_keywords = [
    'fire', 'blaze', 'burn', 'wildfire', 'inferno', 'smoke', 'flames', 'arson',
    'brushfire', 'house-fire', 'forest-fire', 'building-fire', 'firefighters'
]

output_file = 'results_of_fire_incidents.json'
output_lock = Lock()

def load_cleaned_websites():
    try:
        with open('cleaned_websites.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [entry['url'] for entry in data if 'url' in entry]
    except Exception as e:
        logging.error(f"Error loading cleaned websites: {e}")
        return []

def is_allowed(url, user_agent='MyFireNewsCrawler/1.0'):
    import urllib.robotparser

    parsed_uri = urlparse(url)
    domain = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
    robots_url = urljoin(domain, '/robots.txt')

    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception as e:
        logging.warning(f"Could not read robots.txt for {domain}: {e}")
        return False

def crawl_website(url):
    logging.info(f"Crawling {url}")
    try:
        headers = {'User-Agent': 'MyFireNewsCrawler/1.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        article_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = href if href.startswith('http') else urljoin(url, href)
            parsed_full_url = urlparse(full_url)
            normalized_url = parsed_full_url.scheme + '://' + parsed_full_url.netloc + parsed_full_url.path

            if any(keyword in normalized_url.lower() for keyword in fire_keywords):
                if normalized_url not in article_links:
                    article_links.append(normalized_url)

        return article_links
    except Exception as e:
        logging.error(f"Error crawling {url}: {e}")
        return []

def process_article(article_url):
    try:
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
            {"role": "system", "content": "You are an AI that determines if news articles are about fire incidents."},
            {"role": "user", "content": f"Title: {title}\n\nContent: {truncated_content}\n\nRespond with 'Yes' or 'No'."}
        ]

        ai_response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=messages,
            max_tokens=155,
            temperature=0,
            n=1,
            stop=None,
        )

        answer = ai_response.choices[0].message.content.strip()

        if answer.lower() == 'yes':
            summary = truncated_content[:500]
            date = datetime.now().strftime('%Y-%m-%d')
            return {"title": title, "summary": summary, "url": article_url, "date": date}
        return None
    except Exception as e:
        logging.error(f"Error processing {article_url}: {e}")
        return None

def save_result_dynamically(entry):
    with output_lock:
        if not os.path.exists(output_file):
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
        try:
            with open(output_file, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                data.append(entry)
                f.seek(0)
                json.dump(data, f, indent=4, ensure_ascii=False)
                f.truncate()
            logging.info(f"Result dynamically saved: {entry['url']}")
        except Exception as e:
            logging.error(f"Error saving result dynamically: {e}")

def main():
    urls = load_cleaned_websites()

    with ThreadPoolExecutor(max_workers=5) as executor:
        for website in urls:
            article_urls = crawl_website(website)
            logging.info(f"Found {len(article_urls)} potential fire-related article links on {website}")
            time.sleep(2)

            future_to_url = {
                executor.submit(process_article, url): url for url in article_urls if is_allowed(url)
            }

            for future in future_to_url:
                result = future.result()
                if result:
                    save_result_dynamically(result)

if __name__ == "__main__":
    main()
