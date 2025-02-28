import asyncio
import random
import json
import time
import requests
from playwright.async_api import async_playwright
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

# ✅ Search engines with JavaScript selectors
SEARCH_ENGINES = {
    "Google": {
        "url": "https://www.google.com/search?q={query}&tbm=nws",
        "selector": "a",
        "pagination": "a[aria-label='Next'], a[title='Next page']"
    },
    "Bing": {
        "url": "https://www.bing.com/news/search?q={query}",
        "selector": "a.title"
    },
    "Yahoo": {
        "url": "https://news.search.yahoo.com/search?p={query}",
        "selector": "a",
        "pagination": "a.next"
    },
    "DuckDuckGo": {
        "url": "https://duckduckgo.com/?q={query}&ia=news&iar=news",
        "selector": "article a"
    }
}

# ✅ Random User-Agent
ua = UserAgent()

async def fetch_news_urls(query, max_pages=5):
    """Scrape news article links from search engines with full JavaScript execution."""
    all_links = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(user_agent=ua.random)
        page = await context.new_page()

        for engine, data in SEARCH_ENGINES.items():
            search_url = data["url"].format(query=query.replace(" ", "+"))
            selector = data["selector"]
            pagination_selector = data.get("pagination", None)
            print(f"[🔍] Searching {engine}: {search_url}")

            try:
                await page.goto(search_url, timeout=30000)
                await asyncio.sleep(random.uniform(3, 6))  # Anti-detection delay

                all_links[engine] = []  # Initialize the list of links for this engine

                for _ in range(max_pages):
                    await page.wait_for_selector(selector, timeout=10000)  # Wait for news links

                    # Extract news article URLs
                    links = await page.eval_on_selector_all(selector, "elements => elements.map(e => e.href)")

                    # Google-specific cleanup
                    if engine == "Google":
                        links = [l.split("/url?q=")[1].split("&")[0] for l in links if "/url?q=" in l]

                    links = [l for l in links if l.startswith("http")]
                    all_links[engine].extend(links)
                    print(f"[✅] Found {len(links)} news articles on {engine}")

                    # Pagination handling (Google/Yahoo)
                    if pagination_selector:
                        next_button = await page.query_selector(pagination_selector)
                        if next_button:
                            await next_button.click()
                            await page.wait_for_load_state("networkidle")
                        else:
                            break
                    else:
                        break  # If no pagination, stop

            except Exception as e:
                print(f"[❌] Error scraping {engine}: {e}")

        await browser.close()

    return all_links

def fetch_news_content(news_urls):
    """Extracts full news articles from URLs."""
    news_data = []

    for source, urls in news_urls.items():
        for url in urls:
            try:
                print(f"[📰] Scraping news article: {url}")
                headers = {"User-Agent": ua.random}
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, "html.parser")

                title = soup.title.string if soup.title else "No Title"
                paragraphs = [p.get_text() for p in soup.find_all("p")]
                article_text = " ".join(paragraphs[:10])  # Limit to first 10 paragraphs

                news_data.append({"source": source, "url": url, "title": title, "content": article_text})

            except Exception as e:
                print(f"[❌] Failed to scrape: {url}, Error: {e}")

    return news_data

async def main():
    query = "fire news in USA"
    news_urls = await fetch_news_urls(query)

    print(f"[✅] Total {sum(len(urls) for urls in news_urls.values())} news article links found!")

    # Save raw URLs in the desired format
    with open("news_links.json", "w") as f:
        json.dump(news_urls, f, indent=4)

    # Scrape news content
    news_data = fetch_news_content(news_urls)

    # Save full news articles
    with open("full_news_data.json", "w") as f:
        json.dump(news_data, f, indent=4)

    print(f"[✅] Full news articles saved!")

if __name__ == "__main__":
    asyncio.run(main())
