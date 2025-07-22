#!/usr/bin/env python3
"""
Combined Fire Incident Pipeline
Runs enhanced scraper and mainstream media scraper in parallel, then combines results
"""

import asyncio
import os
import sys
import time
import csv
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_header(title):
    print("\n" + "="*60)
    print(f"🔥 {title}")
    print("="*60)

def print_step(step_num, total_steps, title):
    print(f"\n📋 Step {step_num}/{total_steps}: {title}")
    print("-" * 50)

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

async def run_enhanced_scraper():
    """Run the enhanced scraper"""
    print_info("Starting enhanced scraper...")
    try:
        from enhanced_scraper import main as scraper_main
        await scraper_main()
        print_success("Enhanced scraper completed")
        return True
    except Exception as e:
        print_error(f"Enhanced scraper failed: {e}")
        return False

async def run_mainstream_media_scraper():
    """Run the mainstream media scraper"""
    print_info("Starting mainstream media scraper...")
    try:
        # Change to mainstream_media directory
        original_dir = os.getcwd()
        os.chdir('mainstream_media')
        
        # Import and run the mainstream media scraper
        from run_all_mainstream_media import main as mainstream_main
        mainstream_main()
        
        # Return to original directory
        os.chdir(original_dir)
        print_success("Mainstream media scraper completed")
        return True
    except Exception as e:
        print_error(f"Mainstream media scraper failed: {e}")
        # Make sure we return to original directory even if there's an error
        if 'original_dir' in locals():
            os.chdir(original_dir)
        return False

async def run_verification():
    """Run the verification process"""
    print_info("Starting enhanced scraper verification...")
    try:
        from verification import main as verification_main
        verification_main()
        print_success("Enhanced verification completed")
        return True
    except Exception as e:
        print_error(f"Enhanced verification failed: {e}")
        return False

async def run_mainstream_verification():
    """Run the mainstream media verification process"""
    print_info("Starting mainstream media verification...")
    try:
        original_dir = os.getcwd()
        os.chdir('mainstream_media')
        
        from verification import main as mainstream_verification_main
        mainstream_verification_main()
        
        os.chdir(original_dir)
        print_success("Mainstream media verification completed")
        return True
    except Exception as e:
        print_error(f"Mainstream media verification failed: {e}")
        if 'original_dir' in locals():
            os.chdir(original_dir)
        return False

def combine_csv_files():
    """Combine both CSV files into one with 5 columns: title, url, content, date, source"""
    print_info("Combining CSV files...")
    
    try:
        # Find latest enhanced scraper CSV
        enhanced_pattern = "verified_fire_incidents_*.csv"
        enhanced_files = list(Path('verified_results').glob(enhanced_pattern))
        
        # Find latest mainstream media CSV (in mainstream_media directory)
        mainstream_pattern = "verified_mainstream_media_fire_incidents_*.csv"
        mainstream_files = list(Path('mainstream_media').glob(mainstream_pattern))
        
        if not enhanced_files:
            print_error("No enhanced scraper CSV files found")
            return None
            
        if not mainstream_files:
            print_error("No mainstream media CSV files found")
            return None
        
        latest_enhanced = max(enhanced_files, key=lambda x: x.stat().st_mtime)
        latest_mainstream = max(mainstream_files, key=lambda x: x.stat().st_mtime)
        
        print_info(f"Enhanced CSV: {latest_enhanced}")
        print_info(f"Mainstream CSV: {latest_mainstream}")
        
        # Read enhanced scraper CSV
        enhanced_articles = []
        with open(latest_enhanced, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                enhanced_articles.append({
                    'title': row.get('title', ''),
                    'url': row.get('url', ''),
                    'content': row.get('content', ''),
                    'date': row.get('published_date', ''),
                    'source': row.get('source', '')
                })
        
        # Read mainstream media CSV
        mainstream_articles = []
        with open(latest_mainstream, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                mainstream_articles.append({
                    'title': row.get('title', ''),
                    'url': row.get('url', ''),
                    'content': row.get('content', ''),
                    'date': row.get('published_date', ''),
                    'source': row.get('source', '')
                })
        
        print_info(f"Enhanced articles: {len(enhanced_articles)}")
        print_info(f"Mainstream articles: {len(mainstream_articles)}")
        
        # Combine and remove duplicates
        all_articles = enhanced_articles + mainstream_articles
        unique_articles = []
        seen_urls = set()
        
        for article in all_articles:
            if article['url'] not in seen_urls:
                unique_articles.append(article)
                seen_urls.add(article['url'])
        
        print_info(f"Total unique articles: {len(unique_articles)}")
        
        # Save combined CSV with only 5 columns
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        combined_filename = f"verified_results/combined_fire_incidents_{timestamp}.csv"
        
        with open(combined_filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['title', 'url', 'content', 'date', 'source']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for article in unique_articles:
                writer.writerow(article)
        
        print_success(f"Combined CSV saved: {combined_filename}")
        return combined_filename
        
    except Exception as e:
        print_error(f"Failed to combine CSV files: {e}")
        return None

def run_mailer():
    """Run the email sender"""
    print_info("Sending email report...")
    try:
        from mailer import main as mailer_main
        mailer_main()
        print_success("Email sent successfully")
        return True
    except Exception as e:
        print_error(f"Email sending failed: {e}")
        return False

async def main():
    """Main pipeline function"""
    print_header("Combined Fire Incident Pipeline")
    
    print("""
This pipeline runs both scrapers in parallel:

1. 🔍 Enhanced Scraper (Local News) + 📰 Mainstream Media Scraper (National News)
2. 🤖 AI Verification (Both in parallel)
3. 🔗 Combine CSV Results (5 columns: title, url, content, date, source)
4. 📧 Send Email Report
""")
    
    # Check prerequisites
    if not os.environ.get('OPENAI_API_KEY'):
        print_error("OPENAI_API_KEY not found")
        return
    
    # Create directories
    Path('scraped_articles').mkdir(exist_ok=True)
    Path('verified_results').mkdir(exist_ok=True)
    Path('mainstream_media').mkdir(exist_ok=True)
    
    start_time = time.time()
    pipeline_success = True
    
    try:
        # Step 1: Run both scrapers in parallel
        print_step(1, 4, "Running Scrapers in Parallel")
        scraper_tasks = [
            run_enhanced_scraper(),
            run_mainstream_media_scraper()
        ]
        
        scraper_results = await asyncio.gather(*scraper_tasks, return_exceptions=True)
        
        for i, result in enumerate(scraper_results):
            if isinstance(result, Exception) or not result:
                print_error(f"Scraper {i+1} failed")
                pipeline_success = False
        
        if not pipeline_success:
            return
        
        # Step 2: Run both verifications in parallel
        print_step(2, 4, "Running Verifications in Parallel")
        verification_tasks = [
            run_verification(),
            run_mainstream_verification()
        ]
        
        verification_results = await asyncio.gather(*verification_tasks, return_exceptions=True)
        
        for i, result in enumerate(verification_results):
            if isinstance(result, Exception) or not result:
                print_error(f"Verification {i+1} failed")
                pipeline_success = False
        
        if not pipeline_success:
            return
        
        # Step 3: Combine CSV files
        print_step(3, 4, "Combining CSV Results")
        combined_file = combine_csv_files()
        if not combined_file:
            pipeline_success = False
            return
        
        # Step 4: Send email
        print_step(4, 4, "Sending Email Report")
        email_success = run_mailer()
        if not email_success:
            pipeline_success = False
        
        # Pipeline completion
        elapsed_time = time.time() - start_time
        
        print_header("Pipeline Complete")
        
        if pipeline_success:
            print_success("🎉 All steps completed successfully!")
            print(f"⏱️  Total execution time: {elapsed_time:.1f} seconds")
            print("\n📊 Pipeline Results:")
            print("   ✅ Enhanced scraper: Completed")
            print("   ✅ Mainstream media scraper: Completed")
            print("   ✅ AI verification: Completed")
            print("   ✅ CSV combination: Completed")
            print("   ✅ Email report: Sent")
            print(f"\n📄 Combined CSV: {combined_file}")
            print("\n📧 Check your email for the daily fire incident report!")
        else:
            print_error("Pipeline completed with errors")
            print("Please check the logs above for details")
        
    except KeyboardInterrupt:
        print_error("Pipeline interrupted by user")
    except Exception as e:
        print_error(f"Pipeline failed with unexpected error: {e}")
    
    print("\n🏁 Pipeline finished.")

if __name__ == "__main__":
    asyncio.run(main()) 