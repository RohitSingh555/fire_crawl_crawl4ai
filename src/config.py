#!/usr/bin/env python3
"""
Configuration module for Advanced Fire Scraper
"""

import yaml
from typing import Dict, Any

def load_config(config_path: str = "scraper_config.yaml") -> Dict[str, Any]:
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
        print(f"Config file {config_path} not found, using defaults")
        return default_config

# Fire-related keywords for content filtering
FIRE_KEYWORDS = [
    'fire', 'blaze', 'inferno', 'conflagration', 'arson', 'smoke', 'flame',
    'burning', 'firefighter', 'fire department', 'fire station', 'fire truck',
    'wildfire', 'forest fire', 'brush fire', 'house fire', 'building fire',
    'fire alarm', 'fire safety', 'fire prevention', 'fire investigation',
    'fire marshal', 'fire chief', 'fire engine', 'fire hydrant', 'fire escape',
    'fire drill', 'fire code', 'fire damage', 'fire restoration', 'fire insurance'
]

# List of news websites to scrape
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