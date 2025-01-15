import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import openai
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])



def extract_article_data(url):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get(url)
        titles = driver.find_elements(By.TAG_NAME, 'h1')
        title = ' '.join([title.text for title in titles])
        # title = driver.title
        content_elements = driver.find_elements(By.TAG_NAME, 'p')
        content = ' '.join([element.text for element in content_elements])
        return title, content
    finally:
        driver.quit()



def verify_fire_incident(title, content, url):
    print(title, content)
    truncated_content = content[:2000]
    prompt = (
        "You are an AI tasked with determining if a news article describes a specific fire incident. "
        "The article must involve accidental or unintended fires affecting homes, houses, apartments, buildings, or people. "
        "These may include fires caused by electrical faults, negligence, accidents, or natural causes (e.g., forest fires reaching homes).\n\n"
        f"Title: {title}\nContent: {truncated_content}\nURL: {url}\n\n"
        "Extract the publication date from the content or URL, if possible. If the date is found in the URL, return it in the format 'dd-mm-yyyy'. "
        "If the date is found in the content, convert the date into the format 'dd-mm-yyyy'. If the date cannot be determined, respond with 'Date not available'. "
        "Also, determine if the article is related to a fire incident and answer with 'yes' or 'no'."
    )
    messages = [
        {"role": "system", "content": "You are an AI that determines if news articles are about fire incidents."},
        {"role": "user", "content": f"{prompt}"}
    ]

    ai_response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=messages,
        # max_tokens=5,
        temperature=0,
        # n=1,
        # stop=None,
    )

    answer = ai_response.choices[0].message.content.strip()
    
    return answer
def process_urls_from_excel(excel_file_path, output_file_path):
    df = pd.read_excel(excel_file_path)
    urls = df['URL']  # Assuming the column with URLs is named 'URL'
    
    results = []
    for url in urls:
        title, content = extract_article_data(url)
        result = verify_fire_incident(title, content, url)
        if 'yes' in result.lower():
            results.append({'URL': url, 'Fire Incident': 'Yes'})
        else:
            results.append({'URL': url, 'Fire Incident': 'No'})
    
    # Create a DataFrame with the results and save to a new Excel file
    result_df = pd.DataFrame(results)
    result_df.to_excel(output_file_path, index=False)
if __name__ == "__main__":

    input_excel_file = "latimes_fire_articles.xlsx"  # Input file with URLs
    output_excel_file = "fire_incident_results111.xlsx"  # Output file with results
    process_urls_from_excel(input_excel_file, output_excel_file)
    print("Processing complete. Results saved to", output_excel_file)
