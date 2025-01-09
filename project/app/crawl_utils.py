from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import time
from fastapi import Depends
from sqlalchemy.orm import Session
from .models import Article, FireRelatedArticle, Website
from .database import get_db


def fetch_news_from_site(url, search_term="fire"):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(url + search_term)
    time.sleep(3)
    
    articles = []

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    for item in soup.find_all('article'):
        title_tag = item.find('h2')
        if title_tag:
            title = title_tag.get_text(strip=True)
            link = title_tag.find('a')['href']
            description = item.find('p').get_text(strip=True) if item.find('p') else 'No description available'
            
            published_date = "Not available"
            date_tag = item.find('time')
            if date_tag and date_tag.get('datetime'):
                published_date = date_tag['datetime']

            articles.append({
                'Title': title,
                'Link': link,
                'Description': description,
                'Published Date': published_date
            })

    driver.quit()
    return articles

def save_raw_article(db: Session, article_data: dict):
    db_article = Article(**article_data)
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

def process_and_save_fire_related_article(db: Session, article_data: dict):
    db_article = FireRelatedArticle(**article_data)
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

def get_websites_from_db(db: Session):
    return db.query(Website).all()

def crawl_from_websites(search_term="fire", db: Session = Depends(get_db)):
    all_articles = []
    websites = get_websites_from_db(db)

    for website in websites:
        print(f"Fetching news from {website.name}...")
        articles = fetch_news_from_site(website.url, search_term)
        for article in articles:
            save_raw_article(db, article)
            processed_article = {**article, 'processed': 1}
            process_and_save_fire_related_article(db, processed_article)
        all_articles.extend(articles)

    return all_articles