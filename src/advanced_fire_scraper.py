#!/usr/bin/env python3
"""
Advanced Fire News Scraper
A highly sophisticated web scraping system with anti-detection capabilities
"""

import asyncio
import aiohttp
import requests
import time
import random
import json
import re
import logging
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional, Set
import hashlib
import os
import sys
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue
import pickle
import gzip
from pathlib import Path

# Advanced scraping libraries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# BeautifulSoup for HTML parsing
from bs4 import BeautifulSoup
import lxml

# Advanced HTTP libraries
import cloudscraper
from fake_useragent import UserAgent
import undetected_chromedriver as uc

# Proxy and networking
import aiohttp_socks
from aiohttp_socks import ProxyConnector
import socks
import socket

# Data processing
import pandas as pd
from newspaper import Article, Config
import trafilatura
from readability import Document

# Machine learning for content classification
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib

# Configuration and environment
from dotenv import load_dotenv
import yaml

# Advanced logging
import structlog
from structlog import get_logger

# Load environment variables
load_dotenv()

# Configure advanced logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = get_logger()

@dataclass
class ArticleData:
    """Data structure for scraped articles"""
    url: str
    title: str
    content: str
    published_date: str
    source: str
    author: str = ""
    summary: str = ""
    keywords: List[str] = None
    fire_related_score: float = 0.0
    scraped_at: str = ""
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if not self.scraped_at:
            self.scraped_at = datetime.now().isoformat()

class AdvancedFireScraper:
    """Advanced web scraper with anti-detection capabilities"""
    
    def __init__(self, config_path: str = "scraper_config.yaml"):
        self.config = self._load_config(config_path)
        self.session = None
        self.driver = None
        self.ua = UserAgent()
        self.proxy_list = self._load_proxies()
        self.current_proxy = None
        self.scraped_urls = set()
        self.article_queue = Queue()
        self.results = []
        self.lock = threading.Lock()
        
        # Fire-related keywords for content filtering
        self.fire_keywords = [
            'fire', 'blaze', 'inferno', 'conflagration', 'arson', 'smoke', 'flame',
            'burning', 'firefighter', 'fire department', 'fire station', 'fire truck',
            'wildfire', 'forest fire', 'brush fire', 'house fire', 'building fire',
            'fire alarm', 'fire safety', 'fire prevention', 'fire investigation',
            'fire marshal', 'fire chief', 'fire engine', 'fire hydrant', 'fire escape',
            'fire drill', 'fire code', 'fire damage', 'fire restoration', 'fire insurance'
        ]
        
        # Initialize ML model for fire content classification
        self.ml_model = self._load_ml_model()
        
        logger.info("Advanced Fire Scraper initialized", 
                   config_loaded=True, 
                   proxy_count=len(self.proxy_list),
                   fire_keywords_count=len(self.fire_keywords))

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        default_config = {
            'scraping': {
                'max_concurrent_requests': 10,
                'request_delay': (1, 3),
                'timeout': 30,
                'max_retries': 3,
                'user_agent_rotation': True,
                'proxy_rotation': True,
                'headless_browser': True,
                'browser_timeout': 60
            },
            'content': {
                'min_content_length': 100,
                'fire_related_threshold': 0.3,
                'extract_images': False,
                'extract_links': True
            },
            'storage': {
                'output_dir': 'scraped_articles',
                'backup_enabled': True,
                'compression_enabled': True
            }
        }
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return {**default_config, **config}
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return default_config

    def _load_proxies(self) -> List[str]:
        """Load proxy list from various sources"""
        proxies = []
        
        # Free proxy sources (in production, use paid proxies)
        proxy_sources = [
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
            "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt"
        ]
        
        for source in proxy_sources:
            try:
                response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    proxy_list = response.text.strip().split('\n')
                    proxies.extend([f"http://{proxy}" for proxy in proxy_list if proxy])
            except Exception as e:
                logger.warning(f"Failed to load proxies from {source}: {e}")
        
        # Add some known working proxies (replace with your paid proxies)
        additional_proxies = [
            # Add your proxy list here
        ]
        proxies.extend(additional_proxies)
        
        return list(set(proxies))  # Remove duplicates

    def _load_ml_model(self):
        """Load or create ML model for fire content classification"""
        model_path = "fire_classifier_model.pkl"
        
        try:
            if os.path.exists(model_path):
                return joblib.load(model_path)
            else:
                # Create a simple model for fire content classification
                vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
                classifier = MultinomialNB()
                
                # Simple training data (in production, use more comprehensive dataset)
                fire_texts = [
                    "fire broke out in the building", "firefighters responded to the scene",
                    "wildfire spread across the forest", "fire department arrived quickly",
                    "fire caused extensive damage", "fire investigation continues"
                ]
                non_fire_texts = [
                    "weather forecast for today", "local sports team wins championship",
                    "new restaurant opens downtown", "traffic accident on highway",
                    "school board meeting scheduled", "community event this weekend"
                ]
                
                X = fire_texts + non_fire_texts
                y = [1] * len(fire_texts) + [0] * len(non_fire_texts)
                
                X_transformed = vectorizer.fit_transform(X)
                classifier.fit(X_transformed, y)
                
                # Save model
                joblib.dump((vectorizer, classifier), model_path)
                return (vectorizer, classifier)
                
        except Exception as e:
            logger.error(f"Failed to load/create ML model: {e}")
            return None

    async def _create_session(self) -> aiohttp.ClientSession:
        """Create aiohttp session with advanced configuration"""
        if self.current_proxy:
            connector = ProxyConnector.from_url(self.current_proxy)
        else:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30
            )
        
        timeout = aiohttp.ClientTimeout(total=self.config['scraping']['timeout'])
        
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        }
        
        return aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers,
            cookie_jar=aiohttp.CookieJar()
        )

    def _setup_browser(self):
        """Setup undetected Chrome browser"""
        try:
            options = uc.ChromeOptions()
            
            if self.config['scraping']['headless_browser']:
                options.add_argument('--headless')
            
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-web-security')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Random window size
            width = random.randint(1200, 1920)
            height = random.randint(800, 1080)
            options.add_argument(f'--window-size={width},{height}')
            
            # Add random user agent
            options.add_argument(f'--user-agent={self.ua.random}')
            
            # Proxy configuration
            if self.current_proxy:
                options.add_argument(f'--proxy-server={self.current_proxy}')
            
            self.driver = uc.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Browser setup completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup browser: {e}")
            raise

    def _rotate_proxy(self):
        """Rotate to next available proxy"""
        if not self.proxy_list:
            return
        
        if self.current_proxy in self.proxy_list:
            self.proxy_list.remove(self.current_proxy)
        
        if self.proxy_list:
            self.current_proxy = random.choice(self.proxy_list)
            logger.info(f"Rotated to proxy: {self.current_proxy}")
        else:
            self.current_proxy = None
            logger.warning("No more proxies available")

    def _is_fire_related(self, text: str) -> float:
        """Determine if content is fire-related using ML and keyword matching"""
        if not text:
            return 0.0
        
        # Keyword-based scoring
        text_lower = text.lower()
        keyword_matches = sum(1 for keyword in self.fire_keywords if keyword in text_lower)
        keyword_score = keyword_matches / len(self.fire_keywords)
        
        # ML-based scoring
        ml_score = 0.0
        if self.ml_model:
            try:
                vectorizer, classifier = self.ml_model
                X_transformed = vectorizer.transform([text])
                ml_score = classifier.predict_proba(X_transformed)[0][1]
            except Exception as e:
                logger.warning(f"ML prediction failed: {e}")
        
        # Combine scores (weighted average)
        final_score = (keyword_score * 0.6) + (ml_score * 0.4)
        
        return min(final_score, 1.0)

    def _extract_date(self, soup: BeautifulSoup, url: str) -> str:
        """Extract publication date using multiple strategies"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Common date selectors
        date_selectors = [
            'time[datetime]',
            '.date',
            '.published',
            '.timestamp',
            '.article-date',
            '.post-date',
            '.entry-date',
            'meta[property="article:published_time"]',
            'meta[name="publish_date"]',
            'meta[name="date"]'
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
                        # Parse and format date
                        parsed_date = self._parse_date(date_str)
                        if parsed_date:
                            return parsed_date
            except Exception:
                continue
        
        return yesterday

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse various date formats"""
        date_formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%B %d, %Y',
            '%b %d, %Y',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y/%m/%d'
        ]
        
        for fmt in date_formats:
            try:
                parsed = datetime.strptime(date_str.strip(), fmt)
                return parsed.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None

    async def _scrape_with_requests(self, url: str) -> Optional[Dict]:
        """Scrape using requests with advanced anti-detection"""
        try:
            # Use cloudscraper to bypass Cloudflare
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'mobile': False
                }
            )
            
            # Random delay
            await asyncio.sleep(random.uniform(*self.config['scraping']['request_delay']))
            
            response = scraper.get(
                url,
                timeout=self.config['scraping']['timeout'],
                proxies={'http': self.current_proxy, 'https': self.current_proxy} if self.current_proxy else None
            )
            
            if response.status_code == 200:
                return {
                    'html': response.text,
                    'url': url,
                    'status_code': response.status_code
                }
            
        except Exception as e:
            logger.warning(f"Requests scraping failed for {url}: {e}")
        
        return None

    async def _scrape_with_browser(self, url: str) -> Optional[Dict]:
        """Scrape using browser automation"""
        try:
            if not self.driver:
                self._setup_browser()
            
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, self.config['scraping']['browser_timeout']).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Random scroll to simulate human behavior
            for _ in range(random.randint(2, 5)):
                self.driver.execute_script(f"window.scrollTo(0, {random.randint(100, 1000)});")
                await asyncio.sleep(random.uniform(0.5, 2))
            
            return {
                'html': self.driver.page_source,
                'url': url,
                'status_code': 200
            }
            
        except Exception as e:
            logger.warning(f"Browser scraping failed for {url}: {e}")
        
        return None

    def _extract_article_content(self, html: str, url: str) -> Optional[ArticleData]:
        """Extract article content using multiple extraction methods"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Method 1: Trafilatura (best for news articles)
            try:
                extracted = trafilatura.extract(html, include_formatting=True, include_links=True)
                if extracted and len(extracted) > self.config['content']['min_content_length']:
                    title = trafilatura.extract_metadata(html, url).get('title', '')
                    return ArticleData(
                        url=url,
                        title=title,
                        content=extracted,
                        published_date=self._extract_date(soup, url),
                        source=urlparse(url).netloc,
                        fire_related_score=self._is_fire_related(extracted)
                    )
            except Exception as e:
                logger.debug(f"Trafilatura extraction failed: {e}")
            
            # Method 2: Readability
            try:
                doc = Document(html)
                content = doc.summary()
                if content:
                    soup_content = BeautifulSoup(content, 'lxml')
                    text_content = soup_content.get_text().strip()
                    if len(text_content) > self.config['content']['min_content_length']:
                        return ArticleData(
                            url=url,
                            title=doc.title(),
                            content=text_content,
                            published_date=self._extract_date(soup, url),
                            source=urlparse(url).netloc,
                            fire_related_score=self._is_fire_related(text_content)
                        )
            except Exception as e:
                logger.debug(f"Readability extraction failed: {e}")
            
            # Method 3: Newspaper3k
            try:
                config = Config()
                config.browser_user_agent = self.ua.random
                article = Article(url, config=config)
                article.download(input_html=html)
                article.parse()
                
                if article.text and len(article.text) > self.config['content']['min_content_length']:
                    return ArticleData(
                        url=url,
                        title=article.title,
                        content=article.text,
                        published_date=article.publish_date.strftime('%Y-%m-%d') if article.publish_date else self._extract_date(soup, url),
                        source=urlparse(url).netloc,
                        author=article.authors[0] if article.authors else "",
                        fire_related_score=self._is_fire_related(article.text)
                    )
            except Exception as e:
                logger.debug(f"Newspaper3k extraction failed: {e}")
            
            # Method 4: Manual extraction
            try:
                # Common article selectors
                content_selectors = [
                    'article',
                    '.article-content',
                    '.post-content',
                    '.entry-content',
                    '.story-content',
                    '.news-content',
                    '.content',
                    'main'
                ]
                
                for selector in content_selectors:
                    content_element = soup.select_one(selector)
                    if content_element:
                        text_content = content_element.get_text().strip()
                        if len(text_content) > self.config['content']['min_content_length']:
                            title_element = soup.select_one('h1, .title, .headline')
                            title = title_element.get_text().strip() if title_element else ""
                            
                            return ArticleData(
                                url=url,
                                title=title,
                                content=text_content,
                                published_date=self._extract_date(soup, url),
                                source=urlparse(url).netloc,
                                fire_related_score=self._is_fire_related(text_content)
                            )
            except Exception as e:
                logger.debug(f"Manual extraction failed: {e}")
            
        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {e}")
        
        return None

    async def _scrape_single_url(self, url: str) -> Optional[ArticleData]:
        """Scrape a single URL with multiple fallback methods"""
        if url in self.scraped_urls:
            return None
        
        self.scraped_urls.add(url)
        
        # Try requests first
        result = await self._scrape_with_requests(url)
        
        # Fallback to browser if requests fails
        if not result:
            result = await self._scrape_with_browser(url)
        
        if result and result['status_code'] == 200:
            article_data = self._extract_article_content(result['html'], url)
            
            if article_data and article_data.fire_related_score >= self.config['content']['fire_related_threshold']:
                logger.info(f"Successfully scraped fire-related article: {url}", 
                           score=article_data.fire_related_score,
                           content_length=len(article_data.content))
                return article_data
        
        return None

    async def _find_article_urls(self, base_url: str) -> List[str]:
        """Find article URLs from a news website"""
        article_urls = []
        
        try:
            # Scrape homepage
            result = await self._scrape_with_requests(base_url)
            if not result:
                result = await self._scrape_with_browser(base_url)
            
            if result and result['status_code'] == 200:
                soup = BeautifulSoup(result['html'], 'lxml')
                
                # Find all links
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link['href']
                    full_url = urljoin(base_url, href)
                    
                    # Filter for article URLs
                    if self._is_article_url(full_url, base_url):
                        article_urls.append(full_url)
                
                # Remove duplicates and limit
                article_urls = list(set(article_urls))[:50]
                
        except Exception as e:
            logger.error(f"Failed to find article URLs for {base_url}: {e}")
        
        return article_urls

    def _is_article_url(self, url: str, base_url: str) -> bool:
        """Check if URL is likely an article URL"""
        parsed = urlparse(url)
        base_parsed = urlparse(base_url)
        
        # Must be from same domain
        if parsed.netloc != base_parsed.netloc:
            return False
        
        # Common article URL patterns
        article_patterns = [
            r'/article/',
            r'/news/',
            r'/story/',
            r'/post/',
            r'/entry/',
            r'/202[0-9]/',
            r'/20[0-9]{2}/',
            r'/\d{4}/\d{2}/',
            r'/\d{4}-\d{2}/'
        ]
        
        for pattern in article_patterns:
            if re.search(pattern, url):
                return True
        
        return False

    async def scrape_websites(self, websites: List[str]) -> List[ArticleData]:
        """Main scraping method for multiple websites"""
        logger.info(f"Starting to scrape {len(websites)} websites")
        
        all_articles = []
        
        # Create output directory
        output_dir = Path(self.config['storage']['output_dir'])
        output_dir.mkdir(exist_ok=True)
        
        for website in websites:
            try:
                logger.info(f"Scraping website: {website}")
                
                # Find article URLs
                article_urls = await self._find_article_urls(website)
                logger.info(f"Found {len(article_urls)} potential articles on {website}")
                
                # Scrape articles concurrently
                semaphore = asyncio.Semaphore(self.config['scraping']['max_concurrent_requests'])
                
                async def scrape_with_semaphore(url):
                    async with semaphore:
                        return await self._scrape_single_url(url)
                
                tasks = [scrape_with_semaphore(url) for url in article_urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Filter successful results
                website_articles = [r for r in results if r is not None and not isinstance(r, Exception)]
                all_articles.extend(website_articles)
                
                logger.info(f"Successfully scraped {len(website_articles)} articles from {website}")
                
                # Rotate proxy
                if self.config['scraping']['proxy_rotation']:
                    self._rotate_proxy()
                
            except Exception as e:
                logger.error(f"Failed to scrape website {website}: {e}")
                continue
        
        # Save results
        self._save_results(all_articles)
        
        logger.info(f"Scraping completed. Total articles: {len(all_articles)}")
        return all_articles

    def _save_results(self, articles: List[ArticleData]):
        """Save scraped articles to file"""
        try:
            output_dir = Path(self.config['storage']['output_dir'])
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Convert to dict for JSON serialization
            articles_dict = [asdict(article) for article in articles]
            
            # Save as JSON
            json_file = output_dir / f"fire_articles_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(articles_dict, f, indent=2, ensure_ascii=False)
            
            # Save as compressed pickle if enabled
            if self.config['storage']['compression_enabled']:
                pickle_file = output_dir / f"fire_articles_{timestamp}.pkl.gz"
                with gzip.open(pickle_file, 'wb') as f:
                    pickle.dump(articles, f)
            
            # Create summary
            summary = {
                'total_articles': len(articles),
                'sources': list(set(article.source for article in articles)),
                'date_range': {
                    'start': min(article.published_date for article in articles) if articles else None,
                    'end': max(article.published_date for article in articles) if articles else None
                },
                'fire_scores': {
                    'min': min(article.fire_related_score for article in articles) if articles else 0,
                    'max': max(article.fire_related_score for article in articles) if articles else 0,
                    'avg': sum(article.fire_related_score for article in articles) / len(articles) if articles else 0
                }
            }
            
            summary_file = output_dir / f"scraping_summary_{timestamp}.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"Results saved to {output_dir}", 
                       json_file=str(json_file),
                       pickle_file=str(pickle_file) if self.config['storage']['compression_enabled'] else None,
                       summary_file=str(summary_file))
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
        
        if self.session:
            try:
                asyncio.create_task(self.session.close())
            except Exception:
                pass

async def main():
    """Main function"""
    # List of news websites to scrape
    websites = [
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
    
    scraper = AdvancedFireScraper()
    
    try:
        articles = await scraper.scrape_websites(websites)
        print(f"\nScraping completed! Found {len(articles)} fire-related articles.")
        
        # Print summary
        if articles:
            print("\nTop 5 articles by fire relevance score:")
            sorted_articles = sorted(articles, key=lambda x: x.fire_related_score, reverse=True)
            for i, article in enumerate(sorted_articles[:5], 1):
                print(f"{i}. {article.title[:80]}... (Score: {article.fire_related_score:.2f})")
                print(f"   Source: {article.source}")
                print(f"   URL: {article.url}")
                print()
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 