import asyncio
from playwright.async_api import async_playwright
import json

async def scrape_flyer_categories(postal_code):
    url = f"https://flipp.com/en-ca/flyers/groceries?postal_code={postal_code}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Navigate to the URL
        print(f"Navigating to {url}")
        await page.goto(url)
        
       
        await page.wait_for_load_state('networkidle')


        # Wait for the categories section to be fully visible
        try:
            await page.wait_for_selector('div.categories', state='visible', timeout=15000)
        except Exception as e:
            print("Error: Categories section did not become visible in time:", e)
            await browser.close()
            return

        categories_section = await page.query_selector('div.categories')
        categories = await categories_section.query_selector_all('a[is="flipp-link"]')

        if not categories:
            print("Error: No categories found after page load.")
            await browser.close()
            return
        
        # print(f"Found {len(categories)} categories.")
        result = []
        for category in categories:
            name = await category.query_selector('span[flex-grow="true"]')
            count = await category.query_selector('span.pill')

            name_text = await name.inner_text() if name else 'Unknown'
            count_text = await count.inner_text() if count else '0'

            # print(f"Category: {name_text.strip()}, Count: {count_text.strip()}")  # Debugging output
            result.append({
                "name": name_text.strip(),
                "count": count_text.strip()
            })
        
        await browser.close()

    # Return the result in JSON format
    return result


# postal_code = "P7A1A1"


# async def main():
#     categories_json = await scrape_flyer_categories(postal_code)
#     print(categories_json)

# asyncio.run(main())
