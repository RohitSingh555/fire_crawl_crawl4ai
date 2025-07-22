#!/usr/bin/env python3
"""
Fire Incident Pipeline - Complete Workflow with Mainstream Media Integration
Runs enhanced scraper, mainstream media scraper, verification, and email sending in sequence
"""

import asyncio
import os
import sys
import time
import json
import csv
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_header(title):
    """Print a beautiful header"""
    print("\n" + "="*60)
    print(f"🔥 {title}")
    print("="*60)

def print_step(step_num, total_steps, title):
    """Print a step header"""
    print(f"\n📋 Step {step_num}/{total_steps}: {title}")
    print("-" * 50)

def print_success(message):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"❌ {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")

async def run_enhanced_scraper():
    """Run the enhanced scraper"""
    print_step(1, 5, "Running Enhanced Fire Scraper")
    
    try:
        # Import and run the enhanced scraper
        from enhanced_scraper import main as scraper_main
        
        print_info("Starting enhanced scraper with SSL bypass and better detection...")
        start_time = time.time()
        
        await scraper_main()
        
        elapsed_time = time.time() - start_time
        print_success(f"Enhanced scraper completed in {elapsed_time:.1f} seconds")
        
        return True
        
    except Exception as e:
        print_error(f"Enhanced scraper failed: {e}")
        return False

async def run_mainstream_media_scraper():
    """Run the mainstream media scraper"""
    print_step(2, 5, "Running Mainstream Media Scraper")
    
    try:
        # Change to mainstream_media directory
        original_dir = os.getcwd()
        os.chdir('mainstream_media')
        
        print_info("Starting mainstream media scraper (ABC7, ABC News, CBC, Coventry Telegraph)...")
        start_time = time.time()
        
        # Run the mainstream media scraper using subprocess
        import subprocess
        result = subprocess.run([sys.executable, 'run_all_mainstream_media.py'], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            elapsed_time = time.time() - start_time
            print_success(f"Mainstream media scraper completed in {elapsed_time:.1f} seconds")
            if result.stdout:
                print_info("Mainstream media output: " + result.stdout.strip())
        else:
            print_error(f"Mainstream media scraper failed with return code {result.returncode}")
            if result.stderr:
                print_error("Error: " + result.stderr.strip())
            # Return to original directory
            os.chdir(original_dir)
            return False
        
        # Return to original directory
        os.chdir(original_dir)
        
        return True
        
    except subprocess.TimeoutExpired:
        print_error("Mainstream media scraper timed out after 5 minutes")
        if 'original_dir' in locals():
            os.chdir(original_dir)
        return False
    except Exception as e:
        print_error(f"Mainstream media scraper failed: {e}")
        # Make sure we return to original directory even if there's an error
        if 'original_dir' in locals():
            os.chdir(original_dir)
        return False

async def run_verification():
    """Run the verification process"""
    print_step(3, 5, "Running Fire Incident Verification")
    
    try:
        # Check for OpenAI API key
        if not os.environ.get('OPENAI_API_KEY'):
            print_error("OPENAI_API_KEY not found in environment variables")
            print_info("Please set your OpenAI API key:")
            print("export OPENAI_API_KEY='your-api-key-here'")
            return False
        
        # Import and run verification
        from verification import main as verification_main
        
        print_info("Starting AI-powered fire incident verification...")
        start_time = time.time()
        
        verification_main()
        
        elapsed_time = time.time() - start_time
        print_success(f"Verification completed in {elapsed_time:.1f} seconds")
        
        return True
        
    except Exception as e:
        print_error(f"Verification failed: {e}")
        return False

async def run_mainstream_media_verification():
    """Run the mainstream media verification process"""
    print_step(4, 5, "Running Mainstream Media Verification")
    
    try:
        # Check for OpenAI API key
        if not os.environ.get('OPENAI_API_KEY'):
            print_error("OPENAI_API_KEY not found in environment variables")
            return False
        
        # Change to mainstream media directory and run verification
        original_dir = os.getcwd()
        os.chdir('mainstream_media')
        
        print_info("Starting AI-powered mainstream media verification...")
        start_time = time.time()
        
        # Run mainstream media verification using subprocess
        import subprocess
        result = subprocess.run([sys.executable, 'verification.py'], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            elapsed_time = time.time() - start_time
            print_success(f"Mainstream media verification completed in {elapsed_time:.1f} seconds")
            if result.stdout:
                print_info("Mainstream verification output: " + result.stdout.strip())
        else:
            print_error(f"Mainstream media verification failed with return code {result.returncode}")
            if result.stderr:
                print_error("Error: " + result.stderr.strip())
            # Change back to original directory
            os.chdir(original_dir)
            return False
        
        # Change back to original directory
        os.chdir(original_dir)
        
        return True
        
    except subprocess.TimeoutExpired:
        print_error("Mainstream media verification timed out after 5 minutes")
        if 'original_dir' in locals():
            os.chdir(original_dir)
        return False
    except Exception as e:
        print_error(f"Mainstream media verification failed: {e}")
        # Change back to original directory in case of error
        if 'original_dir' in locals():
            os.chdir(original_dir)
        return False

def combine_csv_files():
    """Combine both CSV files into one with 5 columns: title, url, content, date, source"""
    print_step(5, 5, "Combining CSV Results")
    
    try:
        # Find the latest enhanced scraper CSV
        enhanced_pattern = "verified_fire_incidents_*.csv"
        enhanced_files = list(Path('verified_results').glob(enhanced_pattern))
        
        # Find the latest mainstream media CSV
        mainstream_pattern = "verified_mainstream_media_fire_incidents_*.csv"
        mainstream_files = list(Path('mainstream_media').glob(mainstream_pattern))
        
        if not enhanced_files:
            print_error("No enhanced scraper CSV files found")
            return None
            
        if not mainstream_files:
            print_error("No mainstream media CSV files found")
            return None
        
        # Get the latest files
        latest_enhanced = max(enhanced_files, key=lambda x: x.stat().st_mtime)
        latest_mainstream = max(mainstream_files, key=lambda x: x.stat().st_mtime)
        
        print_info(f"Enhanced scraper CSV: {latest_enhanced}")
        print_info(f"Mainstream media CSV: {latest_mainstream}")
        
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
        
        print_info(f"Enhanced scraper articles: {len(enhanced_articles)}")
        print_info(f"Mainstream media articles: {len(mainstream_articles)}")
        
        # Combine articles
        all_articles = enhanced_articles + mainstream_articles
        
        # Remove duplicates based on URL
        unique_articles = []
        seen_urls = set()
        for article in all_articles:
            if article['url'] not in seen_urls:
                unique_articles.append(article)
                seen_urls.add(article['url'])
        
        print_info(f"Total unique articles after combining: {len(unique_articles)}")
        
        # Save combined CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        combined_filename = f"verified_results/combined_fire_incidents_{timestamp}.csv"
        
        with open(combined_filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['title', 'url', 'content', 'date', 'source']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for article in unique_articles:
                writer.writerow(article)
        
        print_success(f"Combined CSV saved to: {combined_filename}")
        return combined_filename
        
    except Exception as e:
        print_error(f"Failed to combine CSV files: {e}")
        return None

def run_mailer():
    """Run the email sender"""
    print_step(6, 6, "Sending Daily Fire Incident Report")
    
    try:
        # Import and run mailer
        from mailer import main as mailer_main
        
        print_info("Sending beautiful daily fire incident report...")
        start_time = time.time()
        
        mailer_main()
        
        elapsed_time = time.time() - start_time
        print_success(f"Email sent successfully in {elapsed_time:.1f} seconds")
        
        return True
        
    except Exception as e:
        print_error(f"Email sending failed: {e}")
        return False

def check_prerequisites():
    """Check if all prerequisites are met"""
    print_info("Checking prerequisites...")
    
    # Check for required directories
    required_dirs = ['scraped_articles', 'verified_results', 'mainstream_media']
    for dir_name in required_dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print_success(f"Directory '{dir_name}' ready")
    
    # Check for OpenAI API key
    if not os.environ.get('OPENAI_API_KEY'):
        print_error("OPENAI_API_KEY not found")
        print_info("Please set your OpenAI API key before running the pipeline")
        return False
    
    print_success("All prerequisites met")
    return True

def show_pipeline_summary():
    """Show a summary of what the pipeline does"""
    print_header("Fire Incident Pipeline - Complete Workflow with Mainstream Media")
    
    print("""
This pipeline automates the complete fire incident monitoring process:

1. 🔍 Enhanced Scraper
   • Scrapes 100+ local news websites for fire-related content
   • Uses SSL bypass and anti-detection techniques
   • Filters articles by fire relevance score
   • Saves results to scraped_articles/ directory

2. 📰 Mainstream Media Scraper
   • Scrapes ABC7, ABC News, CBC, and Coventry Telegraph
   • Formats results to match main scraper structure
   • Saves results to mainstream_media/ directory

3. 🤖 AI Verification (Parallel)
   • Uses OpenAI GPT-4 to verify real fire incidents
   • Runs verification on both enhanced and mainstream media results
   • Filters out false positives and non-structural fires
   • Generates verified CSV and JSON reports

4. 🔗 CSV Combination
   • Combines both verification results into single CSV
   • Removes duplicate articles based on URL
   • Creates unified dataset with 5 columns: title, url, content, date, source

5. 📧 Daily Email Report
   • Creates beautiful HTML email with verification summary
   • Attaches combined CSV file for data analysis
   • Sends to multiple stakeholders automatically
   • Professional formatting with statistics and top incidents

Expected Output:
• Combined CSV with all verified fire incidents
• Beautiful daily email report with CSV attachment
• Complete audit trail of the process
""")

async def main():
    """Main pipeline function"""
    show_pipeline_summary()
    
    # Check prerequisites
    if not check_prerequisites():
        print_error("Prerequisites not met. Please fix the issues above and try again.")
        return
    
    # Track overall success
    pipeline_success = True
    start_time = time.time()
    
    try:
        # Step 1 & 2: Run both scrapers in parallel
        print_info("Running scrapers in parallel...")
        scraper_tasks = [
            run_enhanced_scraper(),
            run_mainstream_media_scraper()
        ]
        
        scraper_results = await asyncio.gather(*scraper_tasks, return_exceptions=True)
        
        # Check scraper results - enhanced scraper is required, mainstream is optional
        enhanced_success = False
        mainstream_success = False
        
        for i, result in enumerate(scraper_results):
            if i == 0:  # Enhanced scraper
                if isinstance(result, Exception):
                    print_error(f"Enhanced scraper failed: {result}")
                    pipeline_success = False
                elif not result:
                    print_error("Enhanced scraper failed")
                    pipeline_success = False
                else:
                    enhanced_success = True
            else:  # Mainstream media scraper
                if isinstance(result, Exception):
                    print_error(f"Mainstream media scraper failed: {result}")
                    print_info("Continuing with enhanced scraper only...")
                elif not result:
                    print_error("Mainstream media scraper failed")
                    print_info("Continuing with enhanced scraper only...")
                else:
                    mainstream_success = True
        
        if not enhanced_success:
            print_error("Pipeline stopped due to enhanced scraper failure")
            return
        
        # Step 3 & 4: Run verifications based on what succeeded
        print_info("Running verifications...")
        verification_tasks = []
        
        # Always run enhanced verification
        verification_tasks.append(run_verification())
        
        # Only run mainstream verification if scraper succeeded
        if mainstream_success:
            verification_tasks.append(run_mainstream_media_verification())
        else:
            print_info("Skipping mainstream media verification due to scraper failure")
        
        verification_results = await asyncio.gather(*verification_tasks, return_exceptions=True)
        
        # Check verification results
        enhanced_verification_success = False
        mainstream_verification_success = False
        
        for i, result in enumerate(verification_results):
            if i == 0:  # Enhanced verification
                if isinstance(result, Exception):
                    print_error(f"Enhanced verification failed: {result}")
                    pipeline_success = False
                elif not result:
                    print_error("Enhanced verification failed")
                    pipeline_success = False
                else:
                    enhanced_verification_success = True
            else:  # Mainstream verification (if it ran)
                if isinstance(result, Exception):
                    print_error(f"Mainstream verification failed: {result}")
                    print_info("Continuing with enhanced verification only...")
                elif not result:
                    print_error("Mainstream verification failed")
                    print_info("Continuing with enhanced verification only...")
                else:
                    mainstream_verification_success = True
        
        if not enhanced_verification_success:
            print_error("Pipeline stopped due to enhanced verification failure")
            return
        
        # Step 5: Combine CSV files (handle case where mainstream failed)
        combined_file = None
        if mainstream_success and mainstream_verification_success:
            combined_file = combine_csv_files()
            if not combined_file:
                print_error("CSV combination failed, but continuing with enhanced scraper results")
        else:
            print_info("Using enhanced scraper results only (no mainstream media data)")
            # Find the latest enhanced scraper CSV and use it directly
            enhanced_pattern = "verified_fire_incidents_*.csv"
            enhanced_files = list(Path('verified_results').glob(enhanced_pattern))
            if enhanced_files:
                latest_enhanced = max(enhanced_files, key=lambda x: x.stat().st_mtime)
                combined_file = str(latest_enhanced)
                print_success(f"Using enhanced scraper CSV: {combined_file}")
            else:
                print_error("No enhanced scraper CSV found")
                pipeline_success = False
        
        if not combined_file:
            print_error("Pipeline stopped due to no CSV data available")
            return
        
        # Step 6: Send Email
        email_success = run_mailer()
        if not email_success:
            pipeline_success = False
            print_error("Pipeline completed but email sending failed")
        
        # Pipeline completion
        elapsed_time = time.time() - start_time
        
        print_header("Pipeline Complete")
        
        if pipeline_success:
            print_success("🎉 All steps completed successfully!")
            print(f"⏱️  Total execution time: {elapsed_time:.1f} seconds")
            print("\n📊 Pipeline Results:")
            print("   ✅ Enhanced scraper: Completed")
            if mainstream_success:
                print("   ✅ Mainstream media scraper: Completed")
            else:
                print("   ⚠️  Mainstream media scraper: Failed (continued with enhanced only)")
            
            if enhanced_verification_success:
                print("   ✅ Enhanced verification: Completed")
            if mainstream_verification_success:
                print("   ✅ Mainstream media verification: Completed")
            elif mainstream_success:
                print("   ⚠️  Mainstream media verification: Failed")
            
            if combined_file and "combined_fire_incidents" in str(combined_file):
                print("   ✅ CSV combination: Completed")
            else:
                print("   ✅ CSV: Using enhanced scraper results")
            
            print("   ✅ Email report: Sent")
            print(f"\n📄 Final CSV: {combined_file}")
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
    # Run the pipeline
    asyncio.run(main()) 