#!/usr/bin/env python3
"""
Main scraper class with anti-detection capabilities
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
from typing import List, Dict, Optional, Set
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue
from pathlib import Path

# Advanced scraping libraries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# BeautifulSoup for HTML parsing
from bs4 import BeautifulSoup
import lxml

# Advanced HTTP libraries
import cloudscraper
from fake_useragent import UserAgent
import undetected_chromedriver as uc

# Data processing
import pandas as pd
from newspaper import Article, Config
import trafilatura
from readability import Document

# Machine learning for content classification
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib

# Import our modules
from config import load_config, FIRE_KEYWORDS
from models import ArticleData
from utils import setup_logging

logger = setup_logging()

class AdvancedFireScraper:
    """Advanced web scraper with anti-detection capabilities"""
    
    def __init__(self, config_path: str = "scraper_config.yaml"):
        self.config = load_config(config_path)
        self.session = None
        self.driver = None
        self.ua = UserAgent()
        self.proxy_list = self._load_proxies()
        self.current_proxy = None
        self.scraped_urls = set()
        self.article_queue = Queue()
        self.results = []
        self.lock = threading.Lock()
        
        # Initialize ML model for fire content classification
        self.ml_model = self._load_ml_model()
        
        logger.info("Advanced Fire Scraper initialized", 
                   config_loaded=True, 
                   proxy_count=len(self.proxy_list),
                   fire_keywords_count=len(FIRE_KEYWORDS))

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

    def _is_fire_related(self, text: str) -> float:
        """Determine if content is fire-related using ML and keyword matching"""
        if not text:
            return 0.0
        
        # Keyword-based scoring
        text_lower = text.lower()
        keyword_matches = sum(1 for keyword in FIRE_KEYWORDS if keyword in text_lower)
        keyword_score = keyword_matches / len(FIRE_KEYWORDS)
        
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
            
        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {e}")
        
        return None

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

    async def _scrape_single_url(self, url: str) -> Optional[ArticleData]:
        """Scrape a single URL with multiple fallback methods"""
        if url in self.scraped_urls:
            return None
        
        self.scraped_urls.add(url)
        
        # Try requests first
        result = await self._scrape_with_requests(url)
        
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
            articles_dict = [article.to_dict() for article in articles]
            
            # Save as JSON
            json_file = output_dir / f"fire_articles_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(articles_dict, f, indent=2, ensure_ascii=False)
            
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