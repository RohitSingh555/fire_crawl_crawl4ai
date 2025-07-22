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
            
            # Extract date - look for the div with specific styling
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
    """Main function to parse the provided HTML"""
    
    # The HTML content you provided
    html_content = """
    <div id="resultdata">
        <div class="queryly_item_row" style="max-height:180px;position:relative;overflow:hidden;margin-bottom:20px;font-size:10px;border-bottom:1px solid #ccc;padding-bottom:20px;width:100%;">
            <a onmousedown="queryly.util.trackClick('/2025/06/22/fast-moving-fire-tears-through-phoenix-mobile-home-park/','fire ');" href="/2025/06/22/fast-moving-fire-tears-through-phoenix-mobile-home-park/" style="text-decoration:none;color:#333">
                <div class="queryly_advanced_item_imagecontainer" style="float:left;background-image: url('/resizer/v2/IUH6TLL5MBCKPDIUSBXCTGTRUM.png?auth=a3d60117eb406dffe18503ed7310a2015b9b3f75bf8d46d9aee3841e0f5156cb&amp;width=300');background-size:cover;background-color:#aaa;"></div>
                <div style="margin-top:0px;overflow:hidden;">
                    <div class="queryly_item_title" style="font-weight:bold;">33 people displaced after fire tears through Phoenix mobile home park</div>
                    <div class="queryly_item_description">PHOENIX (AZFamily) — Fire crews responded to a fast-moving fire at a mobile home park ...</div>
                    <div style="margin-top:6px;color:#555;font-size:12px;">Jun 23, 2025</div>
                </div>
            </a>
        </div>
        <div class="queryly_item_row" style="max-height:180px;position:relative;overflow:hidden;margin-bottom:20px;font-size:10px;border-bottom:1px solid #ccc;padding-bottom:20px;width:100%;">
            <a onmousedown="queryly.util.trackClick('/2025/06/21/person-critical-condition-after-being-rescued-house-fire-apache-junction/','fire ');" href="/2025/06/21/person-critical-condition-after-being-rescued-house-fire-apache-junction/" style="text-decoration:none;color:#333">
                <div class="queryly_advanced_item_imagecontainer" style="float:left;background-image: url('/resizer/v2/L5DBUZLZFJECTF7O44KRFP6ZVA.png?auth=154084744e58a87f8e6c25b52df2ddf72f1ac35a7a018899a4450eef53bd0483&amp;width=300');background-size:cover;background-color:#aaa;"></div>
                <div style="margin-top:0px;overflow:hidden;">
                    <div class="queryly_item_title" style="font-weight:bold;">Person in critical condition after being rescued from house fire in Apache Junction</div>
                    <div class="queryly_item_description">APACHE JUNCTION, AZ (AZFamily) — A person is in the hospital after being pulled from ...</div>
                    <div style="margin-top:6px;color:#555;font-size:12px;">Jun 21, 2025</div>
                </div>
            </a>
        </div>
        <div class="queryly_item_row" style="max-height:180px;position:relative;overflow:hidden;margin-bottom:20px;font-size:10px;border-bottom:1px solid #ccc;padding-bottom:20px;width:100%;">
            <a onmousedown="queryly.util.trackClick('/video/2025/06/23/more-than-30-people-displaced-after-mobile-home-fire-phoenix/','fire ');" href="/video/2025/06/23/more-than-30-people-displaced-after-mobile-home-fire-phoenix/" style="text-decoration:none;color:#333">
                <div class="queryly_advanced_item_imagecontainer" style="float:left;background-image: url('https://do0bihdskp9dy.cloudfront.net/06-23-2025/t_1235cee5c9df44f2a82c8e9debe24aab_name_file_1280x720_2000_v3_1_.jpg');background-size:cover;background-color:#aaa;"></div>
                <div style="margin-top:0px;overflow:hidden;">
                    <div class="queryly_item_title" style="font-weight:bold;">More than 30 people displaced after mobile home fire in Phoenix</div>
                    <div class="queryly_item_description"></div>
                    <div style="margin-top:6px;color:#555;font-size:12px;">Jun 23, 2025</div>
                </div>
            </a>
        </div>
        <div class="queryly_item_row" style="max-height:180px;position:relative;overflow:hidden;margin-bottom:20px;font-size:10px;border-bottom:1px solid #ccc;padding-bottom:20px;width:100%;">
            <a onmousedown="queryly.util.trackClick('/2025/06/18/gila-river-police-seek-alleged-arsonist-accused-setting-fire-old-school-gym/','fire ');" href="/2025/06/18/gila-river-police-seek-alleged-arsonist-accused-setting-fire-old-school-gym/" style="text-decoration:none;color:#333">
                <div class="queryly_advanced_item_imagecontainer" style="float:left;background-image: url('/resizer/v2/KYFFQCVKGVH5HAHFKVS24ZPDSU.png?auth=2d7fcc808887ee539482acfba004dc6fba1f5c9c00112a2925d4c80cffdad4cd&amp;width=300');background-size:cover;background-color:#aaa;"></div>
                <div style="margin-top:0px;overflow:hidden;">
                    <div class="queryly_item_title" style="font-weight:bold;">Gila River police seek alleged arsonist accused of setting fire to old school gym</div>
                    <div class="queryly_item_description">GILA RIVER INDIAN COMMUNITY, AZ (AZFamily) — Authorities are seeking information about an alleged arsonist ...</div>
                    <div style="margin-top:6px;color:#555;font-size:12px;">Jun 19, 2025</div>
                </div>
            </a>
        </div>
        <div class="queryly_item_row" style="max-height:180px;position:relative;overflow:hidden;margin-bottom:20px;font-size:10px;border-bottom:1px solid #ccc;padding-bottom:20px;width:100%;">
            <a onmousedown="queryly.util.trackClick('/2025/06/17/seeing-smoke-crews-battle-brush-fire-north-mountain-phoenix/','fire ');" href="/2025/06/17/seeing-smoke-crews-battle-brush-fire-north-mountain-phoenix/" style="text-decoration:none;color:#333">
                <div class="queryly_advanced_item_imagecontainer" style="float:left;background-image: url('https://cloudfront-us-east-1.images.arcpublishing.com/gray/RQXB43VZN5EFHBA6N376A5QW5I.jpeg');background-size:cover;background-color:#aaa;"></div>
                <div style="margin-top:0px;overflow:hidden;">
                    <div class="queryly_item_title" style="font-weight:bold;">Crews extinguish brush fire on Shaw Butte Trail in Phoenix</div>
                    <div class="queryly_item_description">PHOENIX (AZFamily) — Dozens of fire crews from local and state agencies came together to ...</div>
                    <div style="margin-top:6px;color:#555;font-size:12px;">Jun 18, 2025</div>
                </div>
            </a>
        </div>
        <div class="queryly_item_row" style="max-height:180px;position:relative;overflow:hidden;margin-bottom:20px;font-size:10px;border-bottom:1px solid #ccc;padding-bottom:20px;width:100%;">
            <a onmousedown="queryly.util.trackClick('/2025/06/16/flagstaff-apartment-fire-forces-resident-jump-second-story-window/','fire ');" href="/2025/06/16/flagstaff-apartment-fire-forces-resident-jump-second-story-window/" style="text-decoration:none;color:#333">
                <div class="queryly_advanced_item_imagecontainer" style="float:left;background-image: url('https://cloudfront-us-east-1.images.arcpublishing.com/gray/6MFFLBOU7VEKXPJ5TMRCRF3PRE.png');background-size:cover;background-color:#aaa;"></div>
                <div style="margin-top:0px;overflow:hidden;">
                    <div class="queryly_item_title" style="font-weight:bold;">Flagstaff apartment fire forces resident to jump from second-story window</div>
                    <div class="queryly_item_description">FLAGSTAFF, AZ (AZFamily) — Two people were injured after an apartment fire broke out early ...</div>
                    <div style="margin-top:6px;color:#555;font-size:12px;">Jun 17, 2025</div>
                </div>
            </a>
        </div>
        <div class="queryly_item_row" style="max-height:180px;position:relative;overflow:hidden;margin-bottom:20px;font-size:10px;border-bottom:1px solid #ccc;padding-bottom:20px;width:100%;">
            <a onmousedown="queryly.util.trackClick('/2025/06/15/man-hospitalized-heat-related-issues-after-house-fire-south-phoenix/','fire ');" href="/2025/06/15/man-hospitalized-heat-related-issues-after-house-fire-south-phoenix/" style="text-decoration:none;color:#333">
                <div class="queryly_advanced_item_imagecontainer" style="float:left;background-image: url('/resizer/v2/G7QV2YDT4JC6NOOAHHIEC3QDTI.png?auth=4fc9364bf9b01cc85b3ccb231df2eb55a33b142d8dd001e605bf97b2e93d0a33&amp;width=300');background-size:cover;background-color:#aaa;"></div>
                <div style="margin-top:0px;overflow:hidden;">
                    <div class="queryly_item_title" style="font-weight:bold;">Man hospitalized for heat-related issues after house fire in south Phoenix</div>
                    <div class="queryly_item_description">PHOENIX (AZFamily) — One person is in the hospital after a house fire in south ...</div>
                    <div style="margin-top:6px;color:#555;font-size:12px;">Jun 16, 2025</div>
                </div>
            </a>
        </div>
        <div class="queryly_item_row" style="max-height:180px;position:relative;overflow:hidden;margin-bottom:20px;font-size:10px;border-bottom:1px solid #ccc;padding-bottom:20px;width:100%;">
            <a onmousedown="queryly.util.trackClick('/2025/06/16/crews-battle-cub-fire-caused-by-crash-east-phoenix/','fire ');" href="/2025/06/16/crews-battle-cub-fire-caused-by-crash-east-phoenix/" style="text-decoration:none;color:#333">
                <div class="queryly_advanced_item_imagecontainer" style="float:left;background-image: url('/resizer/v2/GRSAPILXWREG7DWHFOOLI4UXEE.png?auth=e66c206162a4091a80d5379802d2eadeb4f0db22df190591a0c3067b6be17a38&amp;width=300');background-size:cover;background-color:#aaa;"></div>
                <div style="margin-top:0px;overflow:hidden;">
                    <div class="queryly_item_title" style="font-weight:bold;">Crews battle Cub Fire caused by crash east of Phoenix</div>
                    <div class="queryly_item_description">MESA, AZ (AZFamily) — Fire crews in the Tonto National Forest are working to suppress ...</div>
                    <div style="margin-top:6px;color:#555;font-size:12px;">Jun 17, 2025</div>
                </div>
            </a>
        </div>
        <div class="queryly_item_row" style="max-height:180px;position:relative;overflow:hidden;margin-bottom:20px;font-size:10px;border-bottom:1px solid #ccc;padding-bottom:20px;width:100%;">
            <a onmousedown="queryly.util.trackClick('/2025/06/15/man-dead-after-apartment-fire-north-phoenix/','fire ');" href="/2025/06/15/man-dead-after-apartment-fire-north-phoenix/" style="text-decoration:none;color:#333">
                <div class="queryly_advanced_item_imagecontainer" style="float:left;background-image: url('/resizer/v2/IQT4RVXCE5AC3LB4EVX23OZ7TQ.jpeg?auth=d67502cb778640fb33e2b394e0cc77a871306a4e0c57986e36f2f5a030059e76&amp;width=300');background-size:cover;background-color:#aaa;"></div>
                <div style="margin-top:0px;overflow:hidden;">
                    <div class="queryly_item_title" style="font-weight:bold;">Man dead after apartment fire in north Phoenix</div>
                    <div class="queryly_item_description">PHOENIX (AZFamily) — A man has died after fire crews pulled him out of a ...</div>
                    <div style="margin-top:6px;color:#555;font-size:12px;">Jun 16, 2025</div>
                </div>
            </a>
        </div>
        <div class="queryly_item_row" style="max-height:180px;position:relative;overflow:hidden;margin-bottom:20px;font-size:10px;border-bottom:1px solid #ccc;padding-bottom:20px;width:100%;">
            <a onmousedown="queryly.util.trackClick('/2025/06/17/goodyear-fire-captain-thanks-officer-who-saved-his-daughter-burning-car/','fire ');" href="/2025/06/17/goodyear-fire-captain-thanks-officer-who-saved-his-daughter-burning-car/" style="text-decoration:none;color:#333">
                <div class="queryly_advanced_item_imagecontainer" style="float:left;background-image: url('/resizer/v2/HIQOYM27TNFELKGGT3SV5JV7UY.png?auth=bf6b4a08cda9cc789fe5532799d7ee970589877578c18f3cef827d72df5d6a5a&amp;width=300');background-size:cover;background-color:#aaa;"></div>
                <div style="margin-top:0px;overflow:hidden;">
                    <div class="queryly_item_title" style="font-weight:bold;">Goodyear fire captain thanks officer who saved his daughter from burning car</div>
                    <div class="queryly_item_description">GOODYEAR, AZ (AZFamily) — An officer's body camera caught a dramatic rescue in Goodyear after ...</div>
                    <div style="margin-top:6px;color:#555;font-size:12px;">Jun 17, 2025</div>
                </div>
            </a>
        </div>
        <div class="queryly_item_row" style="max-height:180px;position:relative;overflow:hidden;margin-bottom:20px;font-size:10px;border-bottom:1px solid #ccc;padding-bottom:20px;width:100%;">
            <a onmousedown="queryly.util.trackClick('/2025/06/12/gilbert-sees-more-garbage-trucks-catch-fire-due-hazardous-materials-thrown-out/','fire ');" href="/2025/06/12/gilbert-sees-more-garbage-trucks-catch-fire-due-hazardous-materials-thrown-out/" style="text-decoration:none;color:#333">
                <div class="queryly_advanced_item_imagecontainer" style="float:left;background-image: url('/resizer/v2/BFWD2MJSQ5GX3JLW3ICROQ7NUA.png?auth=fc03804904f711c0c51eff2840441c7f79e1a6aa59b6d5f7b4cf9124f1bdd840&amp;width=300');background-size:cover;background-color:#aaa;"></div>
                <div style="margin-top:0px;overflow:hidden;">
                    <div class="queryly_item_title" style="font-weight:bold;">Gilbert sees more garbage trucks catch fire due to hazardous materials thrown out</div>
                    <div class="queryly_item_description">GILBERT, AZ (AZFamily) — The town of Gilbert has become the epicenter of a fiery ...</div>
                    <div style="margin-top:6px;color:#555;font-size:12px;">Jun 13, 2025</div>
                </div>
            </a>
        </div>
        <div class="queryly_item_row" style="max-height:180px;position:relative;overflow:hidden;margin-bottom:20px;font-size:10px;border-bottom:1px solid #ccc;padding-bottom:20px;width:100%;">
            <a onmousedown="queryly.util.trackClick('/2025/06/14/flood-control-system-pipeline-fire-burn-scar-flagstaff-completed/','fire ');" href="/2025/06/14/flood-control-system-pipeline-fire-burn-scar-flagstaff-completed/" style="text-decoration:none;color:#333">
                <div class="queryly_advanced_item_imagecontainer" style="float:left;background-image: url('/resizer/v2/2ZO7W7WX7NFSBGQMZPOPXE6FGM.png?auth=1f40745e8a8fa99f3bb0cecced9b3db769c54c8d67c9344d64a5541cc9aa9a97&amp;width=300');background-size:cover;background-color:#aaa;"></div>
                <div style="margin-top:0px;overflow:hidden;">
                    <div class="queryly_item_title" style="font-weight:bold;">Flood control system in Pipeline Fire burn scar in Flagstaff completed</div>
                    <div class="queryly_item_description">FLAGSTAFF, AZ (AZFamily) — Just one day after the three-year anniversary of the Pipline Fire ...</div>
                    <div style="margin-top:6px;color:#555;font-size:12px;">Jun 14, 2025</div>
                </div>
            </a>
        </div>
        <div class="queryly_item_row" style="max-height:180px;position:relative;overflow:hidden;margin-bottom:20px;font-size:10px;border-bottom:1px solid #ccc;padding-bottom:20px;width:100%;">
            <a onmousedown="queryly.util.trackClick('/2025/06/13/brush-fire-prompts-closure-sr-87-south-payson/','fire ');" href="/2025/06/13/brush-fire-prompts-closure-sr-87-south-payson/" style="text-decoration:none;color:#333">
                <div class="queryly_advanced_item_imagecontainer" style="float:left;background-image: url('/resizer/v2/PNCPWI7Y7ZHOHGKP3SIHHQYICM.png?auth=01c045decda471eecf609633043ed8e11d73d3a632759d25e8019208fb2658a6&amp;width=300');background-size:cover;background-color:#aaa;"></div>
                <div style="margin-top:0px;overflow:hidden;">
                    <div class="queryly_item_title" style="font-weight:bold;">SR 87 south of Payson reopens as brush fire burns</div>
                    <div class="queryly_item_description">DEER CREEK, AZ (AZFamily) — A growing brush fire prompted the partial closure of a ...</div>
                    <div style="margin-top:6px;color:#555;font-size:12px;">Jun 14, 2025</div>
                </div>
            </a>
        </div>
        <a style="float:right;font-family: Segoe UI,Roboto,Helvetica Neue,Arial;font-size: 17px;color: #428bca;font-weight: 600;" class="next_btn" onclick="searchPage.turnpage(20);return false;" href="#">Next Page</a>
    </div>
    """
    
    # Parse the HTML
    articles = parse_azfamily_html(html_content)
    
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