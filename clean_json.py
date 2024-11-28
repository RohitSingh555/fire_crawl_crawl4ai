import json
from datetime import datetime, timedelta

INPUT_FILE = "updated_crawled_websites.json"
OUTPUT_FILE = "cleaned_websites.json"
FIRE_KEYWORDS = [
    "fire", "blaze", "wildfire", "arson", "inferno", "conflagration", "flames", "smoke",
    "burning", "ignition", "explosion", "firefighting", "extinguish", "embers", "scorched",
    "flammable", "hazard", "combustion", "sparks", "rescue", "evacuation", "firebreak",
    "controlled burn", "firestorm", "smoldering", "charred", "arsonist",
    "firetruck", "firefighter", "fire brigade", "fire department", "fire hazard",
    "incendiary", "fire alarm", "fire response", "fire suppression", "brushfire",
    "structure fire", "house fire", "apartment fire", "forest fire", "grassfire",
    "electrical fire", "chemical fire"
]
EXCLUDE_KEYWORDS = ["ceasefire"]

def contains_fire_keywords(url):
    return any(keyword in url.lower() for keyword in FIRE_KEYWORDS)

def contains_exclude_keywords(url):
    return any(keyword in url.lower() for keyword in EXCLUDE_KEYWORDS)

def is_within_last_week(timestamp_str):
    if not isinstance(timestamp_str, str) or timestamp_str in ["Not Available", ""]:
        return False
    try:
        if len(timestamp_str) == 10:  
            timestamp_date = datetime.strptime(timestamp_str, "%Y-%m-%d").date()
        elif timestamp_str.endswith("Z"):
            timestamp_date = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ").date()
        else:
            timestamp_date = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S").date()

        today = datetime.now().date()
        last_week = today - timedelta(days=7)
        
        return last_week <= timestamp_date <= today
    except ValueError:
        return False

def normalize_url(url):
    if url.endswith('/'):
        return url[:-1]
    return url

def clean_json(input_file, output_file):
    try:
        with open(input_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        cleaned_data = []
        seen_urls = set()

        for entry in data:
            url = entry.get("url", "")
            normalized_url = normalize_url(url)
            
            if not contains_exclude_keywords(url) and \
               (len(url) <= 50 or contains_fire_keywords(url)) and \
               is_within_last_week(entry.get("last_modified", "")):
                if normalized_url not in seen_urls:
                    cleaned_data.append(entry)
                    seen_urls.add(normalized_url)

        # Save the first version of cleaned data
        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(cleaned_data, file, indent=4)

        print(f"Cleaned JSON saved to {output_file}. Total entries: {len(cleaned_data)}")

        # Remove duplicates if any and save again
        with open(output_file, "r", encoding="utf-8") as file:
            cleaned_data = json.load(file)

        seen_urls = set()
        unique_data = []
        for entry in cleaned_data:
            url = entry.get("url", "")
            normalized_url = normalize_url(url)
            if normalized_url not in seen_urls:
                unique_data.append(entry)
                seen_urls.add(normalized_url)

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(unique_data, file, indent=4)

        print(f"Final cleaned JSON saved to {output_file}. Total entries: {len(unique_data)}")
        
    except Exception as e:
        print(f"Error processing the JSON file: {e}")

if __name__ == "__main__":
    clean_json(INPUT_FILE, OUTPUT_FILE)
