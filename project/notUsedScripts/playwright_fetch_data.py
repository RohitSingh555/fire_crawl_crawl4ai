from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

url = "https://www.google.co.uk/search?q=fire&as_sitesearch=www.theguardian.com"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url)
    page.wait_for_timeout(5000)  
    html_content = page.content()
    soup = BeautifulSoup(html_content, "html.parser")
    main_content = soup.find_all(['article', 'section', 'div', 'ul'], class_=['news-item', 'story', 'content', 'main-content', 'search-results'])
    if not main_content:
        print("No relevant content found, trying to extract all visible text...")
        main_content = soup.find_all(['p', 'h1', 'h2', 'h3', 'a','span'])

    body_str = ""
    for content in main_content:
        body_str += str(content)

    with open("output_relevant_news.xml", "w", encoding="utf-8") as xml_file:
        xml_file.write(body_str)

    print(body_str)

    browser.close()
