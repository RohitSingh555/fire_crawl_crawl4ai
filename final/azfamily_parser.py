import json
from datetime import datetime
from dateutil import parser
from bs4 import BeautifulSoup
import re

def parse_azfamily_html(html_content):
    """Parse AZ Family HTML and extract fire-related articles from yesterday"""
    
    soup = BeautifulSoup(html_content, "html.parser")
    articles = []
    
    # Find all article rows
    article_rows = soup.select("div.queryly_item_row")
    
    print(f"Found {len(article_rows)} potential articles")
    
    for row in article_rows:
        try:
            # Extract link
            link_elem = row.select_one("a")
            if not link_elem or not link_elem.has_attr("href"):
                continue
                
            href = link_elem["href"]
            
            # Skip video links and non-article links
            if href.startswith("/video/") or href.startswith("/page/"):
                continue
                
            # Make URL absolute
            if href.startswith("/"):
                url = "https://www.azfamily.com" + href
            else:
                url = href
            
            # Extract title
            title_elem = row.select_one("div.queryly_item_title")
            if not title_elem:
                continue
            title = title_elem.get_text(strip=True)
            
            # Extract description
            desc_elem = row.select_one("div.queryly_item_description")
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # Extract date
            date_elem = row.select_one("div[style*='margin-top:6px;color:#555;font-size:12px;']")
            if not date_elem:
                continue
            date_text = date_elem.get_text(strip=True)
            
            # Parse date and check if it's from yesterday
            try:
                # Handle "Jun 23, 2025" format
                parsed_date = parser.parse(date_text)
                today = datetime.now().date()
                article_date = parsed_date.date()
                
                # Check if article is from yesterday or today
                if (today - article_date).days <= 1:
                    article = {
                        "source": "AZ Family",
                        "title": title,
                        "url": url,
                        "date": date_text,
                        "description": description,
                        "full_date": parsed_date.strftime("%Y-%m-%d %H:%M:%S"),
                        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    articles.append(article)
                    print(f"✅ Added: {title} - {date_text}")
                else:
                    print(f"⏰ Skipped (old): {title} - {date_text}")
                    
            except Exception as e:
                print(f"❌ Date parsing error for '{title}': {e}")
                continue
                
        except Exception as e:
            print(f"❌ Error processing article row: {e}")
            continue
    
    return articles

def save_articles(articles, filename="azfamily_yesterday_articles.json"):
    """Save articles to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(articles, f, indent=4, ensure_ascii=False)
    print(f"✅ Saved {len(articles)} articles to {filename}")

def main():
    """Main function to demonstrate parsing"""
    
    # Example HTML content (you can replace this with actual HTML)
    sample_html = """
    <div id="resultdata">
        <div class="queryly_item_row" style="max-height:180px;position:relative;overflow:hidden;margin-bottom:20px;font-size:10px;border-bottom:1px solid #ccc;padding-bottom:20px;width:100%;">
            <a href="/2025/06/22/fast-moving-fire-tears-through-phoenix-mobile-home-park/" style="text-decoration:none;color:#333">
                <div class="queryly_advanced_item_imagecontainer" style="float:left;background-image: url('/resizer/v2/IUH6TLL5MBCKPDIUSBXCTGTRUM.png?auth=a3d60117eb406dffe18503ed7310a2015b9b3f75bf8d46d9aee3841e0f5156cb&amp;width=300');background-size:cover;background-color:#aaa;"></div>
                <div style="margin-top:0px;overflow:hidden;">
                    <div class="queryly_item_title" style="font-weight:bold;">33 people displaced after fire tears through Phoenix mobile home park</div>
                    <div class="queryly_item_description">PHOENIX (AZFamily) — Fire crews responded to a fast-moving fire at a mobile home park ...</div>
                    <div style="margin-top:6px;color:#555;font-size:12px;">Jun 23, 2025</div>
                </div>
            </a>
        </div>
        <div class="queryly_item_row" style="max-height:180px;position:relative;overflow:hidden;margin-bottom:20px;font-size:10px;border-bottom:1px solid #ccc;padding-bottom:20px;width:100%;">
            <a href="/2025/06/21/person-critical-condition-after-being-rescued-house-fire-apache-junction/" style="text-decoration:none;color:#333">
                <div class="queryly_advanced_item_imagecontainer" style="float:left;background-image: url('/resizer/v2/L5DBUZLZFJECTF7O44KRFP6ZVA.png?auth=154084744e58a87f8e6c25b52df2ddf72f1ac35a7a018899a4450eef53bd0483&amp;width=300');background-size:cover;background-color:#aaa;"></div>
                <div style="margin-top:0px;overflow:hidden;">
                    <div class="queryly_item_title" style="font-weight:bold;">Person in critical condition after being rescued from house fire in Apache Junction</div>
                    <div class="queryly_item_description">APACHE JUNCTION, AZ (AZFamily) — A person is in the hospital after being pulled from ...</div>
                    <div style="margin-top:6px;color:#555;font-size:12px;">Jun 21, 2025</div>
                </div>
            </a>
        </div>
    </div>
    """
    
    # Parse the HTML
    articles = parse_azfamily_html(sample_html)
    
    # Save results
    save_articles(articles)
    
    # Print summary
    print(f"\n📊 Summary:")
    print(f"Total articles found: {len(articles)}")
    for article in articles:
        print(f"📰 {article['title']} - {article['date']}")
        print(f"   URL: {article['url']}")
        print(f"   Description: {article['description'][:100]}...")
        print()

if __name__ == "__main__":
    main() 