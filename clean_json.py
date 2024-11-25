import json
from datetime import datetime, timedelta

INPUT_FILE = "crawled_websites.json"
OUTPUT_FILE = "cleaned_websites.json"
FIRE_KEYWORDS = ["fire", "burn", "wildfire", "firefighter", "blaze", "inferno", "firefighting", "firestorm", "flames", "arson", "smoke"]

def contains_fire_keywords(url):
    """Checks if the URL contains any fire-related keywords."""
    return any(keyword in url.lower() for keyword in FIRE_KEYWORDS)

# def is_yesterday_or_earlier(timestamp_str):
#     """
#     Checks if a given timestamp is from yesterday or earlier.
#     Compares only the date (ignoring time).
#     """
#     if not isinstance(timestamp_str, str):
#         return False
#     try:
#         timestamp_date = datetime.fromisoformat(timestamp_str).date()  # Extract only the date
#         yesterday_date = (datetime.now() - timedelta(days=1)).date()   # Extract yesterday's date
#         return timestamp_date <= yesterday_date
#     except ValueError:
#         # Return False if the timestamp is not in a valid ISO format
#         return False

def clean_json(input_file, output_file):
    """
    Cleans the JSON file based on URL length, fire-related keywords, 
    and last-modified date (yesterday or earlier).
    """
    try:
        with open(input_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        cleaned_data = [
            entry for entry in data
            if (len(entry["url"]) <= 50 or contains_fire_keywords(entry["url"])) 
        ]

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(cleaned_data, file, indent=4)

        print(f"Cleaned JSON saved to {output_file}. Total entries: {len(cleaned_data)}")
    except Exception as e:
        print(f"Error processing the JSON file: {e}")

if __name__ == "__main__":
    clean_json(INPUT_FILE, OUTPUT_FILE)
