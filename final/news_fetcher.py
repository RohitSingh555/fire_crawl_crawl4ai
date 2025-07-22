import asyncio
import json
import os
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, TimeoutError
import logging
from typing import Dict, List, Optional, Tuple
import re
from urllib.parse import urlparse
import random
import time
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('news_fetcher.log'),
        logging.StreamHandler()
    ]
)

class NewsFetcher:
    def __init__(self):
        self.search_engines = {
            "Google News": {
                "url": "https://news.google.com/search?q={query}&hl=en-US&gl=US&ceid=US:en",
                "article_selector": "article",
                "link_selector": "a[href*='/articles/']",
                "date_selector": "time",
                "pagination_selector": "a[aria-label='Next page']"
            },
            "Bing News": {
                "url": "https://www.bing.com/news/search?q={query}&FORM=HDRSC6",
                "article_selector": ".news-card",
                "link_selector": "a.title",
                "date_selector": ".news-card-time",
                "pagination_selector": "a.sb_pagN"
            },
            "Yahoo News": {
                "url": "https://news.search.yahoo.com/search?p={query}&fr=news",
                "article_selector": ".NewsArticle",
                "link_selector": "h3.title a",
                "date_selector": ".time",
                "pagination_selector": "a.next"
            }
        }
        
        self.fire_keywords = [
            'fire', 'wildfire', 'blaze', 'flame', 'burn', 'inferno', 'smoke', 
            'firefighters', 'firemen', 'combustion', 'embers', 'spark', 'arson',
            'explosion', 'firestorm', 'fire escape', 'firetruck', 'fire hose',
            'fire alarm', 'fire extinguishers', 'fire drill', 'flamethrower',
            'fireplace', 'flashover', 'fire resistance', 'fire retardant'
        ]
        
        self.yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        self.today = datetime.now().strftime('%Y-%m-%d')
        
        # Create output directory if it doesn't exist
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
    async def init_browser(self):
        """Initialize browser with stealth settings"""
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
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
            return playwright, browser, context
        except Exception as e:
            logging.error(f"Failed to initialize browser: {str(e)}")
            raise

    async def extract_article_data(self, page, url: str) -> Optional[Dict]:
        """Extract detailed article data using Playwright"""
        try:
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_load_state('domcontentloaded')
            
            # Wait for content to load
            await asyncio.sleep(random.uniform(2, 4))
            
            # Extract title
            title = await page.evaluate('''() => {
                const h1 = document.querySelector('h1');
                return h1 ? h1.textContent.trim() : '';
            }''')
            
            # Extract content
            content = await page.evaluate('''() => {
                const paragraphs = Array.from(document.querySelectorAll('p'));
                return paragraphs.map(p => p.textContent.trim()).join(' ');
            }''')
            
            # Extract date
            date = await page.evaluate('''() => {
                const dateSelectors = [
                    'time[datetime]',
                    'meta[property="article:published_time"]',
                    '.date',
                    '.timestamp',
                    '.published-date'
                ];
                
                for (const selector of dateSelectors) {
                    const element = document.querySelector(selector);
                    if (element) {
                        return element.getAttribute('datetime') || element.textContent.trim();
                    }
                }
                return '';
            }''')
            
            # Extract author
            author = await page.evaluate('''() => {
                const authorSelectors = [
                    '.author',
                    '.byline',
                    'meta[name="author"]',
                    '[rel="author"]'
                ];
                
                for (const selector of authorSelectors) {
                    const element = document.querySelector(selector);
                    if (element) {
                        return element.textContent.trim();
                    }
                }
                return '';
            }''')
            
            return {
                'url': url,
                'title': title,
                'content': content,
                'date': date,
                'author': author,
                'source': urlparse(url).netloc
            }
            
        except Exception as e:
            logging.error(f"Error extracting article data from {url}: {str(e)}")
            return None

    def is_fire_related(self, content: str) -> bool:
        """Check if content is fire-related"""
        if not content:
            return False
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in self.fire_keywords)

    def is_recent_article(self, date_str: str) -> bool:
        """Check if article is from yesterday"""
        if not date_str:
            return False
            
        try:
            # Try different date formats
            date_formats = [
                '%Y-%m-%d',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%B %d, %Y',
                '%b %d, %Y',
                '%d %B %Y',
                '%d %b %Y'
            ]
            
            for fmt in date_formats:
                try:
                    article_date = datetime.strptime(date_str.split('T')[0], fmt)
                    return article_date.strftime('%Y-%m-%d') in [self.yesterday, self.today]
                except ValueError:
                    continue
                    
            return False
        except Exception:
            return False

    async def fetch_news_articles(self, query: str = "fire news", max_pages: int = 3) -> List[Dict]:
        """Main method to fetch and verify news articles"""
        playwright = None
        browser = None
        context = None
        all_articles = []
        
        try:
            playwright, browser, context = await self.init_browser()
            
            for engine_name, engine_data in self.search_engines.items():
                logging.info(f"Searching {engine_name}...")
                page = await context.new_page()
                
                for page_num in range(max_pages):
                    try:
                        search_url = engine_data['url'].format(query=query)
                        if page_num > 0:
                            search_url += f"&page={page_num + 1}"
                            
                        await page.goto(search_url, wait_until='networkidle', timeout=30000)
                        await page.wait_for_selector(engine_data['article_selector'], timeout=10000)
                        
                        # Extract article links
                        links = await page.evaluate(f'''() => {{
                            const links = Array.from(document.querySelectorAll('{engine_data["link_selector"]}'));
                            return links.map(link => link.href);
                        }}''')
                        
                        # Process each article
                        for link in links:
                            try:
                                article_data = await self.extract_article_data(page, link)
                                
                                if article_data and self.is_fire_related(article_data['content']):
                                    if self.is_recent_article(article_data['date']):
                                        all_articles.append(article_data)
                                        logging.info(f"Found relevant article: {article_data['title']}")
                                        
                            except Exception as e:
                                logging.error(f"Error processing article {link}: {str(e)}")
                                continue
                                
                    except Exception as e:
                        logging.error(f"Error processing page {page_num + 1} of {engine_name}: {str(e)}")
                        continue
                        
                await page.close()
                
        except Exception as e:
            logging.error(f"Error in fetch_news_articles: {str(e)}")
            
        finally:
            if context:
                await context.close()
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()
            
        return all_articles

    def save_articles(self, articles: List[Dict], filename: str = 'fire_news_articles.json'):
        """Save articles to JSON file"""
        try:
            output_path = self.output_dir / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=4, ensure_ascii=False)
            logging.info(f"Saved {len(articles)} articles to {output_path}")
        except Exception as e:
            logging.error(f"Error saving articles: {str(e)}")

async def main():
    try:
        fetcher = NewsFetcher()
        articles = await fetcher.fetch_news_articles()
        fetcher.save_articles(articles)
    except Exception as e:
        logging.error(f"Main execution error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 