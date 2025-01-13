from fastapi.responses import HTMLResponse
from fastapi import FastAPI
from .routers import data
from .database import Base, engine
from fastapi.staticfiles import StaticFiles
from app.services.news_crawler import router as news_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend/assets"), name="static")

app.include_router(data.router)

from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def get_index():
    with open("frontend/index.html", "r") as f:
        content = f.read()
    return content

app.include_router(news_router, prefix="/api")
