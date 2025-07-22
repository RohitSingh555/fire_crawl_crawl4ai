#!/usr/bin/env python3
"""
Simplified Advanced Fire Scraper
"""

import asyncio
import aiohttp
import requests
import time
import random
import json
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional
import os
from pathlib import Path

# HTML parsing
from bs4 import BeautifulSoup
import lxml

# Anti-detection
import cloudscraper
from fake_useragent import UserAgent

# Content extraction
import trafilatura
from readability import Document

# Configuration
import yaml

# News websites to scrape
NEWS_WEBSITES = [
    "https://www.alachuacountytoday.com/",
    "https://bakercountypress.com/",
    "https://baycountycoastal.com/",
    "https://www.bradfordtoday.ca/",
    "https://brevardbusinessnews.com/",
    "https://calhounjournal.com/",
    "https://thecharlottegazette.com/",
    "https://www.theclaycountynews.com/",
    "https://www.columbiatribune.com/",
    "https://desotocountynews.com/",
    "https://duvaltimes.com/",
    "https://myescambia.com/news",
    "https://www.flaglernewsweekly.com/",
    "https://www.franklintownnews.com/",
    "https://gadsdencountytimes.com/",
    "https://gilchristcountyherald.com/",
    "https://www.hernandosun.com/",
    "https://holmescounty.news/",
    "https://www.jacksoncountytimes.news/",
    "https://www.dailyunion.com/",
    "https://www.lakecountypress.news/",
    "https://www.onlinemadison.com/",
    "https://marioncountynow.com/",
    "https://www.martincountymessenger.com/",
    "https://www.monroenews.com/",
    "https://www.nassaucountyrecord.com/",
    "https://okeechobeetimes.com/",
    "https://www.ocreporter.news/",
    "https://www.aroundosceola.com/",
    "https://www.palmbeachpost.com/",
    "https://www.pasconewsonline.com/",
    "https://pinellastimes.com/",
    "https://www.polkcountynews.net/",
    "https://www.putnamcountycourier.com/",
    "https://srpressgazette.com/",
    "https://www.theitem.com/",
    "https://www.suwanneetimes.com/",
    "https://www.unioncountynews.org/",
    "https://thewakullasun.com/",
    "https://www.waltontribune.com/",
    "https://adairvoice.com/",
    "https://www.andrewscountynews.com/",
    "https://bartonchronicle.com/",
    "https://www.bentonconews.com/",
    "https://www.boonecountyjournal.com/",
    "https://www.butlereagle.com/",
    "https://www.mycaldwellcounty.com/",
    "https://carrollspaper.com/",
    "https://cartercountytimes.com/",
    "https://www.beardstownnewspapers.com/",
    "https://www.hartington.net/",
    "https://www.charitonleader.com/",
    "https://christiancountynow.com/",
    "https://www.clarkcountytoday.com/",
    "https://clintoncountydailynews.com/",
    "https://crawfordcountynow.com/",
    "https://www.southdadenewsleader.com/",
    "https://www.douglascountysentinel.com/",
    "https://www.dddnews.com/",
    "https://fcfreepresspa.com/",
    "https://www.gasconadecountyrepublican.com/",
    "https://greenecountynewsonline.com/",
    "https://www.grundycountyherald.com/",
    "https://hickoryrecord.com/",
    "https://www.myholtcountynews.com/",
    "https://ironcountytoday.com/",
    "https://jcdailynews.com/",
    "https://johnsoncountypost.com/",
    "https://www.laclederecord.com/",
    "https://lewiscountytribune.com/",
    "https://lcnme.com/",
    "https://linncountynews.net/",
    "https://www.thelcn.com/",
    "https://mdcp.nwaonline.com/",
    "https://www.maconcountychronicle.com/",
    "https://mercercountyoutlook.net/",
    "https://www.themorgannews.com/",
    "https://newtoncountytimes.com/",
    "https://nodawaynews.com/",
    "https://www.osagecountyonline.com/",
    "https://www.ozarkcountytimes.com/",
    "https://www.pemiscotpress.com/",
    "https://www.perrytribune.com/",
    "https://www.sedaliademocrat.com/",
    "https://www.phelpscountyfocus.com/",
    "https://www.plattecountycitizen.com/",
    "https://www.polkio.com/",
    "https://monroecountyappeal.com/",
    "https://www.richmond-dailynews.com/",
    "https://www.stclaircourier.com/",
    "https://www.stfrancoisherald.com/",
    "https://www.stegenherald.com/",
    "https://www.schuylercountytimes.com/",
    "https://www.scottcountyrecord.com/",
    "https://www.shelbycountyreporter.com/",
    "https://www.stonecountyenterprise.com/",
    "https://www.scdemocratonline.com/",
    "https://warrencountypost.com/",
    "https://www.thewaynecountynews.com/",
    "https://www.webstercountycitizen.com/",
    "https://wrightcountyjournal.com/"
]

# Fire-related keywords
FIRE_KEYWORDS = [
    'fire', 'blaze', 'inferno', 'conflagration', 'arson', 'smoke', 'flame',
    'burning', 'firefighter', 'fire department', 'fire station', 'fire truck',
    'wildfire', 'forest fire', 'brush fire', 'house fire', 'building fire',
    'fire alarm', 'fire safety', 'fire prevention', 'fire investigation',
    'fire marshal', 'fire chief', 'fire engine', 'fire hydrant', 'fire escape',
    'fire drill', 'fire code', 'fire damage', 'fire restoration', 'fire insurance'
]

class SimpleFireScraper:
    """Simplified fire news scraper with anti-detection"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        self.scraped_urls = set()
        self.articles = []
        
        # Create output directory
        self.output_dir = Path('scraped_articles')
        self.output_dir.mkdir(exist_ok=True)
        
        print("🔥 Simple Fire Scraper initialized")

    def _is_fire_related(self, text: str) -> float:
        """Check if content is fire-related"""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        keyword_matches = sum(1 for keyword in FIRE_KEYWORDS if keyword in text_lower)
        return min(keyword_matches / len(FIRE_KEYWORDS), 1.0)

    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract publication date"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        date_selectors = [
            'time[datetime]',
            '.date',
            '.published',
            '.timestamp',
            '.article-date',
            'meta[property="article:published_time"]',
            'meta[name="publish_date"]'
        ]
        
        for selector in date_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    if element.name == 'meta':
                        date_str = element.get('content', '')
                    else:
                        date_str = element.get('datetime', '') or element.get_text()
                    
                    if date_str:
                        # Simple date parsing
                        for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%B %d, %Y', '%m/%d/%Y']:
                            try:
                                parsed = datetime.strptime(date_str.strip(), fmt)
                                return parsed.strftime('%Y-%m-%d')
                            except ValueError:
                                continue
            except Exception:
                continue
        
        return yesterday

    def _extract_content(self, html: str, url: str) -> Optional[Dict]:
        """Extract article content using multiple methods"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Method 1: Trafilatura
            try:
                extracted = trafilatura.extract(html, include_formatting=True)
                if extracted and len(extracted) > 100:
                    metadata = trafilatura.extract_metadata(html, url)
                    return {
                        'title': metadata.get('title', ''),
                        'content': extracted,
                        'date': self._extract_date(soup),
                        'fire_score': self._is_fire_related(extracted)
                    }
            except Exception:
                pass
            
            # Method 2: Readability
            try:
                doc = Document(html)
                content = doc.summary()
                if content:
                    soup_content = BeautifulSoup(content, 'lxml')
                    text_content = soup_content.get_text().strip()
                    if len(text_content) > 100:
                        return {
                            'title': doc.title(),
                            'content': text_content,
                            'date': self._extract_date(soup),
                            'fire_score': self._is_fire_related(text_content)
                        }
            except Exception:
                pass
            
            # Method 3: Manual extraction
            try:
                content_selectors = ['article', '.article-content', '.post-content', '.content', 'main']
                for selector in content_selectors:
                    content_element = soup.select_one(selector)
                    if content_element:
                        text_content = content_element.get_text().strip()
                        if len(text_content) > 100:
                            title_element = soup.select_one('h1, .title, .headline')
                            title = title_element.get_text().strip() if title_element else ""
                            
                            return {
                                'title': title,
                                'content': text_content,
                                'date': self._extract_date(soup),
                                'fire_score': self._is_fire_related(text_content)
                            }
            except Exception:
                pass
            
        except Exception as e:
            print(f"Content extraction failed for {url}: {e}")
        
        return None

    async def _scrape_url(self, url: str) -> Optional[Dict]:
        """Scrape a single URL"""
        if url in self.scraped_urls:
            return None
        
        self.scraped_urls.add(url)
        
        try:
            # Random delay
            await asyncio.sleep(random.uniform(1, 3))
            
            # Scrape with anti-detection
            response = self.scraper.get(url, timeout=30)
            
            if response.status_code == 200:
                content_data = self._extract_content(response.text, url)
                
                if content_data and content_data['fire_score'] >= 0.3:
                    return {
                        'url': url,
                        'title': content_data['title'],
                        'content': content_data['content'],
                        'published_date': content_data['date'],
                        'source': urlparse(url).netloc,
                        'fire_related_score': content_data['fire_score'],
                        'scraped_at': datetime.now().isoformat()
                    }
            
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")
        
        return None

    async def _find_article_urls(self, base_url: str) -> List[str]:
        """Find article URLs from a news website"""
        article_urls = []
        
        try:
            response = self.scraper.get(base_url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link['href']
                    full_url = urljoin(base_url, href)
                    
                    # Filter for article URLs
                    if self._is_article_url(full_url, base_url):
                        article_urls.append(full_url)
                
                # Remove duplicates and limit
                article_urls = list(set(article_urls))[:20]
                
        except Exception as e:
            print(f"Failed to find articles on {base_url}: {e}")
        
        return article_urls

    def _is_article_url(self, url: str, base_url: str) -> bool:
        """Check if URL is likely an article URL"""
        parsed = urlparse(url)
        base_parsed = urlparse(base_url)
        
        if parsed.netloc != base_parsed.netloc:
            return False
        
        article_patterns = [
            r'/article/', r'/news/', r'/story/', r'/post/', r'/entry/',
            r'/202[0-9]/', r'/20[0-9]{2}/', r'/\d{4}/\d{2}/', r'/\d{4}-\d{2}/'
        ]
        
        for pattern in article_patterns:
            if re.search(pattern, url):
                return True
        
        return False

    async def scrape_websites(self, websites: List[str]) -> List[Dict]:
        """Main scraping method"""
        print(f"🔥 Starting to scrape {len(websites)} websites...")
        
        for i, website in enumerate(websites, 1):
            try:
                print(f"📰 [{i}/{len(websites)}] Scraping: {website}")
                
                # Find article URLs
                article_urls = await self._find_article_urls(website)
                print(f"   Found {len(article_urls)} potential articles")
                
                # Scrape articles
                semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
                
                async def scrape_with_semaphore(url):
                    async with semaphore:
                        return await self._scrape_url(url)
                
                tasks = [scrape_with_semaphore(url) for url in article_urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Filter successful results
                website_articles = [r for r in results if r is not None and not isinstance(r, Exception)]
                self.articles.extend(website_articles)
                
                print(f"   ✅ Scraped {len(website_articles)} fire-related articles")
                
            except Exception as e:
                print(f"   ❌ Failed to scrape {website}: {e}")
                continue
        
        # Save results
        self._save_results()
        
        print(f"\n✅ Scraping completed! Total articles: {len(self.articles)}")
        return self.articles

    def _save_results(self):
        """Save scraped articles to file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save articles
            json_file = self.output_dir / f"fire_articles_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.articles, f, indent=2, ensure_ascii=False)
            
            # Save summary
            summary = {
                'total_articles': len(self.articles),
                'sources': list(set(article['source'] for article in self.articles)),
                'fire_scores': {
                    'min': min(article['fire_related_score'] for article in self.articles) if self.articles else 0,
                    'max': max(article['fire_related_score'] for article in self.articles) if self.articles else 0,
                    'avg': sum(article['fire_related_score'] for article in self.articles) / len(self.articles) if self.articles else 0
                }
            }
            
            summary_file = self.output_dir / f"scraping_summary_{timestamp}.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2)
            
            print(f"📁 Results saved to: {self.output_dir}")
            print(f"   📄 Articles: {json_file}")
            print(f"   📊 Summary: {summary_file}")
            
        except Exception as e:
            print(f"❌ Failed to save results: {e}")

async def main():
    """Main function"""
    print("🔥 Simple Fire News Scraper Starting...")
    
    scraper = SimpleFireScraper()
    
    try:
        articles = await scraper.scrape_websites(NEWS_WEBSITES)
        
        if articles:
            print("\n🔥 Top 5 articles by fire relevance score:")
            sorted_articles = sorted(articles, key=lambda x: x['fire_related_score'], reverse=True)
            for i, article in enumerate(sorted_articles[:5], 1):
                print(f"{i}. {article['title'][:80]}... (Score: {article['fire_related_score']:.2f})")
                print(f"   Source: {article['source']}")
                print(f"   URL: {article['url']}")
                print()
        
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n🏁 Scraper finished.")

if __name__ == "__main__":
    asyncio.run(main()) 