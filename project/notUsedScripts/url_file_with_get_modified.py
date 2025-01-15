import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import datetime
import json
import re
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# File Names
INPUT_FILE = "websites.txt"
CRAWLED_FILE = "crawled_websites.txt"
JSON_FILE = "crawled_websites.json"
OUTPUT_FILE = "updated_crawled_websites.json"

# Constants
FIRE_KEYWORDS = ["fire", "burn", "wildfire", "firefighter", "blaze", "inferno", "firefighting", "firestorm", "flames", "arson", "smoke"]
MAX_PAGES_PER_WEBSITE = 1000

# Data Structures
CRAWLED_URLS = set()
CRAWLED_URLS_LOCK = threading.Lock()
SKIPPED_URLS = set()
website_url_counter = {}
crawled_data = []

def log(message):
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def normalize_url(url):
    parsed = urlparse(url)
    return parsed._replace(fragment="", query="").geturl()

def get_links(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for link in soup.find_all("a", href=True):
            abs_url = normalize_url(urljoin(url, link["href"]))
            if is_valid_link(abs_url, url):
                links.append(abs_url)
        return links
    except Exception as e:
        log(f"Error fetching links from {url}: {e}")
        SKIPPED_URLS.add(normalize_url(url))
        return []

def is_valid_link(url, base_url):
    parsed = urlparse(url)
    base_parsed = urlparse(base_url)
    news_keywords = ["news", "article", "post", "story", "/news/", "/post/", "/article/"]
    if parsed.netloc != base_parsed.netloc or url in CRAWLED_URLS or url in SKIPPED_URLS:
        return False
    if parsed.path.endswith((".jpg", ".png", ".gif", ".css", ".js")):
        return False
    if parsed.path == "/" or any(keyword in parsed.path.lower() for keyword in news_keywords):
        return True
    return False

def crawl(url):
    website = urlparse(url).netloc
    with CRAWLED_URLS_LOCK:
        if website_url_counter.get(website, 0) >= MAX_PAGES_PER_WEBSITE:
            return
        normalized_url = normalize_url(url)
        if normalized_url in CRAWLED_URLS or normalized_url in SKIPPED_URLS:
            return
        CRAWLED_URLS.add(normalized_url)
        website_url_counter[website] = website_url_counter.get(website, 0) + 1

    try:
        response = requests.get(url, timeout=10)
        last_modified = response.headers.get("Last-Modified")
        if last_modified:
            last_modified_date = datetime.datetime.strptime(last_modified, "%a, %d %b %Y %H:%M:%S %Z").isoformat()
        else:
            last_modified_date = None

        save_crawled_url(normalized_url, website, last_modified_date)
        links = get_links(url)
        return links  # Return links for further crawling
    except Exception as e:
        log(f"Error crawling {url}: {e}")
        SKIPPED_URLS.add(normalize_url(url))
        return []

def save_crawled_url(url, website, last_modified_date):
    global crawled_data
    try:
        with open(CRAWLED_FILE, "a", encoding="utf-8") as file:
            file.write(url + "\n")
        crawled_data.append({
            "url": url,
            "website": website,
            "last_modified": last_modified_date
        })
        log(f"Saved URL: {url} with Last-Modified: {last_modified_date}")
        save_to_json()
    except Exception as e:
        log(f"Failed to save URL: {url}. Error: {e}")

def save_to_json():
    try:
        with open(JSON_FILE, "w", encoding="utf-8") as file:
            json.dump(crawled_data, file, indent=4)
    except Exception as e:
        log(f"Error saving to JSON file: {e}")

def threaded_crawl(initial_urls):
    with ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(crawl, url): url for url in initial_urls}
        while future_to_url:
            for future in as_completed(future_to_url):
                try:
                    links = future.result()
                    if links:
                        for link in links:
                            if link not in CRAWLED_URLS and link not in SKIPPED_URLS:
                                future_to_url[executor.submit(crawl, link)] = link
                except Exception as e:
                    log(f"Error in threaded crawl: {e}")
                finally:
                    del future_to_url[future]

def fetch_last_modified_header(url):
    try:
        response = requests.head(url, timeout=10)
        return response.headers.get("Last-Modified", None)
    except Exception as e:
        log(f"Error fetching Last-Modified header for {url}: {e}")
        return None

def extract_date_from_url(url):
    date_patterns = [
        r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b',  
        r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b', 
    ]
    for pattern in date_patterns:
        match = re.search(pattern, url)
        if match:
            try:
                return datetime.strptime(match.group(), "%Y-%m-%d").isoformat()
            except ValueError:
                pass
            try:
                return datetime.strptime(match.group(), "%d-%m-%Y").isoformat()
            except ValueError:
                pass
    return None

def extract_date_from_content(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.text, "html.parser")

        time_tag = soup.find("time")
        if time_tag and time_tag.has_attr("datetime"):
            return time_tag["datetime"]

        meta_tags = [
            {"name": "last-modified"},
            {"property": "article:published_time"},
            {"property": "og:updated_time"},
        ]
        for meta_tag in meta_tags:
            meta = soup.find("meta", meta_tag)
            if meta and meta.has_attr("content"):
                return meta["content"]

        date_patterns = [
            r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b',
            r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b', 
        ]
        for pattern in date_patterns:
            match = re.search(pattern, response.text)
            if match:
                try:
                    return datetime.strptime(match.group(), "%Y-%m-%d").isoformat()
                except ValueError:
                    pass
                try:
                    return datetime.strptime(match.group(), "%d-%m-%Y").isoformat()
                except ValueError:
                    pass

        return None
    except Exception as e:
        log(f"Error extracting date from content for {url}: {e}")
        return None

def get_best_date(url):
    last_modified = fetch_last_modified_header(url)
    if last_modified:
        return last_modified

    date_from_url = extract_date_from_url(url)
    if date_from_url:
        return date_from_url

    date_from_content = extract_date_from_content(url)
    if date_from_content:
        return date_from_content

    return "Not Available"

def process_url(entry):
    try:
        url = entry["url"]
        if entry["last_modified"] is None:
            log(f"Fetching date for: {url}")
            best_date = get_best_date(url)
            entry["last_modified"] = best_date
    except Exception as e:
        log(f"Error processing URL {entry['url']}: {e}")
    return entry

def update_last_modified(json_file, output_file):
    try:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        updated_data = []
        max_threads = os.cpu_count() * 2 
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = {executor.submit(process_url, entry): entry for entry in data}
            for future in as_completed(futures):
                try:
                    updated_entry = future.result()
                    updated_data.append(updated_entry)
                except Exception as e:
                    log(f"Error in thread execution: {e}")

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(updated_data, file, indent=4)
        log(f"Updated JSON saved to: {output_file}")
    except Exception as e:
        log(f"Error processing JSON file: {e}")

if __name__ == "__main__":
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as file:
            initial_urls = [normalize_url(line.strip()) for line in file.readlines()]
        threaded_crawl(initial_urls)

        update_last_modified(JSON_FILE, OUTPUT_FILE)
    except FileNotFoundError as e:
        log(f"File not found: {e}")
    except Exception as e:
        log(f"Unexpected error: {e}")
