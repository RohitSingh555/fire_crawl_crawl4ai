import asyncio
import requests
from playwright.async_api import async_playwright
import time

async def test_azfamily_access():
    """Test if we can access AZ Family website"""
    
    # First try with requests
    print("🔍 Testing with requests...")
    try:
        response = requests.get('https://www.azfamily.com/search/?query=fire', timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Content length: {len(response.text)}")
        if "queryly_item_row" in response.text:
            print("✅ Found queryly_item_row in response")
        else:
            print("❌ queryly_item_row not found in response")
    except Exception as e:
        print(f"❌ Requests failed: {e}")
    
    # Then try with Playwright
    print("\n🔍 Testing with Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Use visible browser for debugging
        page = await browser.new_page()
        
        try:
            print("Navigating to AZ Family...")
            await page.goto('https://www.azfamily.com/search/?query=fire', timeout=60000)
            print("Page loaded successfully")
            
            # Wait a bit
            await asyncio.sleep(5)
            
            # Check if content is loaded
            content = await page.content()
            print(f"Content length: {len(content)}")
            
            if "queryly_item_row" in content:
                print("✅ Found queryly_item_row in page content")
                
                # Try to find the Next Page button
                next_button = await page.query_selector("a.next_btn")
                if next_button:
                    print("✅ Found Next Page button")
                else:
                    print("❌ Next Page button not found")
                    
                # Count articles
                articles = await page.query_selector_all("div.queryly_item_row")
                print(f"Found {len(articles)} article rows")
                
            else:
                print("❌ queryly_item_row not found in page content")
                
            # Take a screenshot for debugging
            await page.screenshot(path="azfamily_debug.png")
            print("📸 Screenshot saved as azfamily_debug.png")
            
        except Exception as e:
            print(f"❌ Playwright failed: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_azfamily_access()) 