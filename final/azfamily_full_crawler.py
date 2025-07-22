import asyncio
import json
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

AZFAMILY_URL = 'https://www.azfamily.com/search/?query=fire'

async def extract_articles_from_page(page):
    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")
    today = datetime.now().date()
    articles = []
    
    for row in soup.select("div.queryly_item_row"):
        link = row.select_one("a")
        if not link or not link.has_attr("href"):
            continue
            
        href = link["href"]
        # Skip video pages and pagination pages
        if href.startswith("/video/") or href.startswith("/page/"):
            continue
            
        url = "https://www.azfamily.com" + href if href.startswith("/") else href
        title = row.select_one("div.queryly_item_title")
        desc = row.select_one("div.queryly_item_description")
        
        # Look for date in multiple possible locations
        date_div = row.select_one("div[style*='margin-top:6px;color:#555;font-size:12px;']")
        if not date_div:
            # Try alternative date selectors
            date_div = row.select_one("div[style*='color:#555']") or row.select_one("div[style*='font-size:12px']")
        
        if not (title and date_div):
            continue
            
        date_text = date_div.get_text(strip=True)
        if not date_text:
            continue
            
        try:
            # Try to parse the date - handle various formats
            article_date = parser.parse(date_text).date()
        except Exception as e:
            print(f"   ⚠️ Could not parse date '{date_text}': {e}")
            continue
            
        # Only include articles from today or yesterday
        days_diff = (today - article_date).days
        if days_diff <= 2:  # Changed from 1 to 2 days to be more inclusive
            article_data = {
                "title": title.get_text(strip=True),
                "url": url,
                "date": date_text,
                "description": desc.get_text(strip=True) if desc else ""
            }
            articles.append(article_data)
            print(f"     📰 Found: {article_data['title'][:50]}... ({date_text})")
    
    return articles

async def extract_full_article(page, url):
    try:
        await page.goto(url, timeout=60000)
        await page.wait_for_selector("h1, .article-title, .headline", timeout=30000)
        await asyncio.sleep(2)
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        title = soup.select_one("h1, .article-title, .headline")
        date_el = soup.select_one("time, .date, .timestamp, .published-date, .article-date")
        content_el = soup.select_one("div.article-body, .article-content, .content, .story-content, .article-text")
        paragraphs = content_el.find_all("p") if content_el else []
        content = "\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        return {
            "title": title.get_text(strip=True) if title else "",
            "date": date_el.get_text(strip=True) if date_el else "",
            "url": url,
            "content": content,
        }
    except Exception as e:
        print(f"❌ Failed to scrape {url}: {e}")
        return None

async def crawl_azfamily_until_yesterday():
    all_articles = []
    seen_urls = set()
    page_count = 0
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(AZFAMILY_URL, timeout=60000)
        # Wait for the first batch of articles to appear
        try:
            await page.wait_for_selector("div.queryly_item_row", timeout=60000)
        except Exception as e:
            print(f"❌ Initial articles did not load: {e}")
            await browser.close()
            return []
        await asyncio.sleep(2)
        keep_going = True
        while keep_going:
            page_count += 1
            print(f"📄 Processing page {page_count}...")
            
            articles = await extract_articles_from_page(page)
            print(f"   Found {len(articles)} articles on this page")
            
            new_articles = 0
            for art in articles:
                if art['url'] not in seen_urls:
                    all_articles.append(art)
                    seen_urls.add(art['url'])
                    new_articles += 1
            
            print(f"   Added {new_articles} new articles (total: {len(all_articles)})")
            
            if not articles:
                print("   No articles found on this page, stopping...")
                break
                
            today = datetime.now().date()
            # Check if all articles on this page are older than 2 days (more inclusive)
            old_articles = 0
            for a in articles:
                try:
                    article_date = parser.parse(a['date']).date()
                    if (today - article_date).days >= 2:  # Changed from 1 to 2 days
                        old_articles += 1
                except:
                    pass
            
            if old_articles == len(articles) and len(articles) > 0:
                print("   All articles on this page are older than 2 days, stopping...")
                break
                
            # Try to click next page
            try:
                # Look for the next page button with multiple selectors
                next_btn = await page.query_selector("a.next_btn, .next_btn, a[onclick*='turnpage']")
                if next_btn:
                    print("   Clicking next page...")
                    await next_btn.click()
                    # Wait for new articles to load
                    await asyncio.sleep(3)  # Give more time for content to load
                    
                    # Wait for either new articles or confirmation that we're on a new page
                    try:
                        await page.wait_for_selector("div.queryly_item_row", timeout=30000)
                    except:
                        print("   No new articles loaded after clicking next, stopping...")
                        break
                        
                else:
                    print("   No next page button found, stopping...")
                    break
            except Exception as e:
                print(f"❌ Error clicking next page: {e}")
                break
                
            # Add a small delay between pages to be respectful
            await asyncio.sleep(1)
            
        await browser.close()
    return all_articles

async def main():
    print("🔍 Crawling AZ Family for all yesterday's articles...")
    articles = await crawl_azfamily_until_yesterday()
    print(f"Found {len(articles)} articles from yesterday or today. Now scraping full content...")
    # Now open each link and get full info
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        full_articles = []
        for i, art in enumerate(articles, 1):
            print(f"[{i}/{len(articles)}] {art['url']}")
            full_info = await extract_full_article(page, art['url'])
            if full_info:
                full_info['description'] = art.get('description', '')
                full_articles.append(full_info)
        await browser.close()
    with open('azfamily_yesterday_full_articles.json', 'w', encoding='utf-8') as f:
        json.dump(full_articles, f, indent=4, ensure_ascii=False)
    print(f"✅ Saved {len(full_articles)} full articles to azfamily_yesterday_full_articles.json")
    for a in full_articles:
        print(f"📰 {a['title']} - {a['date']}")
        print(f"   URL: {a['url']}")
        print(f"   Content: {a['content'][:100]}...")
        print()

async def test_crawler():
    """Test function to verify the crawler works properly"""
    print("🧪 Testing AZ Family crawler...")
    articles = await crawl_azfamily_until_yesterday()
    print(f"✅ Test completed! Found {len(articles)} articles")
    if articles:
        print("Sample articles:")
        for i, art in enumerate(articles[:3], 1):
            print(f"  {i}. {art['title']}")
            print(f"     Date: {art['date']}")
            print(f"     URL: {art['url']}")
            print()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(test_crawler())
    else:
        asyncio.run(main()) 