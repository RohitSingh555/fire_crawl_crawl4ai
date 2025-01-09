from sqlalchemy import Column, Integer, String, Text
from .database import Base

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    website_name = Column(String, index=True)
    url = Column(String, unique=True, index=True)
    summary = Column(Text)
    date = Column(String)
    author = Column(String, nullable=True)

class FireRelatedArticle(Base):
    __tablename__ = 'fire_related_articles'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    link = Column(String)
    description = Column(Text)
    published_date = Column(String)
    processed = Column(Integer, default=0)



class Website(Base):
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, index=True)  
    state = Column(String, index=True)
    city = Column(String, index=True) 
    town = Column(String, index=True) 
    news_link = Column(String, unique=True, index=True)