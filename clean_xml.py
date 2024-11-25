import xml.etree.ElementTree as ET
import datetime

SITEMAP_FILE = "sitemap.xml"
FIRE_KEYWORDS = ["fire", "burn", "wildfire", "firefighter", "blaze", "inferno", "firefighting", "firestorm", "flames", "arson", "smoke"]

def log(message):
    print(f"[{message}]")

def is_fire_related(url):
    return any(keyword in url.lower() for keyword in FIRE_KEYWORDS)

def is_earlier_than_yesterday(lastmod):
    try:
        lastmod_date = datetime.datetime.strptime(lastmod, "%Y-%m-%dT%H:%M:%S.%f")
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        return lastmod_date < yesterday
    except Exception as e:
        log(f"Error parsing lastmod date: {e}")
        return False

def remove_duplicates_and_non_fire_urls():
    try:
        tree = ET.parse(SITEMAP_FILE)
        root = tree.getroot()
        seen_urls = set()
        urls_to_remove = []

        for url_element in list(root):
            loc_element = url_element.find("loc")
            lastmod_element = url_element.find("lastmod")
            if loc_element is not None and lastmod_element is not None:
                url = loc_element.text.strip()
                lastmod = lastmod_element.text.strip()
                if url in seen_urls or not is_fire_related(url) or not is_earlier_than_yesterday(lastmod):
                    urls_to_remove.append(url_element)
                    log(f"Removed URL: {url} (Duplicate, non-fire-related, or not modified earlier than yesterday)")
                else:
                    seen_urls.add(url)

        for url_element in urls_to_remove:
            root.remove(url_element)

        tree.write(SITEMAP_FILE, encoding="utf-8", xml_declaration=True)
        log("Sitemap updated with duplicates, non-fire-related URLs, and URLs not earlier than yesterday removed.")

    except Exception as e:
        log(f"Error removing duplicates and non-fire URLs: {e}")

if __name__ == "__main__":
    remove_duplicates_and_non_fire_urls()
