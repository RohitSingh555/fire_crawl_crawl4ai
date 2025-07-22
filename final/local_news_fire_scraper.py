import asyncio
import json
import re
import time
import random
import requests
from datetime import datetime, timedelta
from dateutil import parser
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from urllib.parse import urljoin, urlparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Local news websites
LOCAL_NEWS_SITES = [
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

# User agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

# Headers for requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0'
}

def is_recent_article(date_string, days_limit=7):
    """Check if article is recent (within specified days)"""
    try:
        if not date_string:
            return True  # Include articles without dates
        
        # Try to parse the date
        parsed_date = parser.parse(date_string, fuzzy=True)
        if isinstance(parsed_date, datetime):
            days_diff = (datetime.now() - parsed_date).days
            return days_diff <= days_limit
        return True
    except:
        return True  # Include articles with unparseable dates

def is_fire_related(title, content):
    """Check if article is fire-related"""
    fire_keywords = [
        'fire', 'blaze', 'burning', 'burned', 'burn', 'flame', 'flames', 'smoke',
        'arson', 'firefighter', 'fire department', 'fire station', 'fire truck',
        'wildfire', 'forest fire', 'brush fire', 'house fire', 'building fire',
        'fire alarm', 'fire safety', 'fire prevention', 'fire damage', 'fire loss'
    ]
    
    text = f"{title} {content}".lower()
    return any(keyword in text for keyword in fire_keywords)

def requests_scrape(url, timeout=15):
    """Method 1: Simple requests scraping"""
    try:
        headers = HEADERS.copy()
        headers['User-Agent'] = random.choice(USER_AGENTS)
        
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        
        if len(response.content) > 1000:
            return response.text
    except Exception as e:
        logger.debug(f"Requests failed for {url}: {e}")
    return None

async def playwright_scrape(url, timeout=30):
    """Method 2: Playwright scraping with stealth"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers=HEADERS
            )
            
            page = await context.new_page()
            
            await page.goto(url, timeout=timeout*1000, wait_until='domcontentloaded')
            await asyncio.sleep(3)
            
            # Try to wait for content
            selectors = ['h1', 'h2', 'p', 'article', '.content', '.article', 'body']
            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    break
                except:
                    continue
            
            html = await page.content()
            await browser.close()
            
            if html and len(html) > 1000:
                return html
                
    except Exception as e:
        logger.debug(f"Playwright failed for {url}: {e}")
    return None

def curl_scrape(url, timeout=30):
    """Method 3: Curl as fallback"""
    try:
        user_agent = random.choice(USER_AGENTS)
        cmd = [
            'curl', '-s', '-L', '--max-time', str(timeout),
            '-H', f'User-Agent: {user_agent}',
            '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            '-H', 'Accept-Language: en-US,en;q=0.5',
            '-H', 'Accept-Encoding: gzip, deflate',
            '-H', 'Connection: keep-alive',
            '--compressed',
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+5)
        
        if result.returncode == 0 and len(result.stdout) > 1000:
            return result.stdout
            
    except Exception as e:
        logger.debug(f"Curl failed for {url}: {e}")
    return None

def universal_scrape(url):
    """Universal scraper that tries multiple methods"""
    logger.info(f"🔍 Scraping: {url}")
    
    # Method 1: Requests
    html = requests_scrape(url)
    if html:
        logger.info("  ✅ Requests succeeded")
        return html
    
    # Method 2: Playwright
    try:
        html = asyncio.run(playwright_scrape(url))
        if html:
            logger.info("  ✅ Playwright succeeded")
            return html
    except Exception as e:
        logger.debug(f"  ❌ Playwright error: {e}")
    
    # Method 3: Curl
    html = curl_scrape(url)
    if html:
        logger.info("  ✅ Curl succeeded")
        return html
    
    logger.warning("  ❌ All methods failed")
    return None

def extract_article_data_from_html(html, url):
    """Extract title, content, and date from HTML content"""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = None
        title_selectors = [
            'h1', 'h1.article-title', 'h1.headline', 'h1.story-title',
            '.article-title', '.headline', 'title', '.title', '.post-title',
            '.entry-title', '.story-title', '.news-title'
        ]
        
        for selector in title_selectors:
            title_el = soup.select_one(selector)
            if title_el:
                title = title_el.get_text(strip=True)
                break
        
        if not title:
            title = "No Title Found"
        
        # Extract content
        content_parts = []
        content_selectors = [
            '.content', '.article-content', '.post-content', '.entry-content',
            '.story-content', '.article-body', '.post-body', 'article',
            '.news-content', '.story-body', '.main-content'
        ]
        
        # Try specific content areas first
        for selector in content_selectors:
            content_el = soup.select_one(selector)
            if content_el:
                paragraphs = content_el.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:
                        content_parts.append(text)
                if content_parts:
                    break
        
        # If no content found, get all paragraphs
        if not content_parts:
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    content_parts.append(text)
        
        content = ' '.join(content_parts)
        
        # Extract date
        date = None
        date_selectors = [
            'time[datetime]', 'time', '.date', '.timestamp', '.published-date',
            '.article-date', '.story-date', '.post-date', '.entry-date',
            '.news-date', '.publish-date', '.meta-date'
        ]
        
        for selector in date_selectors:
            date_el = soup.select_one(selector)
            if date_el:
                if date_el.has_attr('datetime'):
                    date = date_el['datetime']
                else:
                    date = date_el.get_text(strip=True)
                break
        
        # Try JSON-LD for date
        if not date:
            for script in soup.find_all("script", {"type": "application/ld+json"}):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        date = data.get("uploadDate") or data.get("datePublished") or data.get("dateCreated")
                        if date:
                            break
                except:
                    continue
        
        # Try regex patterns in content
        if not date:
            date_patterns = [
                r'\d{1,2}:\d{2} [APM]{2} [A-Za-z]{3} \d{1,2}, \d{4}',
                r'[A-Za-z]{3} \d{1,2}, \d{4}',
                r'[A-Za-z]{4,9} \d{1,2}, \d{4}',
                r'\d{1,2} [A-Za-z]{3} \d{1,4}, \d{4}',
                r'\d{4}-\d{2}-\d{2}',
            ]
            for pattern in date_patterns:
                match = re.search(pattern, content)
                if match:
                    date = match.group()
                    break
        
        return title, content, date
        
    except Exception as e:
        logger.error(f"Error extracting data from HTML: {e}")
        return None, None, None

def extract_article_data(url):
    """Main function to extract article data"""
    try:
        html = universal_scrape(url)
        if not html:
            return None, None, None
        
        title, content, date = extract_article_data_from_html(html, url)
        return title, content, date
        
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None, None, None

async def find_article_links(site_url, page):
    """Find article links on a news site"""
    try:
        await page.goto(site_url, timeout=30000)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)
        
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Common article link patterns
        link_selectors = [
            'a[href*="/article/"]',
            'a[href*="/news/"]',
            'a[href*="/story/"]',
            'a[href*="/post/"]',
            'a[href*="/entry/"]',
            'article a',
            '.article a',
            '.news-item a',
            '.story a',
            '.post a',
            'h1 a',
            'h2 a',
            'h3 a'
        ]
        
        links = set()
        for selector in link_selectors:
            elements = soup.select(selector)
            for element in elements:
                if element.has_attr('href'):
                    href = element['href']
                    if href.startswith('/'):
                        full_url = urljoin(site_url, href)
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue
                    
                    # Filter out non-article URLs
                    if any(skip in full_url.lower() for skip in ['/tag/', '/category/', '/author/', '/page/', '/search']):
                        continue
                    
                    links.add(full_url)
        
        return list(links)
        
    except Exception as e:
        logger.error(f"Error finding links on {site_url}: {e}")
        return []

def process_article(url):
    """Process a single article URL"""
    try:
        title, content, date = extract_article_data(url)
        
        if title and content and is_fire_related(title, content):
            if is_recent_article(date):
                return {
                    'title': title,
                    'url': url,
                    'date': date,
                    'content': content[:1000],  # Limit content length
                    'source': urlparse(url).netloc
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Error processing article {url}: {e}")
        return None

async def scrape_site(site_url):
    """Scrape a single news site for fire-related articles"""
    logger.info(f"🌐 Scraping site: {site_url}")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Find article links
            links = await find_article_links(site_url, page)
            logger.info(f"  Found {len(links)} potential articles")
            
            await browser.close()
            
            # Process articles
            articles = []
            for link in links[:20]:  # Limit to 20 articles per site
                article = process_article(link)
                if article:
                    articles.append(article)
                    logger.info(f"  🔥 Found fire article: {article['title'][:50]}...")
            
            return articles
            
    except Exception as e:
        logger.error(f"Error scraping site {site_url}: {e}")
        return []

async def main():
    """Main function to scrape all local news sites"""
    logger.info("🚀 Starting local news fire scraper...")
    
    all_articles = []
    
    # Process sites in batches to avoid overwhelming
    batch_size = 5
    for i in range(0, len(LOCAL_NEWS_SITES), batch_size):
        batch = LOCAL_NEWS_SITES[i:i+batch_size]
        logger.info(f"📰 Processing batch {i//batch_size + 1}/{(len(LOCAL_NEWS_SITES) + batch_size - 1)//batch_size}")
        
        tasks = [scrape_site(site) for site in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            else:
                logger.error(f"Batch processing error: {result}")
        
        # Save progress
        with open('local_news_fire_articles.json', 'w', encoding='utf-8') as f:
            json.dump(all_articles, f, indent=4, ensure_ascii=False)
        
        logger.info(f"✅ Batch complete. Total articles so far: {len(all_articles)}")
        await asyncio.sleep(2)  # Be respectful
    
    logger.info(f"🎉 Scraping complete! Found {len(all_articles)} fire-related articles")
    logger.info("📁 Results saved to local_news_fire_articles.json")
    
    return all_articles

if __name__ == "__main__":
    asyncio.run(main()) 