from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas, database  # Correct import

router = APIRouter()

@router.post("/articles/", response_model=schemas.Article)
def create_article(article: schemas.ArticleCreate, db: Session = Depends(database.get_db)):
    db_article = models.Article(**article.dict())
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

@router.get("/articles/", response_model=list[schemas.Article])
def read_articles(skip: int = 0, limit: int = 10, db: Session = Depends(database.get_db)):
    return db.query(models.Article).offset(skip).limit(limit).all()
