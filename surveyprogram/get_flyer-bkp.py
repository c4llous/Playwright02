from flask import Flask, jsonify, send_from_directory, request
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
            page.wait_for_load_state('networkidle', timeout=60000)

            print("Network is idle, waiting for flyer...")

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

            # Find the canvas and its bounding box
            canvas_handle = page.query_selector('flipp-flyerview canvas')
            if not canvas_handle:
                raise Exception("Canvas element not found")
            canvas_box = canvas_handle.bounding_box()
            if not canvas_box:
                raise Exception("Failed to retrieve bounding box of canvas")

            # Scroll and capture screenshots using the button
            screenshots = []
            scroll_button_selector = "#app > flipp-flyer-page > flipp-page > div > main > div > div.experience-container > div.flyer-view-container > button.next-page"
            scroll_attempts = 0

            while True:
                # Take a screenshot of the current view
                screenshot_path = os.path.join(image_dir, f"screenshot_{scroll_attempts}.png")
                page.screenshot(path=screenshot_path, clip={
                    'x': canvas_box['x'],
                    'y': canvas_box['y'],
                    'width': canvas_box['width'],
                    'height': canvas_box['height']
                })
                screenshots.append(screenshot_path)

                # Check if the scroll button is disabled
                button_handle = page.query_selector(scroll_button_selector)
                if not button_handle or button_handle.is_disabled():
                    print("Reached the end of the flyer.")
                    break

                # Click the scroll button to move to the next section
                button_handle.click()
                scroll_attempts += 1

                # Wait for the scrolling to complete
                page.wait_for_timeout(1000)

            # Merge screenshots vertically
            images = [Image.open(screenshot) for screenshot in screenshots]

            # Get total width and height for the final merged image
            total_height = sum(img.size[1] for img in images)
            max_width = max(img.size[0] for img in images)

            # Create a blank canvas for the merged image
            merged_image = Image.new('RGB', (max_width, total_height))
            y_offset = 0

            for img in images:
                merged_image.paste(img, (0, y_offset))
                y_offset += img.size[1]

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
           return jsonify({"data": result})
        else:
            return {"error": "Failed to scrape flyer"}, 500
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}, 500


@app.route('/scrape/url', methods=['POST'])
def scrape_url():
    data = request.json
    url = data.get("url")
    if not url:
        return {"error": "Missing URL"}, 400
    return jsonify(scrape_flyer(url))


@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory(image_dir, filename)


if __name__ == "__main__":
    app.run(debug=True)
