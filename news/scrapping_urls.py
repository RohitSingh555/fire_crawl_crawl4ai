import requests
from bs4 import BeautifulSoup
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

websites = [
    "https://www.azfamily.com",
    "https://www.dcnewsnow.com",
    "https://kion546.com",
    "https://firenews.com",
    "https://www.wdsu.com",
    "https://www.dallasobserver.com",
    "https://www.star-telegram.com/news/local/dallas",
    "https://www.texasobserver.org",
    "https://www.houstonchronicle.com",
    "https://ramblernewspapers.com",
    "https://www.irvingjournal.com",
    "https://www.sacbee.com",
    "https://www.sacgazette.com/",
    "https://www.fire.ca.gov/incidents",
    "https://www.firerescue1.com",
    "https://www.nfpa.org",
    "https://www.fire.ca.gov",
    "https://www.bbc.com/news",
    "https://www.cnn.com",
    "https://www.nytimes.com",
    "https://www.theguardian.com",
    "https://www.reuters.com",
    "https://www.aljazeera.com",
    "https://www.foxnews.com",
    "https://www.nbcnews.com",
    "https://abcnews.go.com",
    "https://www.washingtonpost.com",
    "https://www.bloomberg.com",
    "https://www.ft.com",
    "https://www.wsj.com",
    "https://www.usatoday.com",
    "https://www.cbsnews.com/tag/house-fire/",
    "https://www.wowt.com/",
    "https://abc7.com/post",
    "https://abc7.com/search/?query=fire",
    "https://www.independent.co.uk/news/world/americas/",
      "https://www.whitecountycitizen.com",
  "https://www.stuttgartdailyleader.com",
  "https://www.adn.com",
  "https://www.newsminer.com",
  "https://www.juneauempire.com",
  "https://www.ketchikandailynews.com",
  "https://www.kodiakdailymirror.com",
  "https://sitkasentinel.com",
  "https://www.latimes.com",
  "https://www.dailynews.com",
  "https://www.laweekly.com",
  "https://www.ladowntownnews.com",
  "https://www.glendalenewspress.com",
  "https://www.burbankleader.com",
  "https://www.pasadenastarnews.com",
  "https://www.dailybreeze.com",
  "https://www.malibutimes.com",
  "https://smdp.com",
  "https://www.fresnostatenews.com",
  "https://www.selmaenterprise.com",
  "https://kerwestnewspapers.com",
  "https://www.sfchronicle.com",
  "https://www.sfexaminer.com",
  "https://www.sanfranciscochinatown.com",
  "https://sfbayview.com",
  "https://www.sacramentopress.com",
  "https://elkgrovetribune.com",
  "https://goldcountrymedia.com",
  "https://citrusheightssentinel.com",
  "https://www.davisenterprise.com",
  "https://www.natomasbuzz.com",
  "https://www.carmichaeltimes.com",
  "https://sacramento.newsreview.com",
  "https://www.mercurynews.com",
  "https://sanjosespotlight.com",
  "https://local.newsbreak.com",
  "https://www.bakersfield.com",
  "https://www.anaheim.net",
  "https://www.independent.com",
  "https://www.santamariasun.com",
  "https://www.goletavoice.com",
  "https://santamariatimes.com",
  "https://lompocrecord.com",
  "https://syvnews.com",
  "https://www.montecitojournal.net",
  "https://dailynexus.com",
  "https://www.longbeachlocalnews.com",
  "https://www.sandiegouniontribune.com",
  "https://timesofsandiego.com",
  "https://www.chulavistatoday.com",
  "https://www.times-advocate.com",
  "https://thecoastnews.com",
  "https://www.thevistapress.com",
  "https://www.sanmarcosrecord.com",
  "https://www.imperialbeachnewsca.com",
  "https://signalscv.com",
  "https://www.dailycommerce.news",
  "https://www.thecamarilloacorn.com",
  "https://www.newsbreak.com",
  "https://vidanewspaper.com",
  "https://www.vcstar.com",
  "https://www.toacorn.com",
  "https://www.simivalleyacorn.com",
  "https://www.fillmoregazette.com",
  "https://www.mpacorn.com",
  "https://www.ojaivalleynews.com"
]

fire_keywords = ['fire', 'smoke', 'blazing', 'wildfire', 'flame', 'burn', 'incendio', 'emergency', 'rescue', 'firefighter']

def is_fire_related(url, soup):

    if any(keyword in url.lower() for keyword in fire_keywords):
        return True

    text_content = soup.get_text().lower()
    if any(keyword in text_content for keyword in fire_keywords):
        return True

    return False

def get_links_from_website(url):
    """Fetch all the URLs from anchor tags on a webpage."""
    try:
        response = requests.get(url, timeout=10)  
        response.raise_for_status()  
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if not is_fire_related(url, soup):
            return url, []  

        links = set()  

        for anchor in soup.find_all('a', href=True):
            link = anchor['href']

            if link.startswith('http'):
                if any(keyword in link.lower() for keyword in fire_keywords):
                    links.add(link)
            elif link.startswith('/'):
                full_link = url + link
                if any(keyword in full_link.lower() for keyword in fire_keywords):
                    links.add(full_link)
        
        return url, list(links)
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return url, []

def main():
    website_data = {}
    
    with ThreadPoolExecutor(max_workers=10) as executor:  
        futures = {executor.submit(get_links_from_website, website): website for website in websites}

        for future in as_completed(futures):
            website = futures[future]
            try:
                url, links = future.result()
                if links:
                    website_data[url] = links
                    print(f"Scraped {len(links)} fire-related links from {url}")
                else:
                    print(f"Skipping {url} (no fire-related content found).")
            except Exception as exc:
                print(f"Error processing {website}: {exc}")

    with open('fire_scraped_urls.json', 'w') as json_file:
        json.dump(website_data, json_file, indent=4)
    
    print("Fire-related URLs have been saved to 'fire_scraped_urls.json'.")

if __name__ == "__main__":
    start_time = time.time()
    main()
    print(f"Scraping completed in {time.time() - start_time:.2f} seconds.")
