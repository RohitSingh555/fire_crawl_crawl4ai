import json
import requests
from bs4 import BeautifulSoup
import logging
import os
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
from datetime import datetime, timedelta

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

def crawl_website(url, processed_urls):
    article_links = []
    try:
        headers = {'User-Agent': 'MyFireNewsCrawler/1.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = href if href.startswith('http') else urljoin(url, href)
            parsed_full_url = urlparse(full_url)
            normalized_url = parsed_full_url.scheme + '://' + parsed_full_url.netloc + parsed_full_url.path
            if normalized_url not in processed_urls and any(keyword in normalized_url.lower() for keyword in fire_keywords):
                article_links.append(normalized_url)
                processed_urls[normalized_url] = True 
    except Exception as e:
        logging.error(f"Error crawling {url}: {str(e)}")
    return article_links

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
        yesterday_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI tasked with determining if a news article describes a specific fire incident. "
                    "The article must involve accidental or unintended fires affecting homes, houses, apartments, buildings, or people. "
                    "These may include fires caused by electrical faults, negligence, accidents, or natural causes (e.g., forest fires reaching homes). "
                    "Explicitly exclude articles about wars, ceasefires, political events, fundraising campaigns, ceremonial events, or unrelated activities. "
                    f"Additionally, only consider articles that were posted or modified {yesterday_date}. Articles older than {yesterday_date} should be excluded."
                    "Respond only if the content directly involves a fire-related accident as described above. "
                    "Your response must strictly have 'Yes' or 'No' followed by the summary."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Title: {title}\n\nContent: {truncated_content}\n\n"
                    "Does this article describe an accidental fire incident affecting homes, buildings, or people as defined above, "
                    "Respond only with 'Yes' or 'No'."
                )
            }
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
    except Exception as e:
        logging.error(f"Error extracting details for {article_url}: {str(e)}")
        return None, None, None

def load_cleaned_websites():
    try:
        with open('cleaned_websites.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [entry['url'] for entry in data if 'url' in entry]
    except Exception as e:
        logging.error(f"Error loading websites: {str(e)}")
        return []

def save_articles_to_file(articles):
    try:
        if not os.path.exists('final_result'):
            os.makedirs('final_result')

        current_date = datetime.now().strftime("%Y-%m-%d")
        file_path = os.path.join('final_result', f'confirmed_fire_articles_{current_date}.json')

        if articles:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(articles, f, ensure_ascii=False, indent=4)
                logging.info(f"Saved {len(articles)} articles to {file_path}")
        else:
            logging.info("No articles to save.")
    except Exception as e:
        logging.error(f"Error saving to file: {str(e)}")

def process_article_url(article_url, articles):
    title, summary, url = extract_article_details(article_url)
    if summary.startswith("Yes") and title and url:
        short_summary = summary[4:].strip()  
        article = {"title": title, "summary": short_summary, "url": url}
        articles.append(article)
    else:
        logging.info(f"Irrelevant article skipped: {title or 'No Title'} - {url}")


def process_website(website_url, articles, processed_urls):
    article_urls = crawl_website(website_url, processed_urls)
    for article_url in article_urls:
        process_article_url(article_url, articles)

def main():
    manager = multiprocessing.Manager()
    articles = manager.list()
    processed_urls = manager.dict()
    urls = load_cleaned_websites()

    with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count() * 2) as executor:
        futures = [executor.submit(process_website, website, articles, processed_urls) for website in urls]

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logging.error(f"Error processing website: {str(e)}")

    save_articles_to_file(list(articles))

if __name__ == "__main__":
    start_time = datetime.now()
    main()
    logging.info(f"Processing completed in {datetime.now() - start_time}")
