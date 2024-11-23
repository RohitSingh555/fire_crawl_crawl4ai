import os
import json
import asyncio
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy

load_dotenv()  # Load environment variables from the .env file

yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

with open("websites.txt", "r") as file:
    target_websites = [line.strip() for line in file.readlines()]

KEYWORDS = [
    "fire", "blaze", "wildfire", "arson", "inferno", "conflagration", "flames", "smoke",
    "burning", "ignition", "explosion", "firefighting", "extinguish", "embers", "scorched",
    "flammable", "hazard", "combustion", "sparks", "rescue", "evacuation", "firebreak",
    "controlled burn", "firestorm", "smoldering", "charred", "arsonist", "backdraft",
    "firetruck", "firefighter", "fire brigade", "fire department", "fire hazard",
    "incendiary", "fire alarm", "fire response", "fire suppression", "brushfire",
    "structure fire", "house fire", "apartment fire", "forest fire", "grassfire",
    "electrical fire", "chemical fire", "incident"
]

instruction = f"Extract news articles related to 'fire' that were published on {yesterday} in the USA."

output_file = f"fire_news_new{yesterday}.json"

class NewsResponse(BaseModel):
    Title: str = Field(None, description="Name of the OpenAI model.")
    Summary: str = Field(None, description="Fee for input token for the OpenAI model.")
    Link: str = Field(None, description="Fee for output token for the OpenAI model.")

async def crawl_fire_related_news():
    extracted_news = []

    if not os.path.exists(output_file):
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump([], f)

    api_token = os.getenv("OPENAI_API_KEY")  # Fetch the OpenAI API key from the environment

    if not api_token:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        return

    async with AsyncWebCrawler(verbose=True) as crawler:
        for url in target_websites:
            try:
                result = await crawler.arun(
                    url=url,
                    extraction_strategy=LLMExtractionStrategy(
                        provider="openai/gpt-4o",
                        api_token=api_token,  # Use the API token from the environment
                        instruction=instruction,
                        schema=NewsResponse.model_json_schema(),
                        extraction_type="schema",   
                        magic=True,
                        headless=False,
                    ),
                    bypass_cache=True,
                )

                news_items = json.loads(result.extracted_content)
                print(news_items)
                extracted_news.extend(news_items)

                with open(output_file, "r+", encoding="utf-8") as f:
                    data = json.load(f)
                    data.extend(news_items)
                    f.seek(0)
                    json.dump(data, f, indent=2)

                print(f"Successfully processed {url} and saved results.")

            except Exception as e:
                print(f"Error while processing {url}: {e}")

            await asyncio.sleep(5)

    print(f"Finished processing all websites. Extracted news saved to {output_file}")

asyncio.run(crawl_fire_related_news())
