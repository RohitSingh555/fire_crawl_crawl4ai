from pydantic import BaseModel
from typing import Optional

class ArticleBase(BaseModel):
    title: str
    website_name: str
    url: str
    summary: str
    date: str
    author: Optional[str]

class ArticleCreate(ArticleBase):
    pass

class Article(ArticleBase):
    id: int

    class Config:
        orm_mode = True
