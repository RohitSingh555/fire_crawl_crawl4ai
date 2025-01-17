import os
import json
import re
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

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


def extract_article_data(url):
    try:
        response = requests.get(url, headers=headers)
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
        print(f"Error fetching {url}: {e}")
    return None, None, None

def verify_fire_incident(title, content, date, url):
    print(url)
    truncated_content = content[:2000]
    fire_incident_prompt = (
        "You are an AI tasked with determining whether a news article describes a fire incident. "
        "A fire incident involves an unintended or accidental fire affecting homes, apartments, buildings, or people. "
        "This includes fires caused by electrical faults, negligence, accidents, natural disasters (e.g., wildfires), or arson.\n\n"
        "Please carefully evaluate the content and answer the following:\n\n"
        "1. Is the article related to a fire incident? Respond with 'yes' if the article describes a fire incident, or 'no' if it does not.\n\n"
        "3. If the article is not available (e.g., 'Page Not Found' or similar error in the content or Advertisement), respond with 'no'.\n\n"
        f"Title: {title}\nContent: {truncated_content}\nURL: {url}\nDate passed: {date}\n\n"
        "Please ensure that your responses are clear, concise, and formatted as described."
    )

    no_date_prompt = (
        "You are an AI tasked with determining whether a news article describes a fire incident. "
        "A fire incident involves an unintended or accidental fire affecting homes, apartments, buildings, or people. "
        "This includes fires caused by electrical faults, negligence, accidents, natural disasters (e.g., wildfires), or arson.\n\n"
        "Please carefully evaluate the content and answer the following:\n\n"
        "1. Is the article related to a fire incident? Respond with 'yes' if the article describes a fire incident, or 'no' if it does not.\n\n"
        "2. Since no date was passed, please follow these steps to extract the publication date from the article:\n"
        "   - First, check the URL for a date in the format 'dd-mm-yyyy'.\n"
        "   - If no date is found in the URL, search the content for the most recent date. If a date is found, return it in 'dd-mm-yyyy' format.\n"
        "   - If no date can be found, respond with 'Date not available'.\n\n"
        "3. If the article is not available (e.g., 'Page Not Found' or similar error in the content), respond with 'no'.\n\n"
        f"Title: {title}\nContent: {truncated_content}\nURL: {url}\nDate passed: {date}\n\n"
        "Please ensure that your responses are clear, concise, and formatted as described."
    )

    if date and date != "Date not available":
        prompt = fire_incident_prompt 
    else:
        prompt = no_date_prompt  

    messages = [
        {"role": "system", "content": "You are an AI that determines if news articles are about fire incidents."},
        {"role": "user", "content": prompt}
    ]

    ai_response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=messages,
        temperature=0,
    )

    answer = ai_response.choices[0].message.content.strip()
    print(answer)
    return answer


def process_url(url):
    if len(url) <= 30:
        print(f"Skipping URL due to short length: {url}")
        return None
    try:
        title, content, date = extract_article_data(url)
        
        if not title or not content:
            return None
       
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
    except Exception as e:
        print(f"Error processing {url}: {e}")
    return None

def process_urls_from_json(input_json_file, output_json_file):
    with open(input_json_file, 'r') as json_file:
        urls_data = json.load(json_file)

    results = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for website, urls in urls_data.items():
            for url in urls:
                futures.append(executor.submit(process_url, url))

        for future in as_completed(futures):
            article_data = future.result()
            if article_data:
                results.append(article_data)

    with open(output_json_file, 'w') as json_file:
        json.dump(results, json_file, indent=4)

    print(f"Processing complete. Results saved to {output_json_file}")

if __name__ == "__main__":
    input_json_file = "fire_scraped_urls.json"  
    output_json_file = "fire_incident_results.json"  
    process_urls_from_json(input_json_file, output_json_file)
