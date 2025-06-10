import os
import json
import re
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
import time

load_dotenv()

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'TE': 'Trailers',
    'Cache-Control': 'max-age=0',
    'Pragma': 'no-cache',
    'DNT': '1',
    'X-Requested-With': 'XMLHttpRequest',
    'If-None-Match': 'W/"35-f6dpDOfTQUZECdaBBhKg+W5fEz0"'
}


# Function to fetch proxies from the ProxyScrape API
def fetch_proxies():
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
    try:
        print("Fetching proxies from ProxyScrape API...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        proxies = [proxy.strip() for proxy in response.text.splitlines() if proxy.strip()]
        print(f"Fetched {len(proxies)} proxies.")
        return proxies
    except requests.exceptions.RequestException as e:
        print(f"Error fetching proxies: {e}")
        return []


# Function to test a single proxy
def test_proxy(proxy):
    try:
        print(f"Testing proxy: {proxy}")
        response = requests.get(
            "https://httpbin.org/ip",
            proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
            timeout=5,
        )
        if response.status_code == 200:
            print(f"✅ Proxy {proxy} is valid.")
            return {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    except Exception as e:
        print(f"❌ Proxy {proxy} failed: {e}")
    return None


# Fetch and test proxies to create a list of up to 10 valid proxies
def initialize_proxies():
    print("Initializing proxies...")
    proxies = fetch_proxies()
    valid_proxies = []
    for proxy in proxies:
        if len(valid_proxies) >= 3:  # Stop once we have 10 valid proxies
            break
        valid_proxy = test_proxy(proxy)
        if valid_proxy:
            valid_proxies.append(valid_proxy)
    if valid_proxies:
        print(f"Valid proxies initialized: {valid_proxies}")
    else:
        print("No valid proxies found. Requests will be sent directly.")
    return valid_proxies

# Initialize list of valid proxies
valid_proxies = initialize_proxies()

def extract_article_data(url, proxy=None):
    try:
        # Set a timeout of 10 seconds for the request to avoid hanging
        response = requests.get(url, headers=headers, proxies=proxy, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "No Title Found"
        paragraphs = soup.find_all('p')
        content = ' '.join([para.get_text(strip=True) for para in paragraphs])
        date = None
        possible_date_tags = [
            ('time', 'datetime'),
            ('meta', 'content'),
            ('span', None),
            ('div', None),
        ]
        
        for tag, attr in possible_date_tags:
            elements = soup.find_all(tag)
            for element in elements:
                text = element.get_text(strip=True) if not attr else element.get(attr)
                if text:
                    date_patterns = [
                        r'\d{1,2}:\d{2} [APM]{2} [A-Za-z]{3} \d{1,2}, \d{4}',
                        r'[A-Za-z]{3} \d{1,2}, \d{4}',
                        r'[A-Za-z]{4,9} \d{1,2}, \d{4}',
                        r'\d{1,2} [A-Za-z]{3} \d{1,4}, \d{4}',
                        r'\d{4}-\d{2}-\d{2}',
                    ]
                    for pattern in date_patterns:
                        if re.search(pattern, text):
                            date = text
                            break
                if date:
                    break
            if date:
                break
        
        return title, content, date
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url} with proxy {proxy}: {e}")
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
    if len(url) <= 30:
        print(f"Skipping URL due to short length: {url}")
        return None
    try:
        retries = 2
        for attempt in range(retries):
            proxy = valid_proxies[attempt % len(valid_proxies)] if valid_proxies else None
            title, content, date = extract_article_data(url, proxy)
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
            print(f"Retrying URL with a different proxy: {url}")
        print(f"Skipping URL after {retries} retries: {url}")
    except Exception as e:
        print(f"Error processing {url}: {e}")
    return None

def process_urls_from_json(input_json_file, output_json_file):
    if not valid_proxies:
        print("No valid proxies available. Skipping URL processing.")
        return

    with open(input_json_file, 'r') as json_file:
        urls_data = json.load(json_file)

    # Clear the output file before saving results
    with open(output_json_file, 'w') as json_file:
        json_file.write('[]')  # Write an empty JSON array to clear the file

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for website, urls in urls_data.items():
            for url in urls:
                futures.append(executor.submit(process_url, url))

        for future in as_completed(futures):
            try:
                article_data = future.result(timeout=30)  # Set timeout for each future task
                if article_data:
                    # Save the result incrementally
                    with open(output_json_file, 'r+') as json_file:
                        existing_results = json.load(json_file)
                        existing_results.append(article_data)
                        json_file.seek(0)
                        json.dump(existing_results, json_file, indent=4)
            except FuturesTimeoutError:
                print(f"A URL processing timed out.")

    print(f"Processing complete. Results saved to {output_json_file}")

if __name__ == "__main__":
    os.makedirs("all_jsons", exist_ok=True) 

    input_json_file = os.path.join("all_jsons", "fire_scraped_urls.json")
    output_json_file = os.path.join("all_jsons", "fire_incident_results.json")
    
    process_urls_from_json(input_json_file, output_json_file)

