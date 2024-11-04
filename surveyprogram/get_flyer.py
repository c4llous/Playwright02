from flask import Flask, jsonify, send_from_directory
from playwright.sync_api import sync_playwright
import os
from PIL import Image

app = Flask(__name__)

# Ensure the image directory exists
image_dir = "screenshots"
os.makedirs(image_dir, exist_ok=True)

def scrape_flyer_with_playwright(url):
    with sync_playwright() as p:
        # Launch browser in headful mode
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Go to the URL
            page.goto(url)

            # Wait for the network to be idle and for all elements to load
            page.wait_for_load_state('networkidle', timeout=60000)
            print("Network is idle, waiting for canvas...")

            # Remove unwanted elements
            page.evaluate("""
                document.querySelectorAll('#app > flipp-flyer-page > flipp-page > download-app-banner > div').forEach(el => el.remove());
            """)
            page.evaluate("""
                document.querySelectorAll('body > div.cky-consent-container.cky-box-bottom-left').forEach(el => el.remove());
            """)
            page.evaluate("""
                document.querySelectorAll('#app > flipp-flyer-page > flipp-page > div > main > div > div.experience-container > div.flyer-view-container > div.zoom-buttons').forEach(el => el.remove());
            """)
            page.evaluate("""
                document.querySelectorAll('#app > flipp-flyer-page > flipp-page > div > main > div > div.experience-container > div.flyer-view-container > a').forEach(el => el.remove());
            """)

            # Get the canvas bounding box to ensure we only capture it
            canvas_handle = page.query_selector('flipp-flyerview canvas')
            canvas_box = canvas_handle.bounding_box()

            # Take two screenshots of the canvas element
            screenshot_1_path = os.path.join(image_dir, "screenshot1.png")
            page.screenshot(path=screenshot_1_path, clip={
                'x': canvas_box['x'],
                'y': canvas_box['y'],
                'width': canvas_box['width'],
                'height': canvas_box['height']
            })
            
            # Scroll horizontally by a defined amount (e.g., 300 pixels)
            page.evaluate("document.querySelector('flipp-flyerview canvas').scrollBy(300, 0)")
            screenshot_2_path = os.path.join(image_dir, "screenshot2.png")
            page.screenshot(path=screenshot_2_path, clip={
                'x': canvas_box['x'],
                'y': canvas_box['y'],
                'width': canvas_box['width'],
                'height': canvas_box['height']
            })

            # Merge the screenshots
            images = [Image.open(screenshot_1_path), Image.open(screenshot_2_path)]
            widths, heights = zip(*(img.size for img in images))

            total_width = sum(widths)
            max_height = max(heights)

            merged_image = Image.new('RGB', (total_width, max_height))

            x_offset = 0
            for img in images:
                merged_image.paste(img, (x_offset, 0))
                x_offset += img.width

            merged_image_path = os.path.join(image_dir, 'merged_image.png')
            merged_image.save(merged_image_path)
            
            print(f'Merged image saved at {merged_image_path}')
            return merged_image_path

        except Exception as e:
            print(f"Error while processing the flyer: {e}")
            return None
        finally:
            context.close()
            browser.close()


def scrape_flyer(url):
    try:
        # Call synchronous Playwright scraping
        result = scrape_flyer_with_playwright(url)
        if result:
            return {"image_url": result}
        else:
            return {"error": "Failed to scrape flyer"}, 500
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}, 500

@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory(image_dir, filename)

if __name__ == "__main__":
    app.run(debug=True)
