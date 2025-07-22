#!/usr/bin/env python3
"""
Simple Fire Incident Verification Script
Filters scraped articles based on fire keywords without AI
"""

import os
import json
import csv
from datetime import datetime
from pathlib import Path
import re

# Fire-related keywords for filtering
FIRE_INCIDENT_KEYWORDS = [
    'fire broke out', 'fire destroyed', 'fire damaged', 'fire gutted',
    'fire burned', 'fire destroyed', 'fire ravaged', 'fire consumed',
    'fire spread', 'fire erupted', 'fire started', 'fire ignited',
    'house fire', 'building fire', 'apartment fire', 'business fire',
    'fire damage', 'fire destruction', 'fire loss', 'fire destroyed',
    'firefighters responded', 'fire department called', 'fire alarm',
    'fire investigation', 'fire marshal', 'fire chief', 'fire engine',
    'fire truck', 'fire station', 'fire hydrant', 'fire escape',
    'fire drill', 'fire code', 'fire safety', 'fire prevention',
    'arson', 'arsonist', 'arson investigation', 'suspicious fire',
    'electrical fire', 'kitchen fire', 'chimney fire', 'wildfire',
    'forest fire', 'brush fire', 'grass fire', 'field fire',
    'fireworks', 'firework accident', 'firework explosion',
    'smoke damage', 'smoke inhalation', 'fire victim', 'fire casualty',
    'fire fatality', 'fire death', 'fire injury', 'fire burn',
    'fire rescue', 'fire evacuation', 'fire escape', 'fire exit',
    'fire sprinkler', 'fire extinguisher', 'fire suppression',
    'fire alarm', 'fire detection', 'fire warning', 'fire alert'
]

# Keywords that indicate NOT a fire incident
NON_FIRE_KEYWORDS = [
    'fire safety tips', 'fire prevention', 'fire department training',
    'fire drill', 'fire code', 'fire inspection', 'fire permit',
    'fireworks display', 'fireworks show', 'fireworks celebration',
    'fire sale', 'fire pit', 'fireplace', 'fire starter',
    'fire ant', 'firefly', 'firebird', 'firestone', 'firefox',
    'fire department fundraiser', 'fire department open house',
    'fire safety week', 'fire prevention month', 'fire safety class'
]

def is_fire_incident(title, content):
    """Check if article describes an actual fire incident"""
    if not title or not content:
        return False
    
    text = f"{title} {content}".lower()
    
    # Check for non-fire keywords first
    for keyword in NON_FIRE_KEYWORDS:
        if keyword in text:
            return False
    
    # Check for fire incident keywords
    fire_incident_count = 0
    for keyword in FIRE_INCIDENT_KEYWORDS:
        if keyword in text:
            fire_incident_count += 1
    
    # Must have at least 2 fire incident keywords
    return fire_incident_count >= 2

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
            return None
        
        # Check if it's a fire incident
        if is_fire_incident(title, content):
            verified_article = {
                'title': title,
                'content': content[:1000],  # Truncate for CSV
                'published_date': date,
                'url': url,
                'source': source,
                'fire_related_score': fire_score,
                'verification_method': 'keyword_filtering',
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
        
        verified_articles = []
        processed = 0
        
        # Process articles
        for article in articles:
            result = process_article(article)
            processed += 1
            
            if result:
                verified_articles.append(result)
            
            if processed % 50 == 0:
                print(f"📈 Progress: {processed}/{len(articles)} articles processed")
        
        # Save verified articles to CSV
        if verified_articles:
            with open(output_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'title', 'content', 'published_date', 'url', 'source', 
                    'fire_related_score', 'verification_method', 'verified_at'
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
    print("🔥 Simple Fire Incident Verification Script")
    print("=" * 50)
    print("🔍 Using keyword-based filtering (no AI required)")
    
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
        print(f"\n🔥 Top 10 verified fire incidents:")
        for i, article in enumerate(verified_articles[:10], 1):
            print(f"{i}. {article['title'][:80]}...")
            print(f"   Source: {article['source']}")
            print(f"   Date: {article['published_date']}")
            print(f"   Fire Score: {article['fire_related_score']:.2f}")
            print()
    else:
        print("\n❌ No fire incidents found. This could mean:")
        print("   - No actual fire incidents in the scraped articles")
        print("   - Articles are about fire safety, training, etc.")
        print("   - Keyword filtering is too strict")

if __name__ == "__main__":
    main() 