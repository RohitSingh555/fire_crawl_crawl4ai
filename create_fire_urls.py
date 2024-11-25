from bs4 import BeautifulSoup
import requests
import re
from urllib.parse import urljoin

KEYWORDS = [
    "fire", "blaze", "wildfire", "arson", "inferno", "conflagration", "flames", "smoke",
    "burning", "ignition", "explosion", "firefighting", "extinguish", "embers", "scorched",
    "flammable", "hazard", "combustion", "sparks", "rescue", "evacuation", "firebreak",
    "controlled burn", "firestorm", "smoldering", "charred", "arsonist", "backdraft",
    "firetruck", "firefighter", "fire brigade", "fire department", "fire hazard",
    "incendiary", "fire alarm", "fire response", "fire suppression", "brushfire",
    "structure fire", "house fire", "apartment fire", "forest fire", "grassfire",
    "electrical fire", "chemical fire", "incident"
]

visited_urls = set()

def clean_url(url):
    url = url.strip()
    if not re.match(r'^https?://', url): 
        url = 'http://' + url
    return url

def fetch_website_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_relevant_text(content):
    try:
        soup = BeautifulSoup(content, "html.parser")
        headlines = soup.find_all(["h1", "h2", "h3"], limit=10)
        paragraphs = soup.find_all("p", limit=50)
        text = "\n".join([h.get_text() for h in headlines]) + "\n" + \
               "\n".join([p.get_text() for p in paragraphs])
        return text.strip()
    except Exception as e:
        print(f"Error processing HTML content: {e}")
        return ""

def contains_fire_keywords(content):
    return any(keyword.lower() in content.lower() for keyword in KEYWORDS)

def extract_links(content, base_url):
    soup = BeautifulSoup(content, "html.parser")
    links = soup.find_all('a', href=True)
    return [urljoin(base_url, link['href']) for link in links]

def save_crawled_url(url, filename="crawled_websites.txt"):
    """Save the crawled URL to a text file."""
    try:
        with open(filename, "a") as file:
            file.write(url + "\n")
    except Exception as e:
        print(f"Error saving URL to file: {e}")

def crawl(url, max_depth=3, current_depth=0):
    """Crawl a website starting from the given URL."""
    if current_depth > max_depth or url in visited_urls:
        return

    visited_urls.add(url)
    print(f"Crawling: {url}")

    content = fetch_website_content(url)
    if not content:
        return

    relevant_content = extract_relevant_text(content)

    if contains_fire_keywords(relevant_content):
        save_crawled_url(url)

    links = extract_links(content, url)
    for link in links:
        crawl(link, max_depth, current_depth + 1)

if __name__ == "__main__":
    try:
        with open("websites.txt", "r") as file:
            seed_urls = [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        print("Error: The 'websites.txt' file was not found.")
        seed_urls = []

    if not seed_urls:
        print("No seed URLs found to crawl. Please provide valid URLs in 'websites.txt'.")
    else:
        for url in seed_urls:
            crawl(url, max_depth=2)
