import os
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

def extract_article_data(url):
    """Fetch the title and content from a URL using Selenium."""
    options = Options()
    options.add_argument('--headless')  # Ensure no browser window opens
    options.add_argument('--disable-gpu')  # Disable GPU for headless mode
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(url)
        titles = driver.find_elements(By.TAG_NAME, 'h1')
        title = ' '.join([title.text for title in titles])

        # Extract content (assuming it's in <p> tags)
        content_elements = driver.find_elements(By.TAG_NAME, 'p')
        content = ' '.join([element.text for element in content_elements])

        return title, content
    finally:
        driver.quit()

def verify_fire_incident(title, content, url):
    """Use GPT model to verify if an article is related to a fire incident and extract publication date."""
    truncated_content = content[:2000]  
    prompt = (
        "You are an AI tasked with determining if a news article describes a specific fire incident. "
        "The article must involve accidental or unintended fires affecting homes, houses, apartments, buildings, or people. "
        "These may include fires caused by electrical faults, negligence, accidents, or natural causes (e.g., forest fires reaching homes).\n\n"
        f"Title: {title}\nContent: {truncated_content}\nURL: {url}\n\n"
        "Extract the publication date from the content or URL, if possible. If the date is found in the URL, return it in the format 'dd-mm-yyyy'. "
        "If the date is found in the content, convert the date into the format 'dd-mm-yyyy'. If the date cannot be determined, respond with 'Date not available'. "
        "Also, determine if the article is related to a fire incident (NOT A BLOG!) and answer with 'yes' or 'no'."
    )

    # Prepare message for OpenAI API then 

    messages = [
        {"role": "system", "content": "You are an AI that determines if news articles are about fire incidents."},
        {"role": "user", "content": f"{prompt}"}
    ]

    # Get response from OpenAI
    ai_response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=messages,
        temperature=0,
    )

    answer = ai_response.choices[0].message.content.strip()
    print(answer)
    return answer

def process_urls_from_json(input_json_file, output_json_file):
    
    # Load input JSON data (URLs)
    with open(input_json_file, 'r') as json_file:
        urls_data = json.load(json_file)

    results = []

    for website, urls in urls_data.items():
        for url in urls:
            try:
                title, content = extract_article_data(url)
                result = verify_fire_incident(title, content, url)
                if 'yes' in result.lower():
                    date_match = re.search(r'\d{2}-\d{2}-\d{4}', result)
                    if date_match:
                        date = date_match.group(0)
                    else:
                        date = 'Date not available'

                    article_data = {
                        'Title': title,
                        'Description': content[:500], 
                        'Date': date,
                        'URL': url
                    }
                    results.append(article_data)

            except Exception as e:
                print(f"Error processing {url}: {e}")

    with open(output_json_file, 'w') as json_file:
        json.dump(results, json_file, indent=4)

    print(f"Processing complete. Results saved to {output_json_file}")

if __name__ == "__main__":
    input_json_file = "fire_scraped_urls.json"  
    output_json_file = "fire_incident_results.json"  
    process_urls_from_json(input_json_file, output_json_file)
