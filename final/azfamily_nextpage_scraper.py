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

def is_recent(date_string):
    """Check if the date is from yesterday or today"""
    try:
        # Handle "Jun 23, 2025" format
        parsed_date = parser.parse(date_string)
        today = datetime.now().date()
        article_date = parsed_date.date()
        return (today - article_date).days <= 1
    except Exception as e:
        print(f"Date parsing error: {e}")
        return False

async def extract_articles_from_page(page):
    """Extract articles from the current page"""
    articles = []
    
    try:
        # Wait for the content to load
        await page.wait_for_selector("div.queryly_item_row", timeout=10000)
        
        # Get the page content
        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")
        
        # Find all article rows
        article_rows = soup.select("div.queryly_item_row")
        print(f"Found {len(article_rows)} articles on current page")
        
        for row in article_rows:
            try:
                # Extract link
                link_elem = row.select_one("a")
                if not link_elem or not link_elem.has_attr("href"):
                    continue
                    
                href = link_elem["href"]
                
                # Skip video links and non-article links
                if href.startswith("/video/") or href.startswith("/page/"):
                    continue
                    
                # Make URL absolute
                if href.startswith("/"):
                    url = "https://www.azfamily.com" + href
                else:
                    url = href
                
                # Extract title
                title_elem = row.select_one("div.queryly_item_title")
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                
                # Extract description
                desc_elem = row.select_one("div.queryly_item_description")
                description = desc_elem.get_text(strip=True) if desc_elem else ""
                
                # Extract date
                date_elem = row.select_one("div[style*='margin-top:6px;color:#555;font-size:12px;']")
                if not date_elem:
                    continue
                date_text = date_elem.get_text(strip=True)
                
                # Check if article is recent
                if is_recent(date_text):
                    article = {
                        "source": "AZ Family",
                        "title": title,
                        "url": url,
                        "date": date_text,
                        "description": description,
                        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    articles.append(article)
                    print(f"✅ Added: {title} - {date_text}")
                else:
                    print(f"⏰ Skipped (old): {title} - {date_text}")
                    
            except Exception as e:
                print(f"❌ Error processing article: {e}")
                continue
        
        return articles
        
    except Exception as e:
        print(f"❌ Error extracting articles from page: {e}")
        return []

async def click_next_page(page):
    """Click the Next Page button"""
    try:
        # Look for the Next Page button
        next_button = await page.query_selector("a.next_btn")
        if next_button:
            print("🔄 Clicking Next Page button...")
            await next_button.click()
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)  # Wait for content to load
            return True
        else:
            print("❌ Next Page button not found")
            return False
    except Exception as e:
        print(f"❌ Error clicking Next Page: {e}")
        return False

async def scrape_azfamily_with_next_page():
    """Scrape AZ Family using Next Page button navigation"""
    all_articles = []
    page_count = 0
    max_pages = 10  # Limit to prevent infinite loops
    
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
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        page = await context.new_page()

        try:
            # Navigate to the search page
            print("🏠 Navigating to AZ Family search page...")
            await page.goto(AZFAMILY_URL, timeout=30000)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            # Extract articles from first page
            page_count += 1
            print(f"📄 Processing page {page_count}")
            articles = await extract_articles_from_page(page)
            all_articles.extend(articles)
            
            # Continue clicking Next Page until no more pages or limit reached
            while page_count < max_pages:
                if await click_next_page(page):
                    page_count += 1
                    print(f"📄 Processing page {page_count}")
                    articles = await extract_articles_from_page(page)
                    if not articles:
                        print("No more articles found, stopping...")
                        break
                    all_articles.extend(articles)
                else:
                    print("No more pages available")
                    break

        except Exception as e:
            print(f"❌ Error in main scraping: {e}")
        
        finally:
            await browser.close()

    # Remove duplicates based on URL
    unique_articles = []
    seen_urls = set()
    for article in all_articles:
        if article['url'] not in seen_urls:
            unique_articles.append(article)
            seen_urls.add(article['url'])

    # Save results
    output_file = 'azfamily_nextpage_articles.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unique_articles, f, indent=4, ensure_ascii=False)

    print(f"✅ Scraped {len(unique_articles)} unique articles from {page_count} pages. Saved to {output_file}")
    
    # Print summary
    print(f"\n📊 Summary:")
    for article in unique_articles:
        print(f"📰 {article['title']} - {article['date']}")
        print(f"   URL: {article['url']}")
        print(f"   Description: {article['description'][:100]}...")
        print()
    
    return unique_articles

async def main():
    """Main function"""
    await scrape_azfamily_with_next_page()

if __name__ == "__main__":
    asyncio.run(main()) 