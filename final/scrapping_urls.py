


import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# List of websites to scrape (add as many as needed)
# List of websites to scrape
websites = [
    "https://local12.com/search?find=fire",
    "https://www.wtnh.com/?submit&s=fire&orderby=modified",
    "https://www.wtnh.com/page/2/?submit&s=fire&orderby=modified",
    "https://www.wtnh.com/page/3/?submit&s=fire&orderby=modified",
    "https://www.cbs17.com/?submit=&s=fire&orderby=modified",
    "https://www.cbs17.com/page/2/?submit&s=fire&orderby=modified",
    "https://www.cbs17.com/page/3/?submit&s=fire&orderby=modified",
    "https://www.wbir.com/search?q=fire",
    "https://www.wcvb.com/search?q=fire",
    "https://www.knoxnews.com/search/?q=fire",
    "https://westchester.news12.com/search?q=fire",
    "https://news.search.yahoo.com/search;_ylt=Awr49x4ZYo9n_h0Vbm1XNyoA;_ylu=Y29sbwNncTEEcG9zAzEEdnRpZAMEc2VjA3BpdnM-?p=fire&fr2=piv-web&fr=yfp-t",
    "https://www.wfmz.com/search/?tncms_csrf_token=9c51ff51bf2cf19944d9f86af1be6dc76529bf174631622b35291cf8e89a0152.a75fc729d122b8f888ed&l=25&s=start_time&sd=desc&nfl=sponsored%2Cap&f=html&t=article%2Cvideo%2Cyoutube%2Ccollection&app=editorial&nsa=eedition&q=fire",
    "https://news4sanantonio.com/search?find=fire",
    "https://www.wivb.com/?submit=&s=fire",
    "https://www.wivb.com/page/2/?submit&s=fire",
    "https://www.wivb.com/page/3/?submit&s=fire",
    "https://www.nbcconnecticut.com/?s=fire",
    "https://www.alexcityoutlook.com/search/?tncms_csrf_token=38cb207546cbbf67ce54df21e99ec52cc814e062269255bcf55238fb6d1bb16a.bac8c25c99cc38cd1afe&f=html&t=article%2Ccollection%2Cvideo%2Cyoutube&s=start_time&sd=desc&l=100&nsa=eedition&q=fire",
    "https://www.annistonstar.com/search/?tncms_csrf_token=7b3631921dcccd8e84bcec03f6efb2435f130424c58dea543300a0fbd080a5fc.f71cbcec705b30847963&f=html&t=article%2Ccollection%2Cvideo%2Cyoutube&s=start_time&sd=desc&l=50&nsa=eedition&q=fire",
    "https://www.al.com/search/?q=fire",
    "https://cullmantimes.com/",
    "https://www.sfexaminer.com/search/?tncms_csrf_token=6c173170e04fb35026309dedbc0e79e29ccb308ae2bc92b8ae09dc43cd832f98.bf639f5a7fa06d66b3b3&f=html&nfl=WIRE%2C+AP%2Cap&t=article%2Ccollection%2Cvideo%2Cyoutube&s=start_time&sd=desc&l=100&nsa=eedition&q=fire",
    "https://www.decaturdaily.com/search/?tncms_csrf_token=98d0a72c8551bd8539b44da0d36e8ffde159a90030d77c8ef2921eb124cfc803.5b5b8a6ecbcf64716541&f=html&s=start_time&sd=desc&l=100&nsa=eedition&q=fire",
    "https://www.hartselleenquirer.com/?showResults=1&Action=Search&Archive=False&Order=Desc&y=2025&from_date=&to_date=&type_get_category=all&orderby_from_url=most_recent&s=fire",
    "https://www.mountaineagle.com/search/?tncms_csrf_token=3f57e041ea687a1270ef78e6842fa6b85b7bbeb0393e4059a2da83d39a457613.894bd45963433f0afb1c&f=html&t=article%2Ccollection%2Cvideo%2Cyoutube&s=start_time&sd=desc&l=100&nsa=eedition&q=fire",
    "https://thehomewoodstar.com/api/search.html?q=fire&sa=",
    "https://www.thearabtribune.com/search/?tncms_csrf_token=5f10f92161ba234333a90803eda92856e697925b339e78295c91b959c907f284.042826ae48763c554656&f=html&t=article%2Ccollection%2Cvideo%2Cyoutube&s=start_time&sd=desc&l=100&nsa=eedition&q=fire",
    "https://vestaviavoice.com/api/search.html?q=fire&sa=",
    "https://hooversun.com/api/search.html?q=fire&sa=",
   "https://www.themadisonrecord.com/?showResults=1&Action=Search&Archive=False&Order=Desc&y=&from_date=&to_date=&type_get_category=all&orderby_from_url=most_recent&s=fire",
    "https://www.tuscaloosanews.com/search/?q=fire",
    "https://www.birminghamtimes.com/?s=fire",
    "https://www.birminghamtimes.com/page/2/?s=fire",
    "https://www.coventrytelegraph.net/search/?q=fire",
    "https://www.waaytv.com/search/?q=fire",
    "https://www.waaytv.com/search/?tncms_csrf_token=edcec01c09f6cdce362b1f23712365e4ab40fa37e2acf148be402391590fb167.4edfbd9186e3909de5f6&nfl=advertorial&s=start_time&sd=desc&l=100&nsa=eedition&q=fire",
    "https://www.tallasseetribune.com/search/?q=fire",
    "hhttps://www.tallasseetribune.com/search/?tncms_csrf_token=33cf81a0eaacbaa1ef4cb57a3cb7d93d11a0486f916a1c78344f2ea63edf5a56.061543b9791b86f709d1&sd=desc&l=100&nsa=eedition&q=fire",
    "https://www.12news.com/search?q=fire",
    "https://www.phoenixnewtimes.com/phoenix/Search?keywords=fire",
    "https://www.themesatribune.com/search/?q=fire",
    "https://www.tempenews.com/search/?q=fire",
    "https://www.tempenews.com/search/?tncms_csrf_token=b15838982d1bb317b7f565e2b3e40f7fdb3426188b63b31933c81d96e18c7f67.fd818ded5f384b132466&s=start_time&sd=desc&l=100&nsa=eedition&q=fire",
    "https://www.westvalleyview.com/search/?q=fire",
    "https://www.chandlernews.com/search/?q=fire",
    "https://www.glendalestar.com/search/?q=fire",
    "https://www.yourvalley.net/search/?q=fire",
    "https://www.gilbertsunnews.com/search/?q=fire",
    "https://flagscanner.com/?s=fire",
    "https://www.yumanewsnow.com/search/?q=fire",
    "https://www.havasunews.com/search/?q=fire",
    "https://www.tucsonsentinel.com/search/?q=fire",
    "https://www.tucsonlocalmedia.com/search/?q=fire",
    "https://www.gvnews.com/search/?q=fire",
    "https://www.myheraldreview.com",
    "https://www.cityofjacksonville.net",
    "https://www.guardonline.com/",
    "https://www.bentoncourier.com/",
    "https://www.thecabin.net/",
    "https://www.nwaonline.com/",
    "https://thnews.com/",
    "https://harrisondaily.com/",
    "https://www.jonesborosun.com/",
    "https://www.malvern-online.com/",
    "https://www.baxterbulletin.com/",
    "https://www.paragoulddailypress.com/",
    "https://www.whitecountycitizen.com/",
    "https://www.stuttgartdailyleader.com/",
    "https://www.adn.com/",
    "https://www.newsminer.com/",
    "https://www.juneauempire.com/",
    "https://www.ketchikandailynews.com/",
    "https://www.kodiakdailymirror.com/",
    "https://sitkasentinel.com/",
    "https://www.latimes.com",
    "https://www.dailynews.com",
    "https://www.laweekly.com",
    "https://www.ladowntownnews.com",
    "https://www.glendalenewspress.com",
    "https://www.burbankleader.com",
    "https://www.pasadenastarnews.com",
    "https://www.dailybreeze.com",
    "https://malibutimes.com",
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
    "https://goletavoice.com",
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
    "https://www.ojaivalleynews.com",
    "https://santapaulatimes.com",
    "https://www.desertsun.com",
    "https://orangecountytribune.com",
    "https://www.aspendailynews.com/",
    "https://www.dailycamera.com/",
    "https://www.canoncitydailyrecord.com/",
    "https://gazette.com/",
    "https://www.craigdailypress.com/",
    "https://www.durangoherald.com/",
    "https://www.coloradoan.com/",
    "https://www.fortmorgantimes.com/",
    "https://www.summitdaily.com/",
    "https://www.gjsentinel.com/",
    "https://www.greeleytribune.com/",
    "https://www.lajuntatribunedemocrat.com/",
    "https://www.timescall.com/",
    "https://www.reporterherald.com/",
    "https://www.montrosepress.com/",
    "https://www.chieftain.com/",
    "https://www.vaildaily.com/",
    "https://www.ctpost.com/",
    "https://www.bristolpress.com/",
    "https://www.greenwichtime.com/",
    "https://www.newstimes.com/",
    "https://www.courant.com/",
    "https://www.ctinsider.com",
    "https://www.middletownpress.com/",
    "https://www.nhregister.com/",
    "https://theday.com/",
    "https://www.thehour.com/",
    "https://www.norwichbulletin.com/",
    "https://www.stamfordadvocate.com/",
    "https://www.rep-am.com/",
    "https://www.thechronicle.com/",
    "https://baytobaynews.com/",
    "https://www.delawareonline.com/",
    "https://washingtoncitypaper.com",
    "https://www.washingtonpost.com",
    "https://www.washingtonian.com",
    "https://www.heraldtribune.com",
    "https://www.snntv.com",
    "https://www.mysuncoast.com",
    "https://thebradentontimes.com",
    "https://www.bradenton.com",
    "https://cityofbradenton.com",
    "https://www.tampabay.com",
    "https://www.wtsp.com",
    "https://www.tampabeacon.com",
    "https://fortmyers.floridaweekly.com",
    "https://www.miaminewtimes.com",
    "https://www.miamiherald.com",
    "https://www.miamitodaynews.com",
    "https://www.orlandoweekly.com",
    "https://www.cityofcocoabeach.com",
    "https://www.ocala.com",
    "https://www.ocalagazette.com",
    "https://www.jaxdailyrecord.com",
    "https://www.yoursun.com",
    "https://veronews.com",
    "https://www.tcpalm.com",
    "https://www.cityofpsl.com",
    "https://ourtallahassee.com",
    "https://www.news-press.com",
    "https://www.hollywoodreporter.com",
    "https://www.gainesville.com",
    "https://palmbaylive.com",
    "https://www.palmbeachpost.com",
    "https://lakelandtimes.com",
    "https://communitynewspapers.com",
    "https://thegavoice.com",
    "https://www.mdjonline.com",
    "https://patch.com",
    "https://decaturish.com",
    "https://www.augustachronicle.com",
    "https://maconhomepress.com",
    "https://www.savannahtribune.com",
    "https://www.onlineathens.com",
    "https://www.rdrnews.com",
    "https://www.hawaiitribune-herald.com/",
    "https://www.staradvertiser.com/",
    "https://www.westhawaiitoday.com/",
    "https://www.thegardenisland.com/",
    "https://www.mauinews.com/",
    "https://cdapress.com/",
    "https://www.postregister.com/",
    "https://www.lmtribune.com/",
    "https://www.idahopress.com/",
    "https://www.idahostatejournal.com/",
    "https://shoshonenewspress.com/",
    "https://magicvalley.com",
    "https://www.news-gazette.com",
    "https://capitolnewsillinois.com",
    "https://www.chicagotribune.com",
    "https://www.thewoodstockindependent.com",
    "https://www.dailyherald.com",
    "https://www.positivelynaperville.com",
    "https://www.vevaynewspapers.com",
    "https://www.madisoncourier.com",
    "https://www.indystar.com",
    "https://www.ibj.com",
    "https://apnews.com",
    "https://www.tristatehomepage.com",
    "https://www.courierpress.com",
    "https://www.greaterfortwayneinc.com",
    "https://bloomingtonian.com",
    "https://ground.news",
    "https://www.kokomotribune.com",
    "https://www.tribstar.com",
    "https://andersonian.com",
    "https://www.amestrib.com/",
    "https://www.swiowanewssource.com/",
    "https://www.mississippivalleypublishing.com/the_hawk_eye/",
    "https://carrollspaper.com/",
    "https://www.thegazette.com/",
    "https://www.ottumwacourier.com/",
    "https://www.charlescitypress.com/",
    "https://www.chronicletimes.com/",
    "https://www.clintonherald.com/",
    "https://spectrumnews1.com",
    "https://www.courier-journal.com",
    "https://www.pmg-ky1.com",
    "https://www.wave3.com",
    "https://bgdailynews.com",
    "https://www.richmondregister.com",
    "https://linknky.com",
    "https://www.dailyindependent.com/",
    "https://bgdailynews.com/",
    "https://www.thetimestribune.com/",
    "https://www.amnews.com/",
    "https://www.thenewsenterprise.com/",
    "https://www.state-journal.com/",
    "https://www.harlanenterprise.net/",
    "https://www.thegleaner.com/",
    "https://www.kentuckynewera.com/",
    "https://www.middlesboronews.com/",
    "https://www.the-messenger.com/",
    "https://www.theadvocate.com",
    "https://www.brproud.com",
    "https://theneworleanstribune.com",
    "https://www.gretnaguide.com",
    "https://www.thestbernardvoice.com",
    "https://covingtonweekly.com",
    "https://www.hammondstar.com",
    "https://www.plaqueminesgazette.com",
    "https://www.kenner.la.us",
    "https://thedailyiberian.com",
    "https://www.centralmaine.com/",
    "https://www.bangordailynews.com/",
    "https://www.pressherald.com/times-record/",
    "https://www.sunjournal.com/",
    "https://www.baltimoresun.com",
    "https://baltimoretimes-online.com",
    "https://www.thebaltimorebanner.com",
    "https://gaithersburgpost.town.news",
    "https://www.marylandmatters.org",
    "https://www.middletownpress.com/",
    "https://www.thecitizen.com/",
    "https://www.delmarvanow.com/",
    "https://www.dailypress.com",
    "https://www.dailypress.com/",
    "https://www.fairfaxtimes.com",
    "https://www.clarionledger.com",
    "https://www.magnoliareporter.com",
    "https://www.nwahomepage.com",
    "https://www.nwnews.com",
    "https://www.pennlive.com",
    "https://www.thedailyreview.com",
    "https://www.delcotimes.com",
    "https://www.spotlightpa.org",
    "https://www.nj.com",
    "https://www.newjerseyherald.com",
    "https://www.pressofatlanticcity.com"
]


# List of fire-related keywords
fire_keywords = [
    'fire', 'smoke', 'blazing', 'wildfire', 'flame', 'burn', 'incendio', 'emergency', 'rescue',
    'firefighter', 'explosion', 'heat', 'combustion', 'arson', 'burning', 'evacuation', 'hazard',
    'inferno', 'wildfires', 'flames', 'firestorm', 'fumes', 'cinder', 'ashes', 'charred',
    'fireman', 'firefighting', 'firetruck', 'firehouse', 'fire department', 'firefighters', 'control burn',
    'scorched', 'fire safety', 'heatwave', 'evacuate', 'burnt', 'forest fire', 'smoldering', 'fire escape',
    'hazardous', 'combustible', 'extinguisher', 'extinguish', 'emergency services', 'heatstroke', 'fireball',
    'cremation', 'fire hazard', 'emergency response', 'ignition', 'overheating', 'fire drill', 'wildfire smoke',
    'flame retardant', 'fireproof', 'flameout', 'spontaneous combustion', 'fire alarm', 'arsonist', 'firetrap',
    'controlled burn', 'firebreak', 'flash fire', 'burnout', 'ignitable', 'gasoline', 'flame thrower', 'wildfire risk',
    'burn victim', 'ash', 'heat exhaustion', 'fire safety tips', 'fire danger', 'firewatch', 'fire lines',
    'pyro', 'cauterize', 'thermal burn', 'wildfire containment', 'fire-related injuries', 'carbon monoxide',
    'fire-fighting equipment', 'forest firefighting', 'blowtorch', 'fire suppressant', 'fire code', 'fire marshal',
    'emergency evacuation', 'rescue mission', 'boil over', 'flare', 'smoke inhalation', 'fire hazard mitigation',
    'spontaneous ignition', 'overheated', 'fireline', 'heating oil', 'flue fire', 'pilot light', 'flashover',
    'controlled fire', 'fire risk assessment', 'fire prevention', 'fire spread', 'heat-resistant', 'flammable',
    'ignition point', 'fire drill procedure', 'gas leak', 'tinder', 'backburn', 'wet fire', 'fire intensity',
    'house fire', 'fire service', 'hotspot', 'smoking ban', 'safety protocols', 'evacuations order',
    'burning embers', 'fire response', 'fire outbreak', 'fire damage', 'high heat', 'fire cloud', 'flash fire risk'
]

# Add multiple user-agent strings to rotate between
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59 Safari/537.36',
    'Mozilla/5.0 (Linux; Android 10; Pixel 3 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36'
]

# Randomly choose a User-Agent for each request
def get_random_user_agent():
    return random.choice(user_agents)

# Set headers to include random User-Agent
headers = {
    'User-Agent': get_random_user_agent(),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Referer': 'https://www.google.com/',
}

# Check if the page has fire-related content
def is_fire_related(url, soup):
    if any(keyword in url.lower() for keyword in fire_keywords):
        return True

    text_content = soup.get_text().lower()
    if any(keyword in text_content for keyword in fire_keywords):
        return True

    return False

# Function to get links from a website
def get_links_from_website(url):
    retries = 3
    for i in range(retries):
        try:
            # Make a request to the website
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # This will raise an exception for 4xx/5xx errors

            soup = BeautifulSoup(response.text, 'html.parser')

            # If the content is not fire-related, skip it
            if not is_fire_related(url, soup):
                return url, []

            base_url = response.url  # Get the base URL of the page
            links = set()

            # Extract all anchor tags with href attribute
            for anchor in soup.find_all('a', href=True):
                link = anchor['href']
                # Convert relative URLs to absolute URLs
                full_url = urljoin(base_url, link)
                clean_link = full_url.split('?')[0]  # Remove query parameters

                # Only add fire-related links
                if any(keyword in clean_link.lower() for keyword in fire_keywords):
                    links.add(clean_link)

            return url, list(links)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            if i < retries - 1:
                wait_time = random.randint(5, 10)  # Wait between 5 and 10 seconds
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                return url, []

# Main function to scrape all websites concurrently
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

    # Save the results to a JSON file
    with open('fire_urls.json', 'w') as json_file:
        json.dump(website_data, json_file, indent=4)

    print("Fire-related URLs have been saved to 'fire_urls.json'.")

if __name__ == "__main__":
    start_time = time.time()
    main()
    print(f"Scraping completed in {time.time() - start_time:.2f} seconds.")
