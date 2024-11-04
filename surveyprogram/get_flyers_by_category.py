import asyncio
from playwright.async_api import async_playwright
import json

async def scroll_to_end(page):
    last_height = await page.evaluate("document.body.scrollHeight")
    while True:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        await page.wait_for_timeout(1000)

        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

async def scrape_flyers_by_category(category, postal_code):
    url = f"https://flipp.com/en-ca/flyers?postal_code={postal_code}" if category.lower() == "all flyers" else f"https://flipp.com/en-ca/flyers/{category.lower()}?postal_code={postal_code}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(url)
        await page.wait_for_load_state('networkidle')

        sorting_options = ['featured', 'latest', 'alphabetical']
        result = {}

        for option in sorting_options:
            print(f"Clicking on '{option}' sorting button")
            await page.click(f'button[sort="{option}"]')
            await page.wait_for_load_state('networkidle')
            await scroll_to_end(page)
            
            await page.wait_for_selector('div.content', state='visible', timeout=15000)

            flyers = await page.query_selector_all('div.content flipp-flyer-listing-item')
            if not flyers:
                print(f"Error: No flyers found for option '{option}'.")
                result[option] = []
                continue

            flyers_data = []
            for flyer in flyers:
                name_element = await flyer.query_selector('p.flyer-name')
                validity_element = await flyer.query_selector('div.flyer-info-block p:nth-of-type(2)')
                img_element = await flyer.query_selector('img.flyer-thumbnail')
                link_element = await flyer.query_selector('a.flyer-container, a.premium-flyer-container')

                name_text = await name_element.inner_text() if name_element else 'Unknown'
                valid_until_text = await validity_element.inner_text() if validity_element else 'Unknown'
                img_src = await img_element.get_attribute('src') if img_element else None
                flyer_link = await link_element.get_attribute('href') if link_element else None

                flyer_info = {
                    "name": name_text.strip(),
                    "valid_until": valid_until_text.strip(),
                    "image_url": img_src,
                    "source_link": "https://flipp.com" + flyer_link if flyer_link else None
                }
                flyers_data.append(flyer_info)

            result[option] = flyers_data

        await browser.close()

    return result  # Return dictionary instead of JSON-encoded string

# For testing outside of Flask
category = "Groceries"
postal_code = "P7A1A1"

# async def main():
#     flyers_data = await scrape_flyers_by_category(category, postal_code)
#     print(json.dumps(flyers_data, indent=2))

# asyncio.run(main())
