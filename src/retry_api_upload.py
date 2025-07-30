#!/usr/bin/env python3
"""
API Upload Retry Script
Retries sending JSON data to the bulk upload API endpoint
"""

import os
import json
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import argparse

def extract_channel(url):
    """Extract channel name from URL"""
    parsed_url = urlparse(url)
    return parsed_url.netloc.split('.')[1]

def parse_date(date_str):
    """Parse date string to datetime object"""
    try:
        return datetime.strptime(date_str, "%d-%m-%Y")
    except ValueError:
        try:
            from dateutil import parser
            return parser.parse(date_str)
        except:
            return None

def load_verified_articles_from_csv(csv_file):
    """Load verified articles from CSV file and convert to API format"""
    print(f"📁 Loading verified articles from: {csv_file}")
    
    try:
        df = pd.read_csv(csv_file)
        print(f"✅ Loaded {len(df)} articles from CSV")
        
        api_items = []
        for _, row in df.iterrows():
            # Parse the date to ISO format
            date_str = row.get("published_date", "")
            published_date = None
            if date_str and pd.notna(date_str):
                parsed_date = parse_date(str(date_str))
                if parsed_date:
                    published_date = parsed_date.isoformat()
            
            # Handle NaN values in fire_related_score
            fire_score = row.get("fire_related_score", 0.8)
            if pd.isna(fire_score):
                fire_score = 0.8
            fire_score = float(fire_score)
            
            # Create item structure matching the API format
            api_item = {
                "title": str(row.get("title", "") or ""),
                "content": str(row.get("content", "") or ""),
                "published_date": published_date or "",
                "url": str(row.get("url", "") or ""),
                "source": str(row.get("source", "") or ""),
                "fire_related_score": fire_score,
                "verification_result": str(row.get("verification_result", "yes") or "yes"),
                "verified_at": str(row.get("verified_at", datetime.now().isoformat())),
                "state": str(row.get("state", "") or ""),
                "county": str(row.get("county", "") or ""),
                "city": str(row.get("city", "") or ""),
                "province": "",  # Server expects this field
                "country": "USA",
                "image_url": "",
                "tags": "fire,emergency,news",
                "reporter_name": "Web"
            }
            
            # Only add latitude/longitude if they have valid values
            # Otherwise omit them to let the server use defaults
            if row.get("latitude") and pd.notna(row.get("latitude")):
                api_item["latitude"] = float(row.get("latitude"))
            if row.get("longitude") and pd.notna(row.get("longitude")):
                api_item["longitude"] = float(row.get("longitude"))
            api_items.append(api_item)
        
        return {"items": api_items}
        
    except Exception as e:
        print(f"❌ Error loading CSV file: {e}")
        return None

def load_json_data_from_file(json_file):
    """Load JSON data from existing file"""
    print(f"📁 Loading JSON data from: {json_file}")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ Loaded {len(data.get('items', []))} items from JSON")
        return data
    except Exception as e:
        print(f"❌ Error loading JSON file: {e}")
        return None

def clean_json_data(data):
    """Clean JSON data to remove NaN values and ensure JSON compliance"""
    def clean_value(value):
        if pd.isna(value):
            return None
        elif isinstance(value, float) and (value != value):  # Check for NaN
            return None
        elif isinstance(value, str) and value.lower() in ['nan', 'none', 'null']:
            return ""
        return value
    
    def clean_dict(d):
        cleaned = {}
        for key, value in d.items():
            cleaned_value = clean_value(value)
            if cleaned_value is not None:
                cleaned[key] = cleaned_value
            else:
                # Use appropriate default values
                if key == "fire_related_score":
                    cleaned[key] = 0.8
                elif key in ["latitude", "longitude"]:
                    cleaned[key] = None
                else:
                    cleaned[key] = ""
        return cleaned
    
    if isinstance(data, dict):
        if "items" in data:
            # Clean each item in the list
            cleaned_items = []
            for item in data["items"]:
                cleaned_item = clean_dict(item)
                cleaned_items.append(cleaned_item)
            return {"items": cleaned_items}
        else:
            return clean_dict(data)
    return data

def upload_to_bulk_api(api_data, url='http://localhost:8000/api/fire-news/bulk-upload'):
    """Upload data to bulk upload API endpoint"""
    print(f"🌐 Uploading to bulk API: {url}")
    print(f"📊 JSON data items: {len(api_data.get('items', []))}")
    
    # Clean the JSON data to remove NaN values
    cleaned_data = clean_json_data(api_data)
    print(f"🧹 Cleaned JSON data - removed NaN values")
    
    # Debug: Show sample of cleaned JSON data being sent
    if cleaned_data.get('items'):
        print(f"📋 Sample cleaned JSON item structure:")
        sample_item = cleaned_data['items'][0]
        for key, value in sample_item.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"   {key}: {value[:100]}...")
            else:
                print(f"   {key}: {value}")
    
    # Check if server is reachable first
    server_available = True
    try:
        test_response = requests.get(url.replace('/api/fire-news/bulk-upload', '/'), timeout=5)
        print(f"🔍 Server test response: {test_response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is the server running at http://localhost:8000?")
        server_available = False
    except Exception as e:
        print(f"⚠️  Server test failed: {e}")
        server_available = False
    
    if not server_available:
        print("💡 Please start the server and try again")
        return False
    
    # Upload JSON data directly
    try:
        headers = {
            'Content-Type': 'application/json'
        }
        
        print("📤 Sending cleaned JSON data to bulk upload endpoint...")
        response = requests.post(url, json=cleaned_data, headers=headers, timeout=30)
        print(f"✅ POST request sent. Status code: {response.status_code}")
        print(f"📤 Response: {response.text}")
        print(f"📊 Sent {len(cleaned_data.get('items', []))} items in JSON data")
        
        if response.status_code == 200:
            print("🎉 Bulk upload successful!")
            return True
        else:
            print(f"❌ Upload failed with status code: {response.status_code}")
            print(f"📋 Response headers: {dict(response.headers)}")
            print(f"📄 Response content: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        print("💡 Make sure the server is running at http://localhost:8000")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ Request timeout: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to send POST request: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
        return False

def find_latest_verified_file():
    """Find the most recent verified results file"""
    verified_dir = Path('verified_results')
    if not verified_dir.exists():
        print("❌ No verified_results directory found")
        return None
    
    # Find all verified CSV files
    csv_files = list(verified_dir.glob('verified_fire_incidents_*.csv'))
    if not csv_files:
        print("❌ No verified CSV files found")
        return None
    
    # Return the most recent file
    latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
    print(f"📁 Found latest verified file: {latest_file}")
    return str(latest_file)

def save_json_for_manual_upload(api_data, output_dir):
    """Save JSON data for manual upload"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_file = output_dir / f"bulk_upload_data_{timestamp}.json"
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(api_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved JSON data: {json_file}")
    return json_file

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Retry bulk API upload for fire incident data')
    parser.add_argument('--csv', help='Path to verified CSV file')
    parser.add_argument('--json', help='Path to existing JSON data file')
    parser.add_argument('--url', default='http://localhost:8000/api/fire-news/bulk-upload', 
                       help='Bulk upload API endpoint URL')
    parser.add_argument('--latest', action='store_true', 
                       help='Use the latest verified CSV file')
    parser.add_argument('--save-only', action='store_true',
                       help='Only save JSON data, don\'t upload')
    
    args = parser.parse_args()
    
    print("🔄 Bulk API Upload Retry Script")
    print("=" * 50)
    
    # Determine input file
    input_file = None
    if args.csv:
        input_file = args.csv
        file_type = 'csv'
    elif args.json:
        input_file = args.json
        file_type = 'json'
    elif args.latest:
        input_file = find_latest_verified_file()
        file_type = 'csv'
    else:
        # Try to find latest file automatically
        input_file = find_latest_verified_file()
        file_type = 'csv'
    
    if not input_file:
        print("❌ No input file specified or found")
        print("Usage examples:")
        print("  python retry_api_upload.py --latest")
        print("  python retry_api_upload.py --csv verified_results/verified_fire_incidents_20250730_154607.csv")
        print("  python retry_api_upload.py --json verified_results/bulk_upload_data_20250730_154607.json")
        print("  python retry_api_upload.py --latest --save-only")
        return
    
    # Load data
    api_data = None
    if file_type == 'csv':
        api_data = load_verified_articles_from_csv(input_file)
    else:
        api_data = load_json_data_from_file(input_file)
    
    if not api_data:
        print("❌ Failed to load data")
        return
    
    # Create output directory
    output_dir = Path('verified_results')
    output_dir.mkdir(exist_ok=True)
    
    # Save JSON data for backup
    json_file = save_json_for_manual_upload(api_data, output_dir)
    
    if args.save_only:
        print(f"\n💾 JSON data saved to: {json_file}")
        print("💡 You can manually upload this JSON file when the server is ready")
        return
    
    # Upload to bulk API
    success = upload_to_bulk_api(api_data, args.url)
    
    if success:
        print("\n🎉 Bulk upload completed successfully!")
        print("✅ All fields including published_date should be updated in the backend")
    else:
        print("\n❌ Bulk upload failed.")
        print(f"💡 JSON data saved to: {json_file}")
        print("💡 You can manually upload this JSON file when the server is ready")

if __name__ == "__main__":
    main() 