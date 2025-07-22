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
        # Handle different date formats
        if "Jun" in date_string:
            # Convert "Jun 23, 2025" to "2025-06-23"
            date_obj = parser.parse(date_string)
            date_str = date_obj.strftime("%Y-%m-%d")
        else:
            date_str = date_string
            
        today = datetime.today().date()
        article_date = parser.parse(date_str).date()
        return (today - article_date).days <= 1
    except Exception as e:
        print(f"Date parsing error: {e}")
        return False

async def get_azfamily_links(page):
    """Extract article links from AZ Family search results"""
    links = []
    page_number = 1
    
    while page_number <= 3:  # Limit to 3 pages
        url = f"{AZFAMILY_URL}&page={page_number}" if page_number > 1 else AZFAMILY_URL
        print(f"🔍 Crawling AZ Family page {page_number}: {url}")

        try:
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)

            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")

            # Extract articles using the correct selector from the HTML
            articles = soup.select("div.queryly_item_row a")
            print(f"Found {len(articles)} potential articles on page {page_number}")
            
            if not articles:
                print("✅ No more AZ Family articles found.")
                break

            new_links = []
            for a in articles:
                if a.has_attr("href"):
                    href = a["href"]
                    # Skip non-article links
                    if href.startswith("/page/") or href.startswith("/video/"):
                        continue
                    # Make relative URLs absolute
                    if href.startswith("/"):
                        full_url = "https://www.azfamily.com" + href
                    else:
                        full_url = href
                    new_links.append(full_url)

            if not new_links:
                print("No valid article links found on this page")
                break

            links.extend(new_links)
            print(f"Added {len(new_links)} links from page {page_number}")
            page_number += 1

        except PlaywrightTimeout:
            print(f"⚠️ Timeout on AZ Family page {page_number}. Skipping.")
            page_number += 1
        except Exception as e:
            print(f"❌ Unexpected error on AZ Family page {page_number}: {e}")
            page_number += 1

    return list(set(links))

async def scrape_azfamily_article(page, url):
    """Scrape individual AZ Family article"""
    try:
        print(f"📄 Scraping: {url}")
        await page.goto(url, timeout=30000)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title_el = soup.select_one("h1, .article-title, .headline")
        if not title_el:
            print(f"⚠️ No title found for: {url}")
            return None
        
        title = title_el.text.strip()

        # Extract date - try multiple selectors
        date_el = soup.select_one("time, .date, .timestamp, .published-date, .article-date")
        date_string = ""
        if date_el:
            date_string = date_el.text.strip()
        else:
            # Try to find date in meta tags
            meta_date = soup.select_one('meta[property="article:published_time"]')
            if meta_date:
                date_string = meta_date.get('content', '')

        # Extract content
        content_el = soup.select_one("div.article-body, .article-content, .content, .story-content, .article-text")
        if not content_el:
            print(f"⚠️ No content found for: {url}")
            return None

        # Extract paragraphs
        paragraphs = content_el.find_all("p")
        content = "\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        if not content:
            print(f"⚠️ No content text found for: {url}")
            return None

        # Check if article is recent
        if date_string and not is_recent(date_string):
            print(f"⚠️ Article not recent (date: {date_string}): {url}")
            return None

        return {
            "source": "AZ Family",
            "title": title,
            "url": url,
            "date": date_string if date_string else "Date not available",
            "content": content,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        print(f"❌ Failed to scrape {url}: {e}")
        return None

async def main():
    """Main function to scrape AZ Family news"""
    all_articles = []

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
            # Get all article links
            print("🏠 Starting AZ Family scraping...")
            links = await get_azfamily_links(page)
            print(f"🔗 Found {len(links)} AZ Family article links.")

            # Scrape each article
            for i, link in enumerate(links, 1):
                print(f"📄 Scraping article {i}/{len(links)}")
                article = await scrape_azfamily_article(page, link)
                if article:
                    all_articles.append(article)
                    print(f"✅ Successfully scraped: {article['title']}")

        except Exception as e:
            print(f"❌ Error in main scraping: {e}")
        
        finally:
            await browser.close()

    # Save results
    output_file = 'azfamily_articles.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_articles, f, indent=4, ensure_ascii=False)

    print(f"✅ Scraped {len(all_articles)} articles total. Saved to {output_file}")
    
    # Print summary
    for article in all_articles:
        print(f"📰 {article['title']} - {article['date']}")
    
    return all_articles

if __name__ == "__main__":
    asyncio.run(main()) 