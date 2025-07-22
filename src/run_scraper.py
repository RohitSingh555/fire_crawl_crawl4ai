#!/usr/bin/env python3
"""
Simple runner script for the Advanced Fire Scraper
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import NEWS_WEBSITES
    from scraper import AdvancedFireScraper
    from utils import setup_logging
    
    logger = setup_logging()
    
    async def run_scraper():
        """Run the fire news scraper"""
        print("🔥 Advanced Fire News Scraper Starting...")
        print(f"📰 Target websites: {len(NEWS_WEBSITES)}")
        
        # Initialize scraper
        scraper = AdvancedFireScraper()
        
        try:
            # Start scraping
            articles = await scraper.scrape_websites(NEWS_WEBSITES)
            
            print(f"\n✅ Scraping completed! Found {len(articles)} fire-related articles.")
            
            # Print summary
            if articles:
                print("\n🔥 Top 5 articles by fire relevance score:")
                sorted_articles = sorted(articles, key=lambda x: x.fire_related_score, reverse=True)
                for i, article in enumerate(sorted_articles[:5], 1):
                    print(f"{i}. {article.title[:80]}... (Score: {article.fire_related_score:.2f})")
                    print(f"   Source: {article.source}")
                    print(f"   URL: {article.url}")
                    print()
            
            # Print statistics
            if articles:
                sources = set(article.source for article in articles)
                avg_score = sum(article.fire_related_score for article in articles) / len(articles)
                print(f"\n📊 Statistics:")
                print(f"   Total articles: {len(articles)}")
                print(f"   Unique sources: {len(sources)}")
                print(f"   Average fire relevance score: {avg_score:.2f}")
                print(f"   Output directory: {scraper.config['storage']['output_dir']}")
            
        except KeyboardInterrupt:
            print("\n⚠️  Scraping interrupted by user")
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            print(f"\n❌ Error: {e}")
        finally:
            scraper.cleanup()
            print("\n🏁 Scraper finished.")
    
    if __name__ == "__main__":
        asyncio.run(run_scraper())
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required packages are installed:")
    print("source src/venv/bin/activate && pip install -r src/requirements.txt")
except Exception as e:
    print(f"❌ Unexpected error: {e}") 