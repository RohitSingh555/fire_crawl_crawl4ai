#!/usr/bin/env python3
"""
Fire Incident Verification Script
Processes scraped articles and verifies fire incidents using AI
"""

import os
import json
import re
import asyncio
import requests
import csv
from datetime import datetime
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
import time
import random
from urllib.parse import urlparse
from pathlib import Path

load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

def verify_fire_incident(title, content, date, url, source):
    """Verify if an article describes a real fire incident using AI"""
    print(f"🔍 Verifying: {title[:60]}...")
    
    truncated_content = content[:2000] if content else ""
    
    # Enhanced prompt for fire incident verification
    prompt = (
        f"A fire incident refers strictly to an unintended or accidental fire that results in damage to physical structures, "
        "such as homes, apartments, offices, commercial buildings, factories, or any infrastructure, within the United States. "
        "The fire must have caused structural damage or destruction and can be due to causes such as electrical faults, "
        "negligence, accidents, natural disasters (e.g., wildfires), or arson.\n\n"
        "Please carefully evaluate the article content and respond according to the following criteria:\n\n"
        "1. Does the article explicitly mention fire-related damage to physical structures? Respond with 'yes' only if structural damage "
        "(e.g., destruction, partial damage, collapse, repairs needed) is clearly described. Otherwise, respond with 'no'.\n\n"
        "2. If the article mentions fire but only in passing (e.g., 'fire safety tips', 'fire department training', 'fireworks'), respond with 'no'.\n\n"
        f"Title: {title}\nContent: {truncated_content}\nURL: {url}\nDate: {date}\nSource: {source}\n\n"
        "Ensure your response is clear and strictly follows the criteria outlined above."
    )

    messages = [
        {
            "role": "system",
            "content": "You are an AI tasked with evaluating news articles to determine if they describe actual fire incidents causing structural damage. Only articles explicitly mentioning damage to physical structures within the United States should be considered relevant."
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
        print(f"   AI Response: {answer}")
        return answer.lower().strip()
    except Exception as e:
        print(f"   ❌ Error with OpenAI API: {e}")
        return "no"

def process_article(article_data):
    """Process a single article for fire incident verification"""
    try:
        title = article_data.get('title', '')
        content = article_data.get('content', '')
        date = article_data.get('published_date', '')
        url = article_data.get('url', '')
        source = article_data.get('source', '')
        fire_score = article_data.get('fire_related_score', 0.0)
        
        # Skip articles with very low fire scores
        if fire_score < 0.1:
            print(f"⏭️  Skipping low fire score: {title[:50]}... (Score: {fire_score})")
            return None
        
        # Verify with AI
        verification_result = verify_fire_incident(title, content, date, url, source)
        
        if 'yes' in verification_result:
            verified_article = {
                'title': title,
                'content': content[:1000],  # Truncate for CSV
                'published_date': date,
                'url': url,
                'source': source,
                'fire_related_score': fire_score,
                'verification_result': verification_result,
                'verified_at': datetime.now().isoformat()
            }
            print(f"   ✅ Verified fire incident: {title[:50]}...")
            return verified_article
        else:
            print(f"   ❌ Not a fire incident: {title[:50]}...")
            return None
            
    except Exception as e:
        print(f"   ❌ Error processing article: {e}")
        return None

def process_scraped_results(input_file, output_csv_file, output_json_file):
    """Process scraped results and verify fire incidents"""
    print("🚀 Starting fire incident verification process...")
    
    try:
        # Load scraped articles
        with open(input_file, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        
        print(f"📊 Loaded {len(articles)} articles from {input_file}")
        
        # Clear output files
        with open(output_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            csvfile.write('')  # Clear CSV file
        
        with open(output_json_file, 'w', encoding='utf-8') as jsonfile:
            json.dump([], jsonfile)  # Clear JSON file
        
        verified_articles = []
        processed = 0
        
        # Process articles with threading
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for article in articles:
                futures.append(executor.submit(process_article, article))
            
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=120)  # 2 minute timeout
                    processed += 1
                    
                    if result:
                        verified_articles.append(result)
                    
                    print(f"📈 Progress: {processed}/{len(articles)} articles processed")
                    
                except FuturesTimeoutError:
                    print("⏰ Article processing timed out")
                    processed += 1
                except Exception as e:
                    print(f"❌ Error processing article: {e}")
                    processed += 1
        
        # Save verified articles to CSV
        if verified_articles:
            with open(output_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'title', 'content', 'published_date', 'url', 'source', 
                    'fire_related_score', 'verification_result', 'verified_at'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(verified_articles)
        
        # Save verified articles to JSON
        with open(output_json_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(verified_articles, jsonfile, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 Verification complete!")
        print(f"📊 Results:")
        print(f"   Total articles processed: {len(articles)}")
        print(f"   Verified fire incidents: {len(verified_articles)}")
        print(f"   Success rate: {(len(verified_articles)/len(articles)*100):.1f}%")
        print(f"📁 Output files:")
        print(f"   CSV: {output_csv_file}")
        print(f"   JSON: {output_json_file}")
        
        return verified_articles
        
    except FileNotFoundError:
        print(f"❌ Input file not found: {input_file}")
        return []
    except Exception as e:
        print(f"❌ Error processing scraped results: {e}")
        return []

def find_latest_scraped_file():
    """Find the most recent scraped articles file"""
    scraped_dir = Path('scraped_articles')
    if not scraped_dir.exists():
        print("❌ No scraped_articles directory found")
        return None
    
    # Find all fire_articles_*.json files
    json_files = list(scraped_dir.glob('fire_articles_*.json'))
    if not json_files:
        print("❌ No scraped articles files found")
        return None
    
    # Return the most recent file
    latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
    print(f"📁 Found latest scraped file: {latest_file}")
    return str(latest_file)

def main():
    """Main function"""
    print("🔥 Fire Incident Verification Script")
    print("=" * 50)
    
    # Check for OpenAI API key
    if not os.environ.get('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Find input file
    input_file = find_latest_scraped_file()
    if not input_file:
        print("❌ No scraped articles found. Please run the scraper first:")
        print("python src/enhanced_scraper.py")
        return
    
    # Create output directory
    output_dir = Path('verified_results')
    output_dir.mkdir(exist_ok=True)
    
    # Generate output filenames with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_csv_file = output_dir / f"verified_fire_incidents_{timestamp}.csv"
    output_json_file = output_dir / f"verified_fire_incidents_{timestamp}.json"
    
    # Process articles
    verified_articles = process_scraped_results(
        input_file, 
        str(output_csv_file), 
        str(output_json_file)
    )
    
    if verified_articles:
        print(f"\n🔥 Top 5 verified fire incidents:")
        for i, article in enumerate(verified_articles[:5], 1):
            print(f"{i}. {article['title'][:80]}...")
            print(f"   Source: {article['source']}")
            print(f"   Date: {article['published_date']}")
            print(f"   Fire Score: {article['fire_related_score']:.2f}")
            print()
        
        # Automatically send email with results
        print("\n📧 Sending verification results via email...")
        try:
            from mailer import main as send_email
            send_email()
            print("✅ Email sent successfully!")
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            print("You can manually send the email by running:")
            print("python src/mailer.py")
    else:
        print("\n❌ No verified fire incidents found. Email will not be sent.")

if __name__ == "__main__":
    main()

