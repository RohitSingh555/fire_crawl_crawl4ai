import os
import json
import re
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from playwright.sync_api import sync_playwright
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

PROXIES = ["http://proxy1:port", "http://proxy2:port", "http://proxy3:port"]
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

def get_browser_context(p):
    """Tries to use a proxy, falls back to direct connection if proxy fails."""
    proxy = random.choice(PROXIES)
    try:
        return p.chromium.launch(headless=True).new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 800},
            java_script_enabled=True,
            proxy={"server": proxy}
        )
    except:
        print(f"Proxy {proxy} failed, using direct connection.")
        return p.chromium.launch(headless=True).new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 800},
            java_script_enabled=True
        )

def extract_article_data(url):
    """Scrapes the title, content, and date from an article URL."""
    with sync_playwright() as p:
        context = get_browser_context(p)
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(random.uniform(2, 5))
            title = page.title() or "No Title Found"
            paragraphs = page.query_selector_all("p")
            content = " ".join([p.inner_text().strip() for p in paragraphs if p.inner_text().strip()])
            date = extract_date(page, url)
            return title, content, date
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None, None, None
        finally:
            context.close()

def extract_date(page, url):
    """Extracts the publication date from the page or URL."""
    meta_selectors = [
        "meta[property='article:published_time']",
        "meta[name='date']",
        "meta[name='publish-date']",
        "time[datetime]"
    ]
    for selector in meta_selectors:
        element = page.query_selector(selector)
        if element:
            date = element.get_attribute("content")
            if date and re.search(r'\d{4}-\d{2}-\d{2}', date):
                return date[:10]
    
    content = page.inner_text("body")
    date_matches = re.findall(r'\b\d{4}-\d{2}-\d{2}\b', content) or re.findall(r'\b\d{2}/\d{2}/\d{4}\b', content)
    if date_matches:
        return date_matches[0]
    
    url_date_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', url) or re.search(r'\b\d{2}/\d{2}/\d{4}\b', url)
    return url_date_match.group(0) if url_date_match else "Date not available"

def verify_fire_incident(title, content, date, url):
    """Uses OpenAI to verify if an article is about a fire incident."""
    truncated_content = content[:2000]
    prompt = (
        "A fire incident refers strictly to an unintended or accidental fire that results in damage to physical structures within the United States. "
        "Evaluate the following article and determine if it describes a fire-related structural damage. Only respond 'yes' if there is explicit mention of such damage, otherwise respond 'no'. "
        f"Title: {title}\nContent: {truncated_content}\nURL: {url}\nDate: {date}\n"
    )
    
    messages = [{"role": "user", "content": prompt}]
    
    try:
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=messages,
            temperature=0,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        return "no"

def process_url(url):
    """Processes a single URL and extracts fire-related article data."""
    if len(url) <= 30:
        print(f"Skipping short URL: {url}")
        return None
    
    try:
        title, content, date = extract_article_data(url)
        if not title or not content:
            return None
        
        result = verify_fire_incident(title, content, date, url)
        
        if 'yes' in result.lower():
            return {
                'Title': title,
                'Description': content[:500],
                'Date': date,
                'URL': url
            }
    except Exception as e:
        print(f"Error processing {url}: {e}")
    return None

def process_urls_from_json(input_json_file, output_json_file):
    """Reads URLs from a JSON file, processes them, and saves results."""
    with open(input_json_file, 'r') as json_file:
        urls_data = json.load(json_file)
    
    results = []
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(process_url, url) for urls in urls_data.values() for url in urls]
        
        for future in as_completed(futures):
            try:
                article_data = future.result(timeout=40)  # Increased timeout for reliability
                if article_data:
                    results.append(article_data)
            except FuturesTimeoutError:
                print("A URL processing timed out.")
    
    with open(output_json_file, 'w') as json_file:
        json.dump(results, json_file, indent=4)
    
    print(f"Processing complete. Results saved to {output_json_file}")

if __name__ == "__main__":
    os.makedirs("all_jsons", exist_ok=True)  

    input_json_file = os.path.join("all_jsons", "fire_scraped_urls.json")
    output_json_file = os.path.join("all_jsons", "fire_incident_results.json")
    
    process_urls_from_json(input_json_file, output_json_file)

