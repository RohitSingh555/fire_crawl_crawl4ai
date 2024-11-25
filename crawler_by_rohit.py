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
    except:
        return False

def crawl_website(url):
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
    except:
        return []

def extract_article_details(article_url):
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
            return None, None, None
        max_content_length = 2000
        truncated_content = content[:max_content_length]
        messages = [
            {"role": "system", "content": "You are an AI that summarizes news articles."},
            {"role": "user", "content": f"Title: {title}\n\nContent: {truncated_content}\n\nSummarize this article in a few sentences."}
        ]
        ai_response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=messages,
            max_tokens=150,
            temperature=0.7,
            n=1,
            stop=None,
        )
        summary = ai_response.choices[0].message.content.strip()
        return title, summary, article_url
    except:
        return None, None, None

def load_cleaned_websites():
    try:
        with open('cleaned_websites.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [entry['url'] for entry in data if 'url' in entry]
    except:
        return []

def save_to_file(article):
    try:
        if not os.path.exists('confirmed_fire_articles_live.json'):
            with open('confirmed_fire_articles_live.json', 'w', encoding='utf-8') as f:
                json.dump([article], f, ensure_ascii=False, indent=4)
        else:
            with open('confirmed_fire_articles_live.json', 'r+', encoding='utf-8') as f:
                data = json.load(f)
                data.append(article)
                f.seek(0)
                json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass

def main():
    urls = load_cleaned_websites()
    for website in urls:
        article_urls = crawl_website(website)
        time.sleep(2)
        for article_url in article_urls:
            if not is_allowed(article_url):
                continue
            title, summary, url = extract_article_details(article_url)
            if title and summary:
                article = {"website": website, "title": title, "summary": summary, "url": url}
                save_to_file(article)
            time.sleep(1)

if __name__ == "__main__":
    main()
