import asyncio
import json
import requests
from datetime import datetime, timedelta
from dateutil import parser
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

ABC_NEWS_URL = 'https://abcnews.go.com/search?searchtext=fire'

async def extract_articles_from_page(page):
    """Extract articles from the current ABC News search page"""
    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")
    today = datetime.now().date()
    articles = []
    
    # Debug: Check what we're finding
    content_roll_items = soup.select("section.ContentRoll__Item")
    print(f"     🔍 Found {len(content_roll_items)} ContentRoll__Item sections")
    
    # ABC News search results are in ContentRoll__Item sections
    for i, article in enumerate(content_roll_items):
        print(f"     📄 Processing article {i+1}...")
        
        # Look for the main link in the headline
        link = article.select_one("div.ContentRoll__Headline a")
        if not link or not link.has_attr("href"):
            print(f"       ❌ No link found")
            continue
            
        href = link["href"]
        print(f"       🔗 Link: {href}")
        
        # Skip video pages and other non-article content, but be less restrictive
        if any(skip in href.lower() for skip in ['/gallery/', '/slideshow/', '/interactive/', '/images/', '/shop/']):
            print(f"       ⏭️ Skipping gallery/slideshow/shop content")
            continue
            
        # For videos, we'll include them but mark them as video content
        is_video = '/video/' in href.lower()
        
        # Make sure we have a full URL
        if href.startswith('/'):
            url = "https://abcnews.go.com" + href
        elif href.startswith('http'):
            url = href
        else:
            print(f"       ❌ Invalid URL format")
            continue
            
        # Extract title from the headline
        title_el = article.select_one("div.ContentRoll__Headline h2")
        if not title_el:
            print(f"       ❌ No title found")
            continue
        title = title_el.get_text(strip=True)
        print(f"       📰 Title: {title[:50]}...")
        
        # Extract description/summary
        desc_el = article.select_one("div.ContentRoll__Desc")
        description = desc_el.get_text(strip=True) if desc_el else ""
        
        # Extract date from the timestamp
        date_el = article.select_one("div.ContentRoll__TimeStamp .TimeStamp__Date")
        date_text = ""
        if date_el:
            date_text = date_el.get_text(strip=True)
        
        print(f"       📅 Date: {date_text}")
        
        # Handle relative time formats like "14 hours ago", "2 hours ago"
        if date_text and any(relative in date_text.lower() for relative in ['ago', 'hours', 'minutes', 'days']):
            try:
                # For relative times, we'll include them as recent articles
                article_data = {
                    "title": title,
                    "url": url,
                    "date": date_text,
                    "description": description,
                    "date_parsed": False,
                    "is_recent": True,
                    "is_video": is_video
                }
                articles.append(article_data)
                print(f"       ✅ Added recent {'video' if is_video else 'article'}: {title[:50]}... ({date_text})")
                continue
            except:
                pass
        
        # Try to parse the date
        article_date = None
        if date_text:
            try:
                article_date = parser.parse(date_text).date()
            except:
                pass
        
        # If we can't parse the date, include the article anyway but mark it
        if not article_date:
            print(f"       ⚠️ Could not parse date '{date_text}' for article: {title[:50]}...")
            # Include articles without dates but limit to recent ones
            article_data = {
                "title": title,
                "url": url,
                "date": date_text,
                "description": description,
                "date_parsed": False,
                "is_video": is_video
            }
            articles.append(article_data)
            print(f"       ✅ Added {'video' if is_video else 'article'} with unknown date: {title[:50]}...")
        else:
            # Only include articles from the last 2 days
            days_diff = (today - article_date).days
            if days_diff <= 2:
                article_data = {
                    "title": title,
                    "url": url,
                    "date": date_text,
                    "description": description,
                    "date_parsed": True,
                    "is_video": is_video
                }
                articles.append(article_data)
                print(f"       ✅ Added recent {'video' if is_video else 'article'}: {title[:50]}... ({date_text})")
            else:
                print(f"       ⏭️ Skipping old {'video' if is_video else 'article'}: {title[:50]}... ({date_text})")
    
    return articles

async def extract_full_article(page, url):
    """Extract full article or video content from ABC News article page"""
    try:
        await page.goto(url, timeout=60000)
        await page.wait_for_selector("h1, .article-title, .headline, .story-title, h2.video-info-module__text--title", timeout=30000)
        await asyncio.sleep(2)
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Try to extract video info from ld+json
        video_json = None
        for script in soup.find_all("script", {"type": "application/ld+json"}):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get("@type") == "VideoObject":
                    video_json = data
                    break
            except Exception:
                continue

        if video_json:
            title = video_json.get("name", "")
            description = video_json.get("description", "")
            date = video_json.get("uploadDate", "")
            video_url = video_json.get("contentUrl") or video_json.get("url")
            thumbnail = video_json.get("thumbnailUrl", "")
            return {
                "title": title,
                "date": date,
                "url": url,
                "description": description,
                "video_url": video_url,
                "thumbnail": thumbnail,
                "type": "video"
            }

        # Fallback: extract as text article
        title = soup.select_one("h1, .article-title, .headline, .story-title")
        date_el = soup.select_one("time, .date, .timestamp, .published-date, .article-date, .story-date")
        content_selectors = [
            ".article-body", ".story-body", ".content", ".article-content",
            ".story-content", ".article-text", ".story-text", ".body-content"
        ]
        content_el = None
        for selector in content_selectors:
            content_el = soup.select_one(selector)
            if content_el:
                break
        if not content_el:
            content_el = soup.select_one("article, .article, .story")
        paragraphs = []
        if content_el:
            paragraphs = content_el.find_all("p")
        content = "\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        return {
            "title": title.get_text(strip=True) if title else "",
            "date": date_el.get_text(strip=True) if date_el else "",
            "url": url,
            "content": content,
            "type": "article"
        }
    except Exception as e:
        print(f"❌ Failed to scrape {url}: {e}")
        return None

async def crawl_abc_news_until_yesterday():
    """Crawl ABC News search results for fire-related articles"""
    all_articles = []
    seen_urls = set()
    page_count = 0
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto(ABC_NEWS_URL, timeout=60000)
        
        # Wait for search results to load
        try:
            await page.wait_for_selector("section.ContentRoll__Item", timeout=60000)
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
            
            # Check if we should continue to next page
            today = datetime.now().date()
            old_articles = 0
            for a in articles:
                # Include articles marked as recent (relative time stamps)
                if a.get('is_recent', False):
                    continue
                    
                if a.get('date_parsed', False):
                    try:
                        article_date = parser.parse(a['date']).date()
                        if (today - article_date).days >= 2:
                            old_articles += 1
                    except:
                        pass
            
            if old_articles == len(articles) and len(articles) > 0:
                print("   All articles on this page are older than 2 days, stopping...")
                break
            
            # Try to click next page
            try:
                # Look for next page button - ABC News uses pagination__link--enabled
                next_btn = await page.query_selector("a.pagination__link--enabled")
                
                if next_btn:
                    print("   Clicking next page...")
                    await next_btn.click()
                    await asyncio.sleep(3)
                    
                    try:
                        await page.wait_for_selector("section.ContentRoll__Item", timeout=30000)
                    except:
                        print("   No new articles loaded after clicking next, stopping...")
                        break
                else:
                    print("   No next page button found, stopping...")
                    break
            except Exception as e:
                print(f"❌ Error clicking next page: {e}")
                break
            
            await asyncio.sleep(1)
        
        await browser.close()
    return all_articles

async def main():
    print("🔍 Crawling ABC News for fire-related articles...")
    articles = await crawl_abc_news_until_yesterday()
    print(f"Found {len(articles)} articles. Now scraping full content...")
    
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
    
    with open('abcnews_fire_articles.json', 'w', encoding='utf-8') as f:
        json.dump(full_articles, f, indent=4, ensure_ascii=False)
    
    print(f"✅ Saved {len(full_articles)} full articles to abcnews_fire_articles.json")
    
    for a in full_articles:
        print(f"📰 {a['title']} - {a['date']}")
        print(f"   URL: {a['url']}")
        print(f"   Content: {a['content'][:100]}...")
        print()

async def test_crawler():
    """Test function to verify the crawler works properly"""
    print("🧪 Testing ABC News crawler...")
    articles = await crawl_abc_news_until_yesterday()
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
