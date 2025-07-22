import requests
import json
from datetime import datetime, timedelta
import time

def fetch_coventrytelegraph_articles():
    """Fetch fire-related articles from Coventry Telegraph API"""
    
    base_url = "https://api.mantis-intelligence.com/reach/search"
    params = {
        'search_text_all': 'fire',
        'search_text': '',
        'search_text_none': '',
        'mantis_categories': '',
        'tags': '',
        'domains': 'coventrytelegraph',
        'excluded_domains': '',
        'author': '',
        'start': 0,
        'limit': 100,
        'sort': 'date',
        'indexAlias': '12-months'
    }
    
    # Current date and yesterday's date for filtering
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    def is_today_or_yesterday(date_string):
        try:
            # Parse the ISO date string from Coventry Telegraph API
            date_obj = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ")
            return date_obj.date() == today.date() or date_obj.date() == yesterday.date()
        except ValueError:
            # Try alternative format without milliseconds
            try:
                date_obj = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
                return date_obj.date() == today.date() or date_obj.date() == yesterday.date()
            except ValueError:
                return False
    
    all_articles = []
    total_articles = 0
    page = 0
    
    while True:
        params['start'] = page * 100
        
        try:
            response = requests.get(base_url, params=params)
            
            if response.status_code != 200:
                print(f"Failed to retrieve data. Status code: {response.status_code}")
                break
                
            data = response.json()
            
            # Get total number of articles for first page
            if page == 0:
                total_articles = data.get('totalNumberofArticlesMatched', 0)
                print(f"Total articles found: {total_articles}")
            
            articles = data.get('articleData', [])
            
            if not articles:
                break
                
            # Filter articles by date and process
            for article in articles:
                published_date = article.get('publishedDate')
                if published_date and is_today_or_yesterday(published_date):
                    # Process article data
                    processed_article = {
                        'title': article.get('title', ''),
                        'leadText': article.get('leadText', ''),
                        'url': article.get('url', ''),
                        'publishedDate': published_date,
                        'author': article.get('author', ''),
                        'imageThumbnail': article.get('imageThumbnail', ''),
                        'score': article.get('score', 0),
                        'source': 'Coventry Telegraph'
                    }
                    
                    # Ensure the URL has the proper protocol
                    if processed_article['url'] and not processed_article['url'].startswith('http'):
                        processed_article['url'] = f"https://{processed_article['url']}"
                    
                    all_articles.append(processed_article)
            
            print(f"Processed page {page + 1}, found {len(articles)} articles, filtered to {len([a for a in all_articles if a['source'] == 'Coventry Telegraph'])} recent articles")
            
            # If we've processed all articles or no more articles, break
            if len(articles) < 100 or (page + 1) * 100 >= total_articles:
                break
                
            page += 1
            
            # Add a small delay to be respectful to the API
            time.sleep(1)
            
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break
    
    return all_articles

def save_articles(articles, filename=None):
    """Save articles to JSON file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"coventrytelegraph_fire_articles_{timestamp}.json"
    
    output_data = {
        'source': 'Coventry Telegraph',
        'search_query': 'fire',
        'total_articles': len(articles),
        'fetch_date': datetime.now().isoformat(),
        'articles': articles
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    
    print(f"Saved {len(articles)} articles to {filename}")
    return filename

if __name__ == "__main__":
    print("Fetching fire-related articles from Coventry Telegraph...")
    articles = fetch_coventrytelegraph_articles()
    
    if articles:
        filename = save_articles(articles)
        print(f"\nSummary:")
        print(f"- Total articles found: {len(articles)}")
        print(f"- Articles from today/yesterday: {len(articles)}")
        print(f"- Saved to: {filename}")
        
        # Print first few articles as preview
        print(f"\nFirst 3 articles:")
        for i, article in enumerate(articles[:3]):
            print(f"{i+1}. {article['title']}")
            print(f"   Published: {article['publishedDate']}")
            print(f"   URL: {article['url']}")
            print()
    else:
        print("No articles found.") 