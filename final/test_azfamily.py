import asyncio
import json
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# AZ Family URL
AZFAMILY_URL = 'https://www.azfamily.com/search/?query=fire'

async def test_azfamily_scraping():
    """Test AZ Family scraping with better error handling"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-gpu',
                '--disable-infobars',
                '--window-size=1920,1080',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()

        try:
            print(f"🔍 Testing AZ Family URL: {AZFAMILY_URL}")
            
            # Navigate to the page with longer timeout
            await page.goto(AZFAMILY_URL, timeout=60000)
            print("✅ Successfully loaded the page")
            
            # Wait for content to load
            await page.wait_for_load_state("domcontentloaded", timeout=30000)
            print("✅ DOM content loaded")
            
            # Wait a bit more for dynamic content
            await asyncio.sleep(5)
            
            # Get the page content
            content = await page.content()
            print(f"✅ Got page content ({len(content)} characters)")
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")
            
            # Look for the specific elements from the HTML you provided
            articles = soup.select("div.queryly_item_row")
            print(f"🔍 Found {len(articles)} queryly_item_row elements")
            
            if articles:
                print("📰 Sample articles found:")
                for i, article in enumerate(articles[:3]):  # Show first 3
                    title_el = article.select_one(".queryly_item_title")
                    date_el = article.select_one("div[style*='margin-top:6px']")
                    link_el = article.select_one("a")
                    
                    title = title_el.text.strip() if title_el else "No title"
                    date = date_el.text.strip() if date_el else "No date"
                    link = link_el.get('href') if link_el else "No link"
                    
                    print(f"  {i+1}. {title}")
                    print(f"     Date: {date}")
                    print(f"     Link: {link}")
                    print()
            
            # Save the HTML for inspection
            with open('azfamily_test_page.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ Saved page HTML to azfamily_test_page.html")
            
        except PlaywrightTimeout as e:
            print(f"❌ Timeout error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_azfamily_scraping()) 