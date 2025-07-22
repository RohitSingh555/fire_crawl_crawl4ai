import os
import json
import re
import asyncio
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from playwright.async_api import async_playwright
import time
import random
from urllib.parse import urlparse
import subprocess
import sys

load_dotenv()

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# User agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

# Headers for requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0'
}

def get_domain(url):
    """Extract domain from URL"""
    try:
        return urlparse(url).netloc
    except:
        return "unknown"

def requests_scrape(url, timeout=15):
    """Method 1: Simple requests scraping"""
    try:
        headers = HEADERS.copy()
        headers['User-Agent'] = random.choice(USER_AGENTS)
        
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        
        if len(response.content) > 1000:  # Basic content check
            return response.text
    except Exception as e:
        print(f"    Requests failed: {e}")
    return None

async def playwright_scrape(url, timeout=30):
    """Method 2: Playwright scraping with stealth"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers=HEADERS
            )
            
            page = await context.new_page()
            
            # Set longer timeout and wait for content
            await page.goto(url, timeout=timeout*1000, wait_until='domcontentloaded')
            await asyncio.sleep(3)  # Wait for JS to load
            
            # Try to wait for content
            selectors = ['h1', 'h2', 'p', 'article', '.content', '.article', 'body']
            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    break
                except:
                    continue
            
            html = await page.content()
            await browser.close()
            
            if html and len(html) > 1000:
                return html
                
    except Exception as e:
        print(f"    Playwright failed: {e}")
    return None

def selenium_scrape(url, timeout=30):
    """Method 3: Selenium scraping as fallback"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'--user-agent={random.choice(USER_AGENTS)}')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(timeout)
        
        driver.get(url)
        
        # Wait for content to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except:
            pass
        
        html = driver.page_source
        driver.quit()
        
        if html and len(html) > 1000:
            return html
            
    except Exception as e:
        print(f"    Selenium failed: {e}")
    return None

def curl_scrape(url, timeout=30):
    """Method 4: Curl as last resort"""
    try:
        user_agent = random.choice(USER_AGENTS)
        cmd = [
            'curl', '-s', '-L', '--max-time', str(timeout),
            '-H', f'User-Agent: {user_agent}',
            '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            '-H', 'Accept-Language: en-US,en;q=0.5',
            '-H', 'Accept-Encoding: gzip, deflate',
            '-H', 'Connection: keep-alive',
            '--compressed',
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+5)
        
        if result.returncode == 0 and len(result.stdout) > 1000:
            return result.stdout
            
    except Exception as e:
        print(f"    Curl failed: {e}")
    return None

def universal_scrape(url):
    """
    Universal scraper that tries multiple methods to ensure any website can be scraped
    """
    print(f"🔍 Scraping: {url}")
    
    # Method 1: Requests (fastest)
    print("  Trying requests...")
    html = requests_scrape(url)
    if html:
        print("  ✅ Requests succeeded")
        return html
    
    # Method 2: Playwright (handles JS)
    print("  Trying Playwright...")
    try:
        html = asyncio.run(playwright_scrape(url))
        if html:
            print("  ✅ Playwright succeeded")
            return html
    except Exception as e:
        print(f"  ❌ Playwright error: {e}")
    
    # Method 3: Selenium (fallback)
    print("  Trying Selenium...")
    html = selenium_scrape(url)
    if html:
        print("  ✅ Selenium succeeded")
        return html
    
    # Method 4: Curl (last resort)
    print("  Trying curl...")
    html = curl_scrape(url)
    if html:
        print("  ✅ Curl succeeded")
        return html
    
    print("  ❌ All methods failed")
    return None

def extract_article_data_from_html(html, url):
    """Extract title, content, and date from HTML content"""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title - try multiple selectors
        title = None
        title_selectors = [
            'h1', 'h1.article-title', 'h1.headline', 'h1.story-title',
            'h2.video-info-module__text--title', '.article-title', '.headline',
            'title', '.title', '.post-title', '.entry-title'
        ]
        
        for selector in title_selectors:
            title_el = soup.select_one(selector)
            if title_el:
                title = title_el.get_text(strip=True)
                break
        
        if not title:
            title = "No Title Found"
        
        # Extract content - get all paragraphs and text content
        paragraphs = soup.find_all('p')
        content_parts = []
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 20:  # Only meaningful paragraphs
                content_parts.append(text)
        
        # If no paragraphs, try other content selectors
        if not content_parts:
            content_selectors = [
                '.content', '.article-content', '.post-content', '.entry-content',
                '.story-content', '.article-body', '.post-body', 'article'
            ]
            for selector in content_selectors:
                content_el = soup.select_one(selector)
                if content_el:
                    paragraphs = content_el.find_all('p')
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if text and len(text) > 20:
                            content_parts.append(text)
                    break
        
        content = ' '.join(content_parts)
        
        # Extract date - try multiple approaches
        date = None
        date_selectors = [
            'time[datetime]', 'time', '.date', '.timestamp', '.published-date',
            '.article-date', '.story-date', '.post-date', '.entry-date',
            '.video-info-module__text--subtitle__timestamp'
        ]
        
        for selector in date_selectors:
            date_el = soup.select_one(selector)
            if date_el:
                if date_el.has_attr('datetime'):
                    date = date_el['datetime']
                else:
                    date = date_el.get_text(strip=True)
                break
        
        # If no date found, try to extract from JSON-LD
        if not date:
            for script in soup.find_all("script", {"type": "application/ld+json"}):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        date = data.get("uploadDate") or data.get("datePublished") or data.get("dateCreated")
                        if date:
                            break
                except:
                    continue
        
        # If still no date, try regex patterns in content
        if not date:
            date_patterns = [
                r'\d{1,2}:\d{2} [APM]{2} [A-Za-z]{3} \d{1,2}, \d{4}',
                r'[A-Za-z]{3} \d{1,2}, \d{4}',
                r'[A-Za-z]{4,9} \d{1,2}, \d{4}',
                r'\d{1,2} [A-Za-z]{3} \d{1,4}, \d{4}',
                r'\d{4}-\d{2}-\d{2}',
            ]
            for pattern in date_patterns:
                match = re.search(pattern, content)
                if match:
                    date = match.group()
                    break
        
        return title, content, date
        
    except Exception as e:
        print(f"Error extracting data from HTML: {e}")
        return None, None, None

def extract_article_data(url):
    """Main function to extract article data using universal scraping"""
    try:
        # Use universal scraper to get HTML
        html = universal_scrape(url)
        if not html:
            return None, None, None
        
        # Extract data from the HTML
        title, content, date = extract_article_data_from_html(html, url)
        return title, content, date
        
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None, None, None

def verify_fire_incident(title, content, date, url, country="YourCountry"):
    print(url)
    truncated_content = content[:2000]
    
    # Modify the fire incident prompt to include the country filter
    fire_incident_prompt = (
        f"A fire incident refers strictly to an unintended or accidental fire that results in damage to physical structures, such as homes, apartments, offices, commercial buildings, factories, or any infrastructure, within the United States. "
        "The fire must have caused structural damage or destruction and can be due to causes such as electrical faults, negligence, accidents, natural disasters (e.g., wildfires), or arson.\n\n"
        "Please carefully evaluate the article content and respond according to the following criteria:\n\n"
        "1. Does the article explicitly mention fire-related damage to physical structures? Respond with 'yes' only if structural damage (e.g., destruction, partial damage, collapse, repairs needed) is clearly described. Otherwise, respond with 'no'.\n\n"
        "2. If the article is not available (e.g., 'Page Not Found' or similar error messages in the content or advertisements), respond with 'no'.\n\n"
        f"Title: {title}\nContent: {truncated_content}\nURL: {url}\nDate passed: {date}\n\n"
        "Ensure your response is clear and strictly follows the criteria outlined above."
    )

    no_date_prompt = (
        f"A fire incident refers strictly to an unintended or accidental fire that results in damage to physical structures, such as homes, apartments, offices, commercial buildings, factories, or any infrastructure, within the United States. "
        "The fire must have caused structural damage or destruction and can be due to causes such as electrical faults, negligence, accidents, natural disasters (e.g., wildfires), or arson.\n\n"
        "Please carefully evaluate the article content and respond according to the following criteria:\n\n"
        "1. Does the article explicitly mention fire-related damage to physical structures? Respond with 'yes' only if structural damage (e.g., destruction, partial damage, collapse, repairs needed) is clearly described. Otherwise, respond with 'no'.\n\n"
        "2. Since no date was provided, please follow these steps to extract the publication date from the article:\n"
        "   - First, check the URL for a date in the format 'dd-mm-yyyy'.\n"
        "   - If no date is found in the URL, search the article content for the most recent date. If found, return it in 'dd-mm-yyyy' format.\n"
        "   - If no date is available, respond with 'Date not available'.\n\n"
        "3. If the article is not available (e.g., 'Page Not Found' or similar error messages), respond with 'no'.\n\n"
        f"Title: {title}\nContent: {truncated_content}\nURL: {url}\nDate passed: {date}\n\n"
        "Ensure your response is clear and strictly follows the criteria outlined above."
    )

    if date and date != "Date not available":
        prompt = fire_incident_prompt
    else:
        prompt = no_date_prompt

    messages = [
        {
            "role": "system",
            "content": "You are an AI tasked with evaluating news articles to determine if they describe fire incidents causing structural damage. Only articles explicitly mentioning damage to physical structures within the United States should be considered relevant."
        },
        {"role": "user", "content": prompt}
    ]


    try:
        ai_response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=messages,
            temperature=0,
        )

        answer = ai_response.choices[0].message.content.strip()
        print(answer)
        return answer
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        return "no"

def process_url(url):
    """Process a single URL using universal scraping"""
    if len(url) <= 30:
        print(f"Skipping URL due to short length: {url}")
        return None
    
    try:
        retries = 2
        for attempt in range(retries):
            print(f"Processing {url} (attempt {attempt + 1})")
            title, content, date = extract_article_data(url)
            
            if title and content:
                result = verify_fire_incident(title, content, date, url)
                if 'yes' in result.lower():
                    if date:
                        pass
                    else:
                        date_match = re.search(r'\d{2}-\d{2}-\d{4}', result)
                        date = date_match.group(0) if date_match else 'Date not available'
                    
                    article_data = {
                        'Title': title,
                        'Description': content[:500], 
                        'Date': date,
                        'URL': url
                    }
                    return article_data
            
            if attempt < retries - 1:
                print(f"Retrying URL: {url}")
                time.sleep(1)  # Small delay between retries
        
        print(f"Skipping URL after {retries} retries: {url}")
    except Exception as e:
        print(f"Error processing {url}: {e}")
    return None

def process_urls_from_json(input_json_file, output_json_file):
    print("🚀 Starting universal scraping process...")

    with open(input_json_file, 'r') as json_file:
        urls_data = json.load(json_file)

    # Clear the output file before saving results
    with open(output_json_file, 'w') as json_file:
        json_file.write('[]')  # Write an empty JSON array to clear the file

    total_urls = sum(len(urls) for urls in urls_data.values())
    print(f"📊 Total URLs to process: {total_urls}")

    with ThreadPoolExecutor(max_workers=3) as executor:  # Conservative worker count
        futures = []
        for website, urls in urls_data.items():
            print(f"📰 Processing {len(urls)} URLs from {website}")
            for url in urls:
                futures.append(executor.submit(process_url, url))

        completed = 0
        successful = 0
        
        for future in as_completed(futures):
            try:
                article_data = future.result(timeout=120)  # 2 minute timeout per URL
                completed += 1
                print(f"✅ Completed {completed}/{total_urls} URLs")
                
                if article_data:
                    successful += 1
                    # Save the result incrementally
                    with open(output_json_file, 'r+') as json_file:
                        existing_results = json.load(json_file)
                        existing_results.append(article_data)
                        json_file.seek(0)
                        json.dump(existing_results, json_file, indent=4)
                        print(f"🔥 Found fire incident: {article_data['Title'][:50]}...")
                        
            except FuturesTimeoutError:
                print(f"⏰ A URL processing timed out.")
                completed += 1
            except Exception as e:
                print(f"❌ Error processing URL: {e}")
                completed += 1

    print(f"🎉 Processing complete! Found {successful} fire incidents out of {total_urls} URLs")
    print(f"📁 Results saved to {output_json_file}")

if __name__ == "__main__":
    os.makedirs("all_jsons", exist_ok=True) 

    input_json_file = os.path.join("all_jsons", "fire_scraped_urls.json")
    output_json_file = os.path.join("all_jsons", "fire_incident_results.json")
    
    process_urls_from_json(input_json_file, output_json_file)

