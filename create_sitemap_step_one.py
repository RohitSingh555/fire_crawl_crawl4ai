import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import datetime

INPUT_FILE = "websites.txt"
CRAWLED_URLS = set()
SKIPPED_URLS = set()
CRAWLED_FILE = "crawled_websites.txt"
SITEMAP_FILE = "sitemap.xml"

FIRE_KEYWORDS = ["fire", "burn", "wildfire", "firefighter", "blaze", "inferno", "firefighting", "firestorm", "flames", "arson", "smoke"]
MAX_CRAWL_LIMIT = 1000  # Limit of 1000 URLs per website

crawl_counter = 0
current_url_index = 0  # Index to track which URL to crawl
website_url_counter = {}  # Track URL crawl count per website

def log(message):
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def normalize_url(url):
    parsed = urlparse(url)
    return parsed._replace(fragment="", query="").geturl()

def get_links(url):
    global crawl_counter
    try:
        log(f"Fetching links from {url}")
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            log(f"Failed to fetch {url} (Status code: {response.status_code})")
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
        if is_long_url(parsed.path) and not contains_fire_keyword(parsed.path):  
            return False  
        return True
    return False

def is_long_url(path):
    return len(path.split('/')) > 4

def contains_fire_keyword(path):
    return any(keyword in path.lower() for keyword in FIRE_KEYWORDS)

def crawl(url):
    global crawl_counter, current_url_index
    website = urlparse(url).netloc  # Extract domain to track crawl count
    
    # Check if 1000 URLs have already been crawled for the current website
    if website_url_counter.get(website, 0) >= MAX_CRAWL_LIMIT:
        log(f"Reached {MAX_CRAWL_LIMIT} URLs for {website}. Switching to next URL.")
        current_url_index += 1  
        if current_url_index < len(initial_urls): 
            log(f"Switching to next URL: {initial_urls[current_url_index]}")
            crawl(initial_urls[current_url_index])  # Start crawling the next URL
        return
    
    normalized_url = normalize_url(url)
    if normalized_url in CRAWLED_URLS:
        log(f"Already crawled {normalized_url}")
        return
    if normalized_url in SKIPPED_URLS:
        log(f"Skipping previously failed URL {normalized_url}")
        return
    try:
        if is_recent_url(url):
            log(f"Crawling {normalized_url}")
            CRAWLED_URLS.add(normalized_url)
            save_crawled_url(normalized_url)
            crawl_counter += 1
            website_url_counter[website] = website_url_counter.get(website, 0) + 1  # Increment URL counter for the website
            generate_sitemap()
        else:
            log(f"Skipping {normalized_url} (Not recently modified)")
        links = get_links(url)
        for link in links:
            crawl(link)
    except Exception as e:
        log(f"Error during crawling {url}: {e}")
        SKIPPED_URLS.add(normalized_url)

def save_crawled_url(url):
    try:
        with open(CRAWLED_FILE, "a", encoding="utf-8") as file:
            file.write(url + "\n")
        log(f"Saved {url} to {CRAWLED_FILE}")
    except Exception as e:
        log(f"Error saving URL {url}: {e}")

def is_recent_url(url):
    try:
        log(f"Checking if {url} is recently modified")
        response = requests.head(url, timeout=10, allow_redirects=True)
        if response.status_code != 200:
            log(f"Failed to check {url} (Status code: {response.status_code})")
            return False
        last_modified = response.headers.get("Last-Modified")
        if last_modified:
            last_mod_date = datetime.datetime.strptime(last_modified, "%a, %d %b %Y %H:%M:%S %Z").date()
            today = datetime.date.today()
            yesterday = today - datetime.timedelta(days=1)
            return last_mod_date in [today, yesterday]
        log(f"No Last-Modified header for {url}")
        return True
    except Exception as e:
        log(f"Error checking if {url} is recently modified: {e}")
        SKIPPED_URLS.add(normalize_url(url))
        return False

def generate_sitemap():
    try:
        log("Generating sitemap")
        now = datetime.datetime.now().isoformat()
        sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
        sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        sitemap += 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        sitemap += 'xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9 '
        sitemap += 'http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">\n'
        sitemap += f"<!-- Created on {now} -->\n"
        
        unique_urls = set()

        for url in CRAWLED_URLS:
            if url not in unique_urls:
                sitemap += "  <url>\n"
                sitemap += f"    <loc>{url}</loc>\n"
                sitemap += f"    <lastmod>{now}</lastmod>\n"
                sitemap += f"    <priority>{'1.00' if any(url.startswith(base_url) for base_url in initial_urls) else '0.80'}</priority>\n"
                sitemap += "  </url>\n"
                
                unique_urls.add(url)

        sitemap += "</urlset>"
        
        with open(SITEMAP_FILE, "w", encoding="utf-8") as file:
            file.write(sitemap)
        log("Sitemap generated successfully")
    
    except Exception as e:
        log(f"Error generating sitemap: {e}")

def fetch_sitemap(url):
    """Try to fetch the sitemap.xml for the given URL."""
    try:
        sitemap_url = urljoin(url, "sitemap.xml")
        log(f"Trying to fetch sitemap from {sitemap_url}")
        response = requests.get(sitemap_url)
        if response.status_code == 200:
            log(f"Sitemap found at {sitemap_url}. Stopping crawl.")
            return True
        else:
            log(f"No sitemap found at {sitemap_url}. Continuing crawl.")
            return False
    except Exception as e:
        log(f"Error fetching sitemap from {url}: {e}")
        return False

if __name__ == "__main__":
    try:
        log(f"Reading URLs from {INPUT_FILE}")
        with open(INPUT_FILE, "r", encoding="utf-8") as file:
            initial_urls = [normalize_url(line.strip()) for line in file.readlines()]

        if fetch_sitemap(initial_urls[current_url_index]):
            log("Sitemap found, stopping execution.")
            exit()  
        for url in initial_urls:
            crawl(url)
    
    except FileNotFoundError:
        log(f"Error: {INPUT_FILE} not found.")
