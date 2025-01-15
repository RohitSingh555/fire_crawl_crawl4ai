import json
import os
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

INPUT_FILE = "crawled_websites.json"
OUTPUT_FILE = "updated_crawled_websites.json"

def fetch_last_modified_header(url):
    try:
        response = requests.head(url, timeout=10)
        return response.headers.get("Last-Modified", None)
    except Exception as e:
        print(f"Error fetching Last-Modified header for {url}: {e}")
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
        print(f"Error extracting date from content for {url}: {e}")
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
            print(f"Fetching date for: {url}")
            best_date = get_best_date(url)
            entry["last_modified"] = best_date
    except Exception as e:
        print(f"Error processing URL {entry['url']}: {e}")
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
                    print(f"Error in thread execution: {e}")

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(updated_data, file, indent=4)
        print(f"Updated JSON saved to: {output_file}")
    except Exception as e:
        print(f"Error processing JSON file: {e}")

if __name__ == "__main__":
    update_last_modified(INPUT_FILE, OUTPUT_FILE)
