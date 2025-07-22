import asyncio
import pandas as pd
from datetime import datetime
from dateutil import parser
from dateutil.tz import gettz
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# URLs for the three news sources
FOX_NEWS_URL = 'https://www.foxnews.com/search-results/search?q=fire'
ABC_NEWS_URL_BASE = 'https://abcnews.go.com/search?searchtext=fire&section=US&sort=date'
AZFAMILY_URL = 'https://www.azfamily.com/search/?query=fire'

def is_recent(date_string):
    try:
        date = parser.parse(date_string).date()
        return (datetime.today().date() - date).days <= 1
    except Exception:
        return False

async def get_fox_news_links(page):
    links = []
    page_number = 1
    
    while page_number <= 5:  # Limit crawling to 5 pages
        url = f"{FOX_NEWS_URL}&page={page_number}" if page_number > 1 else FOX_NEWS_URL
        print(f"🔍 Crawling Fox News: {url}")

        try:
            await page.goto(url, timeout=20000)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")

            # Fox News selectors
            articles = soup.select("article.article h2.title a, .search-result a")
            if not articles:
                print("✅ No more Fox News articles found.")
                break

            new_links = [a["href"] for a in articles if a.has_attr("href")]
            if not new_links:
                break

            links.extend(new_links)
            page_number += 1

        except PlaywrightTimeout:
            print(f"⚠️ Timeout on Fox News page {page_number}. Skipping.")
            page_number += 1
        except Exception as e:
            print(f"❌ Unexpected error on Fox News: {e}")
            page_number += 1

    return list(set(links))

async def get_abc_news_links(page):
    links = []
    page_number = 1
    
    while page_number <= 5:  # Limit crawling to 5 pages
        url = f"{ABC_NEWS_URL_BASE}&page={page_number}" if page_number > 1 else ABC_NEWS_URL_BASE
        print(f"🔍 Crawling ABC News: {url}")

        try:
            await page.goto(url, timeout=20000)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")

            # ABC News selectors
            articles = soup.select("section.ContentRoll__Item h2 a, .search-result a")
            if not articles:
                print("✅ No more ABC News articles found.")
                break

            new_links = [a["href"] for a in articles if a.has_attr("href")]
            if not new_links:
                break

            links.extend(new_links)
            page_number += 1

        except PlaywrightTimeout:
            print(f"⚠️ Timeout on ABC News page {page_number}. Skipping.")
            page_number += 1
        except Exception as e:
            print(f"❌ Unexpected error on ABC News: {e}")
            page_number += 1

    return list(set(links))

async def get_azfamily_links(page):
    links = []
    page_number = 1
    
    while page_number <= 5:  # Limit crawling to 5 pages
        url = f"{AZFAMILY_URL}&page={page_number}" if page_number > 1 else AZFAMILY_URL
        print(f"🔍 Crawling AZ Family: {url}")

        try:
            await page.goto(url, timeout=20000)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")

            # AZ Family selectors based on the HTML structure provided
            articles = soup.select("div.queryly_item_row a")
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
                break

            links.extend(new_links)
            page_number += 1

        except PlaywrightTimeout:
            print(f"⚠️ Timeout on AZ Family page {page_number}. Skipping.")
            page_number += 1
        except Exception as e:
            print(f"❌ Unexpected error on AZ Family: {e}")
            page_number += 1

    return list(set(links))

async def scrape_fox_news_article(page, url):
    try:
        await page.goto(url, timeout=20000)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Fox News selectors
        title_el = soup.select_one("h1.headline")
        date_el = soup.select_one("time, .time")
        content_el = soup.select_one("div.article-body")

        if not (title_el and content_el):
            print(f"⚠️ Missing title or content on Fox News: {url}")
            return None

        # Extract and clean the date
        date_string = date_el.text.strip() if date_el else ""
        try:
            parsed_date = parser.parse(date_string)
        except Exception as e:
            print(f"❌ Failed to parse date on Fox News {url}: {e}")
            return None

        if not is_recent(parsed_date.strftime("%Y-%m-%d")):
            return None

        # Extract content
        content = "\n".join(
            [
                p.get_text(strip=True)
                for p in content_el.find_all(["p", "div"], recursive=True)
                if p.text.strip()
            ]
        )

        return {
            "source": "Fox News",
            "title": title_el.text.strip(),
            "url": url,
            "date": parsed_date.strftime("%Y-%m-%d %H:%M:%S"),
            "content": content if content else "No content available"
        }

    except Exception as e:
        print(f"❌ Failed to scrape Fox News {url}: {e}")
        return None

async def scrape_abc_news_article(page, url):
    try:
        await page.goto(url, timeout=20000)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # ABC News selectors
        title_el = soup.select_one("h1")
        date_el = soup.select_one("time, .timestamp")
        content_el = soup.select_one("div.article-body, .article-content")

        if not (title_el and content_el):
            print(f"⚠️ Missing title or content on ABC News: {url}")
            return None

        # Extract and clean the date
        date_string = date_el.text.strip() if date_el else ""
        try:
            parsed_date = parser.parse(date_string)
        except Exception as e:
            print(f"❌ Failed to parse date on ABC News {url}: {e}")
            return None

        if not is_recent(parsed_date.strftime("%Y-%m-%d")):
            return None

        # Extract content
        content = "\n".join(
            [
                p.get_text(strip=True)
                for p in content_el.find_all(["p", "div"], recursive=True)
                if p.text.strip()
            ]
        )

        return {
            "source": "ABC News",
            "title": title_el.text.strip(),
            "url": url,
            "date": parsed_date.strftime("%Y-%m-%d %H:%M:%S"),
            "content": content if content else "No content available"
        }

    except Exception as e:
        print(f"❌ Failed to scrape ABC News {url}: {e}")
        return None

async def scrape_azfamily_article(page, url):
    try:
        await page.goto(url, timeout=20000)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # AZ Family selectors based on the HTML structure
        title_el = soup.select_one("h1, .article-title")
        date_el = soup.select_one("time, .date, .timestamp, .published-date")
        content_el = soup.select_one("div.article-body, .article-content, .content, .story-content")

        if not (title_el and content_el):
            print(f"⚠️ Missing title or content on AZ Family: {url}")
            return None

        # Extract and clean the date
        date_string = date_el.text.strip() if date_el else ""
        try:
            parsed_date = parser.parse(date_string)
        except Exception as e:
            print(f"❌ Failed to parse date on AZ Family {url}: {e}")
            return None

        if not is_recent(parsed_date.strftime("%Y-%m-%d")):
            return None

        # Extract content
        content = "\n".join(
            [
                p.get_text(strip=True)
                for p in content_el.find_all(["p", "div"], recursive=True)
                if p.text.strip()
            ]
        )

        return {
            "source": "AZ Family",
            "title": title_el.text.strip(),
            "url": url,
            "date": parsed_date.strftime("%Y-%m-%d %H:%M:%S"),
            "content": content if content else "No content available"
        }

    except Exception as e:
        print(f"❌ Failed to scrape AZ Family {url}: {e}")
        return None

async def main():
    all_articles = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Fox News
        print("🦊 Starting Fox News scraping...")
        fox_links = await get_fox_news_links(page)
        print(f"🔗 Found {len(fox_links)} Fox News article links.")

        for i, link in enumerate(fox_links, 1):
            print(f"📄 Scraping Fox News article {i}/{len(fox_links)}: {link}")
            article = await scrape_fox_news_article(page, link)
            if article:
                all_articles.append(article)

        # ABC News
        print("📺 Starting ABC News scraping...")
        abc_links = await get_abc_news_links(page)
        print(f"🔗 Found {len(abc_links)} ABC News article links.")

        for i, link in enumerate(abc_links, 1):
            print(f"📄 Scraping ABC News article {i}/{len(abc_links)}: {link}")
            article = await scrape_abc_news_article(page, link)
            if article:
                all_articles.append(article)

        # AZ Family
        print("🏠 Starting AZ Family scraping...")
        azfamily_links = await get_azfamily_links(page)
        print(f"🔗 Found {len(azfamily_links)} AZ Family article links.")

        for i, link in enumerate(azfamily_links, 1):
            print(f"📄 Scraping AZ Family article {i}/{len(azfamily_links)}: {link}")
            article = await scrape_azfamily_article(page, link)
            if article:
                all_articles.append(article)

        await browser.close()

    # Save to JSON file
    with open('mainstream_media_articles.json', 'w', encoding='utf-8') as f:
        json.dump(all_articles, f, indent=4, ensure_ascii=False)

    print(f"✅ Scraped {len(all_articles)} articles total. Saved to mainstream_media_articles.json")
    return all_articles

if __name__ == "__main__":
    asyncio.run(main()) 