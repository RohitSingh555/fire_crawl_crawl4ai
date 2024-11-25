import json
import requests
from bs4 import BeautifulSoup
import time
import logging
import os
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

fire_keywords = [
    'fire', 'blaze', 'burn', 'wildfire', 'inferno', 'smoke', 'flames', 'arson',
    'brushfire', 'house-fire', 'forest-fire', 'building-fire', 'firefighters'
]

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
        headers = {
            'User-Agent': 'MyFireNewsCrawler/1.0'
        }
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

def is_fire_related_ai(article_url):
    try:
        headers = {
            'User-Agent': 'MyFireNewsCrawler/1.0'
        }
        response = requests.get(article_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else ''
        content_paragraphs = soup.find_all('p')
        content = ' '.join([para.get_text(strip=True) for para in content_paragraphs])

        if not title or not content:
            logging.warning(f"Title or content not found for {article_url}")
            return False

        max_content_length = 2000
        truncated_content = content[:max_content_length]

        messages = [
            {"role": "system", "content": "You are an AI that determines if news articles are about fire incidents."},
            {"role": "user", "content": f"Title: {title}\n\nContent: {truncated_content}\n\nRespond with 'Yes' or 'No'."}
        ]

        ai_response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=messages,
            max_tokens=5,
            temperature=0,
            n=1,
            stop=None,
        )

        answer = ai_response.choices[0].message.content.strip()
        logging.info(f"AI response for {article_url}: {answer}")
        return answer.lower() == 'yes'
    except Exception as e:
        logging.error(f"Error processing {article_url}: {e}")
        return False

def load_cleaned_websites():
    try:
        with open('cleaned_websites.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [entry['url'] for entry in data if 'url' in entry]
    except Exception as e:
        logging.error(f"Error loading cleaned websites: {e}")
        return []

def main():
    all_fire_article_links = []
    urls = load_cleaned_websites()

    for website in urls:
        article_urls = crawl_website(website)
        logging.info(f"Found {len(article_urls)} potential fire-related article links on {website}")
        time.sleep(2)

        for article_url in article_urls:
            if not is_allowed(article_url):
                logging.warning(f"Crawling disallowed by robots.txt for {article_url}")
                continue

            is_fire_related = is_fire_related_ai(article_url)
            if is_fire_related:
                logging.info(f"Confirmed fire-related article: {article_url}")
                all_fire_article_links.append(article_url)
            else:
                logging.debug(f"Article not fire-related: {article_url}")

            time.sleep(1)

    with open('confirmed_fire_article_links.txt', 'w') as f:
        for link in all_fire_article_links:
            f.write(link + '\n')

    logging.info(f"Total confirmed fire-related articles found: {len(all_fire_article_links)}")

if __name__ == "__main__":
    main()
