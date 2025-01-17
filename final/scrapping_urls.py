import requests
from bs4 import BeautifulSoup
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

websites = [
    "https://www.cbsnews.com/",
    "https://local12.com/",
    "https://www.wtnh.com/",
    "https://www.cbs17.com/",
    "https://abc7.com/",
    "https://www.wbir.com/",
    "https://www.wcvb.com/",
    "https://www.knoxnews.com/",
    "https://westchester.news12.com/",
    "https://www.yahoo.com/",
    "https://www.wfmz.com/",
    "https://news4sanantonio.com/",
    "https://www.wivb.com/",
    "https://www.nbcconnecticut.com/",
    "https://www.alexcityoutlook.com/",
    "https://www.annistonstar.com/",
    "https://www.al.com/",
    "https://cullmantimes.com/",
    "https://www.sfexaminer.com/",
    "https://www.decaturdaily.com/",
    "https://www.hartselleenquirer.com/",
    "https://www.mountaineagle.com/",
    "https://thehomewoodstar.com",
    "https://www.thearabtribune.com",
    "https://vestaviavoice.com",
    "https://hooversun.com",
    "https://www.themadisonrecord.com",
    "https://www.tuscaloosanews.com",
    "https://www.birminghamtimes.com",
    "https://www.coventrytelegraph.net",
    "https://www.waaytv.com",
    "https://www.tallasseetribune.com",
    "https://www.12news.com",
    "https://www.phoenixnewtimes.com",
    "https://www.themesatribune.com",
    "https://www.tempenews.com",
    "https://www.westvalleyview.com",
    "https://www.chandlernews.com",
    "https://www.glendalestar.com",
    "https://www.yourvalley.net",
    "https://www.gilbertsunnews.com",
    "https://flagscanner.com",
    "https://www.yumanewsnow.com",
    "https://www.havasunews.com",
    "https://www.tucsonsentinel.com",
    "https://www.tucsonlocalmedia.com",
    "https://www.gvnews.com",
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

    with open('fire_urls.json', 'w') as json_file:
        json.dump(website_data, json_file, indent=4)
    
    print("Fire-related URLs have been saved to 'fire_scraped_urls.json'.")

if __name__ == "__main__":
    start_time = time.time()
    main()
    print(f"Scraping completed in {time.time() - start_time:.2f} seconds.")
