#!/usr/bin/env python3
"""
Data models for Advanced Fire Scraper
"""

from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime

@dataclass
class ArticleData:
    """Data structure for scraped articles"""
    url: str
    title: str
    content: str
    published_date: str
    source: str
    author: str = ""
    summary: str = ""
    keywords: List[str] = None
    fire_related_score: float = 0.0
    scraped_at: str = ""
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if not self.scraped_at:
            self.scraped_at = datetime.now().isoformat()
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self) 