#!/usr/bin/env python3
"""
Enhanced Fire Scraper with SSL bypass and better detection
"""

import asyncio
import aiohttp
import requests
import time
import random
import json
import re
import ssl
import urllib3
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional
import os
from pathlib import Path

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# HTML parsing
from bs4 import BeautifulSoup
import lxml

# Anti-detection
import cloudscraper
from fake_useragent import UserAgent

# Content extraction
import trafilatura
from readability import Document

# News websites to scrape (focusing on ones that worked)
WORKING_WEBSITES = [
    # Original working websites
    "https://www.hernandosun.com/",
    "https://www.theclaycountynews.com/",
    "https://www.dailyunion.com/",
    "https://marioncountynow.com/",
    "https://www.waltontribune.com/",
    "https://carrollspaper.com/",
    "https://www.hartington.net/",
    "https://www.charitonleader.com/",
    "https://christiancountynow.com/",
    "https://www.southdadenewsleader.com/",
    "https://www.douglascountysentinel.com/",
    "https://www.dddnews.com/",
    "https://greenecountynewsonline.com/",
    "https://www.grundycountyherald.com/",
    "https://hickoryrecord.com/",
    "https://ironcountytoday.com/",
    "https://linncountynews.net/",
    "https://www.thelcn.com/",
    "https://mdcp.nwaonline.com/",
    "https://www.maconcountychronicle.com/",
    "https://mercercountyoutlook.net/",
    "https://www.perrytribune.com/",
    "https://www.phelpscountyfocus.com/",
    "https://www.polkio.com/",
    "https://www.stfrancoisherald.com/",
    "https://www.stegenherald.com/",
    "https://www.schuylercountytimes.com/",
    "https://www.shelbycountyreporter.com/",
    "https://www.stonecountyenterprise.com/",
    "https://www.webstercountycitizen.com/",
    
    # New working websites from testing
    "https://www.baxleynewsbanner.com",
    "https://www.thebrunswicknews.com",
    "https://www.valdostadailytimes.com",
    "https://www.timesenterprise.com",
    "https://www.tiftongazette.com",
    "https://www.southeastsun.com",
    "https://www.northgeorgianews.com",
    "https://www.thepress-sentinel.com",
    "https://www.whitecountynews.net",
    "https://www.andrewscountynews.com",
    "https://www.bexar.org/CivicAlerts.aspx",
    "https://www.bowiecountynow.com/",
    "https://www.brazoscountytx.gov/156/News",
    "https://www.burnetbulletin.com/",
    "https://www.pittsburgnews.com",
    "https://www.casscountynow.com/",
    "https://www.thecherokeean.com/",
    "https://www.colemantoday.com/",
    "https://www.coloradocountycitizen.com/",
    "https://www.thecomanchechief.com/news/county_news/",
    "https://www.cranenews.com",
    "https://crockettcountytimes.com/",
    "https://www.deltacountyindependent.com/",
    "https://www.dentoncounty.gov/156/News",
    "https://www.cuerorecord.com",
    "https://www.clarendonlive.com",
    "https://www.fayettecountyrecord.com/",
    "https://www.fortbendcountytx.gov/news",
    "https://freestonecountytimesonline.com/",
    "https://www.galvestontx.gov/156/Notify-Me",
    "https://www.fredericksburgstandard.com",
    "https://www.gonzalesinquirer.com",
    "https://www.hardincoindependent.com/category/news/",
    "https://www.thehendersonnews.com/",
    "https://www.hidalgocounty.us/156/News",
    "https://www.co.hood.tx.us/156/News",
    "https://www.bigspringherald.com",
    "https://www.jacksboronewspapers.com",
    "https://www.victoriaadvocate.com",
    "https://www.mysoutex.com",
    "https://kerrcountylead.com/",
    "https://www.junctioneagle.com",
    "https://www.kinneycountypost.com/",
    "https://www.knoxcountynewsonline.com/",
    "https://www.llanonews.com",
    "https://www.martincountymessenger.com/",
    "https://www.masoncountynews.com",
    "https://themavericktimesnews.com/",
    "https://www.bradystandard.com",
    "https://www.menardnews.com",
    "https://www.co.midland.tx.us/156/News",
    "https://www.rockdalereporter.com",
    "https://www.moorecountynews.com",
    "https://www.newtoncountytimes.com",
    "https://orangeleader.com/",
    "https://www.mineralwellsindex.com",
    "https://www.panolawatchman.com/",
    "https://www.parkercountytx.com/156/News",
    "https://www.pottercountynews.com/",
    "https://www.sansabanews.com",
    "https://www.snyderdailynews.com",
    "https://www.albanynewsnow.com",
    "https://scttx.com/news",
    "https://www.shermancotimes.com",
    "https://www.brownfieldonline.com",
    "https://www.traviscountytx.gov/news",
    "https://www.trinitycountynews.com",
    "https://www.uvaldeleadernews.com",
    "https://www.vanzandtnews.com",
    "https://www.itemonline.com",
    "https://www.journal-spectator.com/",
    "https://www.wilco.org/news",
    "https://www.wilsoncountynews.com/",
    "https://www.wcmessenger.com/",
    "https://www.woodcountymonitor.com/",
    "https://www.crystalcitynews.com",
    
    # Major National News Outlets
    "https://www.cnn.com/search?q=fire",
    "https://www.foxnews.com/search-results/search?q=fire",
    "https://www.nbcnews.com/search/?q=fire",
    "https://www.cbsnews.com/search/?q=fire",
    "https://www.abcnews.go.com/search?q=fire",
    "https://www.nytimes.com/search?query=fire",
    "https://www.latimes.com/search?q=fire",
    "https://www.chicagotribune.com/search/?q=fire",
    "https://www.boston.com/search/?q=fire",
    "https://www.dallasnews.com/search/?q=fire",
    "https://www.washingtonpost.com",
    "https://www.usatoday.com",
    "https://www.reuters.com",
    "https://www.apnews.com",
    "https://www.bbc.com/news",
    
    # Local TV News Stations and Regional News
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
    "https://www.wfmz.com/search/?q=fire",
    "https://news4sanantonio.com/search?find=fire",
    "https://www.wivb.com/?submit=&s=fire",
    "https://www.nbcconnecticut.com/?s=fire",
    "https://www.al.com/search/?q=fire",
    "https://cullmantimes.com/",
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
    "https://www.kodiakdailymirror.com/search/?q=fire",
    "https://sitkasentinel.com/search/?q=fire",
    "https://www.dailynews.com/search/?q=fire",
    "https://www.laweekly.com/search/?q=fire",
    "https://www.ladowntownnews.com/search/?q=fire",
    "https://www.glendalenewspress.com/search/?q=fire",
    "https://www.burbankleader.com/search/?q=fire",
    "https://www.pasadenastarnews.com/search/?q=fire",
    "https://www.dailybreeze.com/?s=fire&orderby=date&order=desc",
    "https://malibutimes.com/?s=fire",
    "https://smdp.com/?s=fire",
    "https://www.fresnostatenews.com//?s=fire",
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
    "https://www.thewoodstockindependent.com",
    "https://www.dailyherald.com",
    "https://www.positivelynaperville.com",
    "https://www.vevaynewspapers.com",
    "https://www.madisoncourier.com",
    "https://www.indystar.com",
    "https://www.ibj.com",
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
    "https://www.thecitizen.com/",
    "https://www.delmarvanow.com/",
    "https://www.dailypress.com",
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
    "https://www.pressofatlanticcity.com",
    "https://winknews.com/",
    "https://www.wric.com/",
    "https://www.us977.com/",
    "https://www.wdtn.com/",
    "https://cbs12.com/",
    "https://www.wbrc.com/",
    "https://www.mississippivalleypublishing.com/",
    "https://signalakron.org/",
    "https://jgpr.net/",
    "https://katu.com/",
    "https://abc7ny.com/",
    "https://abc6onyourside.com/",
    "https://www.wtkr.com/",
    "https://www.clickorlando.com/",
    "https://www.9news.com/",
    "https://www.wane.com/",
    "https://www.yahoo.com/news/",
    "https://www.wave3.com/",
    "https://www.tribstar.com/",
    "https://www.dailyherald.com/",
    "https://gazette.com/",
    "https://syvnews.com/",
    "https://lompocrecord.com/",
    "https://www.12onyourside.com/",
    "https://local12.com/",
    "https://www.live5news.com/",
    "https://www.fox5atlanta.com/",
    "https://www.wgem.com/",
    "https://www.fox35orlando.com/",
    "https://www.wpri.com/",
    "https://fox59.com/",
    "https://www.whas11.com/",
    "https://www.wlky.com/",
    "https://www.theolympian.com/",
    "https://www.wtnh.com/",
    "https://www.cbsnews.com/",
    "https://www.wkrn.com/",
    "https://cnycentral.com/",
    "https://www.dcnewsnow.com/",
    "https://fox17.com/",
    "https://www.nbc4i.com/",
    "https://www.lubbockonline.com/",
    "https://www.13wmaz.com/",
    "https://www.valleynewslive.com/",
    "https://ktla.com/",
    "https://www.abc10.com/",
    "https://www.wtva.com/",
    "https://abc7chicago.com/",
    "https://www.news4jax.com/",
    "https://www.yahoo.com/",
    "https://www.kiiitv.com/",
    "https://www.wfmynews2.com/",
    "https://smokeybarn.com/",
    "https://www.khou.com/",
    "https://www.wapt.com/",
    "https://brooklyn.news12.com/",
    "https://www.fox5vegas.com/",
    "https://news3lv.com/",
    "https://thegeorgiasun.com/",
    "https://www.expressnews.com/",
    "https://wbontv.com/",
    "https://www.pahomepage.com/",
    "https://kfor.com/",
    "https://abc7amarillo.com/",
    "https://www.kltv.com/",
    "https://abc6onyourside.com/th",
    "https://www.firstalert4.com/",
    "https://www.silive.com/",
    "https://www.star-telegram.com/",
    "https://www.whec.com/",
    "https://www.wsoctv.com/",
    "https://www.11alive.com/",
    "https://www.wbir.com/",
    "https://mendofever.com/",
    "https://fox11online.com/",
    "https://www.wfaa.com/",
    "https://www.wavy.com/",
    "https://www.courier-journal.com/",
    "https://www.koco.com/",
    "https://idahonews.com/",
    "http://northernnewsnow.com/",
    "https://www.12newsnow.com/",
    "https://www.kron4.com/",
    "https://www.fox4news.com/",
    "https://www.wsfa.com/",
    "https://krdo.com/",
    "https://www.azfamily.com/",
    "https://www.wbay.com/",
    "https://www.ksn.com/",
    "https://www.wnct.com/",
    "https://www.dailypress.com/",
    "https://www.klkntv.com/",
    "https://www.wcax.com/",
    "https://www.newschannel10.com/",
    "https://www.wkyt.com/",
    "https://tucson.com/",
    "https://www.wmtw.com/",
    
    # Additional Georgia and Regional News Sites
    "https://www.atkinsoncitizennews.com",
    "https://www.almatimes.com",
    "https://bakercountypress.com/",
    "https://baldwintimes.com/",
    "https://www.thebankspost.com",
    "https://www.mainstreetnews.com/barrow/"
]

# Fire-related keywords (expanded)
FIRE_KEYWORDS = [
    'fire', 'blaze', 'inferno', 'conflagration', 'arson', 'smoke', 'flame',
    'burning', 'firefighter', 'fire department', 'fire station', 'fire truck',
    'wildfire', 'forest fire', 'brush fire', 'house fire', 'building fire',
    'fire alarm', 'fire safety', 'fire prevention', 'fire investigation',
    'fire marshal', 'fire chief', 'fire engine', 'fire hydrant', 'fire escape',
    'fire drill', 'fire code', 'fire damage', 'fire restoration', 'fire insurance',
    'emergency', 'rescue', 'evacuation', 'sprinkler', 'smoke detector',
    'fireworks', 'explosion', 'combustion', 'ignition', 'extinguisher'
]

class EnhancedFireScraper:
    """Enhanced fire news scraper with SSL bypass and better detection"""
    
    def __init__(self):
        self.ua = UserAgent()
        
        # Create scraper with SSL bypass
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        # Create session with SSL bypass
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.scraped_urls = set()
        self.articles = []
        
        # Create output directory
        self.output_dir = Path('scraped_articles')
        self.output_dir.mkdir(exist_ok=True)
        
        print("🔥 Enhanced Fire Scraper initialized")

    def _is_fire_related(self, text: str) -> float:
        """Check if content is fire-related with lower threshold"""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        keyword_matches = sum(1 for keyword in FIRE_KEYWORDS if keyword in text_lower)
        score = keyword_matches / len(FIRE_KEYWORDS)
        
        # Lower threshold - any fire keyword match gets a score
        if keyword_matches > 0:
            score = max(score, 0.2)  # Minimum score for any fire keyword
        
        return min(score, 1.0)

    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract publication date"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
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
            'meta[name="date"]',
            '.news-date',
            '.story-date'
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
                        for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%B %d, %Y', '%m/%d/%Y', '%d/%m/%Y']:
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
                if extracted and len(extracted) > 50:  # Lower minimum length
                    metadata = trafilatura.extract_metadata(html, url)
                    fire_score = self._is_fire_related(extracted)
                    
                    if fire_score > 0.1:  # Lower threshold
                        return {
                            'title': metadata.get('title', ''),
                            'content': extracted,
                            'date': self._extract_date(soup),
                            'fire_score': fire_score
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
                    if len(text_content) > 50:
                        fire_score = self._is_fire_related(text_content)
                        
                        if fire_score > 0.1:
                            return {
                                'title': doc.title(),
                                'content': text_content,
                                'date': self._extract_date(soup),
                                'fire_score': fire_score
                            }
            except Exception:
                pass
            
            # Method 3: Manual extraction with fire keyword search
            try:
                # Look for fire-related content in the entire page
                page_text = soup.get_text().lower()
                fire_score = self._is_fire_related(page_text)
                
                if fire_score > 0.1:
                    content_selectors = ['article', '.article-content', '.post-content', '.content', 'main', '.story-content']
                    for selector in content_selectors:
                        content_element = soup.select_one(selector)
                        if content_element:
                            text_content = content_element.get_text().strip()
                            if len(text_content) > 50:
                                title_element = soup.select_one('h1, .title, .headline, .story-title')
                                title = title_element.get_text().strip() if title_element else ""
                                
                                return {
                                    'title': title,
                                    'content': text_content,
                                    'date': self._extract_date(soup),
                                    'fire_score': fire_score
                                }
            except Exception:
                pass
            
        except Exception as e:
            print(f"Content extraction failed for {url}: {e}")
        
        return None

    async def _scrape_url(self, url: str) -> Optional[Dict]:
        """Scrape a single URL with SSL bypass"""
        if url in self.scraped_urls:
            return None
        
        self.scraped_urls.add(url)
        
        try:
            # Random delay
            await asyncio.sleep(random.uniform(1, 2))
            
            # Try with SSL bypass first
            try:
                response = self.session.get(url, timeout=30, verify=False)
            except Exception:
                # Fallback to cloudscraper
                response = self.scraper.get(url, timeout=30)
            
            if response.status_code == 200:
                content_data = self._extract_content(response.text, url)
                
                if content_data:
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
            # Try with SSL bypass first
            try:
                response = self.session.get(base_url, timeout=30, verify=False)
            except Exception:
                # Fallback to cloudscraper
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
                article_urls = list(set(article_urls))[:30]  # Increased limit
                
        except Exception as e:
            print(f"Failed to find articles on {base_url}: {e}")
        
        return article_urls

    def _is_article_url(self, url: str, base_url: str) -> bool:
        """Check if URL is likely an article URL"""
        parsed = urlparse(url)
        base_parsed = urlparse(base_url)
        
        if parsed.netloc != base_parsed.netloc:
            return False
        
        # More flexible article patterns
        article_patterns = [
            r'/article/', r'/news/', r'/story/', r'/post/', r'/entry/',
            r'/202[0-9]/', r'/20[0-9]{2}/', r'/\d{4}/\d{2}/', r'/\d{4}-\d{2}/',
            r'/local/', r'/community/', r'/breaking/', r'/latest/',
            r'\.html$', r'\.php$', r'\.aspx$'
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
                semaphore = asyncio.Semaphore(3)  # Reduced concurrent requests
                
                async def scrape_with_semaphore(url):
                    async with semaphore:
                        return await self._scrape_url(url)
                
                tasks = [scrape_with_semaphore(url) for url in article_urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Filter successful results
                website_articles = [r for r in results if r is not None and not isinstance(r, Exception)]
                self.articles.extend(website_articles)
                
                print(f"   ✅ Scraped {len(website_articles)} fire-related articles")
                
                # Show some details about found articles
                for article in website_articles[:3]:  # Show first 3
                    print(f"      🔥 {article['title'][:60]}... (Score: {article['fire_related_score']:.2f})")
                
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
    print("🔥 Enhanced Fire News Scraper Starting...")
    print("🔧 Features: SSL bypass, lower thresholds, better detection")
    
    scraper = EnhancedFireScraper()
    
    try:
        articles = await scraper.scrape_websites(WORKING_WEBSITES)
        
        if articles:
            print("\n🔥 Top 10 articles by fire relevance score:")
            sorted_articles = sorted(articles, key=lambda x: x['fire_related_score'], reverse=True)
            for i, article in enumerate(sorted_articles[:10], 1):
                print(f"{i}. {article['title'][:80]}... (Score: {article['fire_related_score']:.2f})")
                print(f"   Source: {article['source']}")
                print(f"   URL: {article['url']}")
                print()
        else:
            print("\n❌ No fire-related articles found. This could mean:")
            print("   - No fire incidents reported yesterday")
            print("   - Sites are blocking automated access")
            print("   - Content structure has changed")
            print("   - Fire-related content uses different keywords")
        
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n🏁 Scraper finished.")

if __name__ == "__main__":
    asyncio.run(main())