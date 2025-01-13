from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import requests
from bs4 import BeautifulSoup
from app.models import Article, Website
from app.database import get_db

router = APIRouter()

def fetch_news_from_site(url, search_term="fire"):
    try:
        response = requests.get(url)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []

        for link_tag in soup.find_all('a', href=True):
            link_text = link_tag.get_text(strip=True).lower()
            link_url = link_tag['href']
            if search_term.lower() in link_text or search_term.lower() in link_url:
                title = link_text
                description = "No description available"
                published_date = "Not available"
                
                parent = link_tag.find_parent(['article', 'section', 'div'])
                if parent:
                    description_tag = parent.find('p') or parent.find('span')
                    if description_tag:
                        description = description_tag.get_text(strip=True)
                    
                    date_tag = parent.find('time')
                    if date_tag and date_tag.get('datetime'):
                        published_date = date_tag['datetime']
                
                articles.append({
                    'title': title,
                    'link': link_url,
                    'description': description,
                    'published_date': published_date
                })

        return articles
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data from {url}: {str(e)}")

def crawl_and_store_articles(db: Session, search_term="fire"):
    websites = db.query(Website).all()
    if not websites:
        raise HTTPException(status_code=404, detail="No websites found in the database.")

    for website in websites:
        if not website.news_link:
            print(f"Skipping website with ID {website.id}: No news link provided.")
            continue

        print(f"Fetching news from {website.news_link}...")
        try:
            articles = fetch_news_from_site(website.news_link, search_term=search_term)

            for article in articles:
                exists = db.query(Article).filter_by(url=article['link']).first()
                if exists:
                    print(f"Article with link {article['link']} already exists. Skipping...")
                    continue

                new_article = Article(
                    title=article['title'],
                    website_name=website.news_link,  
                    url=article['link'],
                    summary=article['description'],
                    date=article['published_date'],
                    author=None  
                )
                db.add(new_article)
            db.commit()
            print(f"Successfully stored articles from {website.news_link}.")

        except HTTPException as http_exc:
            print(f"Error processing website {website.news_link}: {http_exc.detail}")
        except Exception as e:
            db.rollback()
            print(f"Error processing website {website.news_link}: {e}")

@router.post("/crawl-news", status_code=200)
def crawl_news(search_term: str = "fire", db: Session = Depends(get_db)):
    """
    API endpoint to trigger crawling news from websites.
    
    Args:
        search_term (str): The search term to use (default is "fire").
        db (Session): Database session dependency.
    """
    try:
        crawl_and_store_articles(db, search_term=search_term)
        return {"message": "News articles crawled and stored successfully."}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
