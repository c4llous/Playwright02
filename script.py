from playwright.sync_api import sync_playwright

def scrape_flyer_with_playwright(url):
    with sync_playwright() as p:
        # Launch browser in headful mode to see everything
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Go to the URL
            page.goto(url)

            # Wait for the network to be idle and for all elements to load
            page.wait_for_load_state('networkidle', timeout=60000)
            print("Network is idle, waiting for canvas...")

            # Remove popups and overlays that could be obstructing the canvas
            page.evaluate("""document.querySelectorAll('#app > flipp-flyer-page > flipp-page > download-app-banner > div').forEach(el => el.remove());""")
            page.evaluate("""document.querySelectorAll('body > div.cky-consent-container.cky-box-bottom-left').forEach(el => el.remove());""")
            page.evaluate("""document.querySelectorAll('#app > flipp-flyer-page > flipp-page > div > main > div > div.experience-container > div.flyer-view-container > div.zoom-buttons').forEach(el => el.remove());""")
            page.evaluate("""document.querySelectorAll('#app > flipp-flyer-page > flipp-page > div > main > div > div.experience-container > div.flyer-view-container > a').forEach(el => el.remove());""")
            
            print("Popups and overlays removed.")

            # Get all frames and search for the canvas inside the correct frame
            frames = page.frames
            target_frame = None
            for frame in frames:
                if 'flipp' in frame.url:
                    target_frame = frame
                    break

            if target_frame:
                print(f"Canvas found in frame with URL: {target_frame.url}")

                # Wait for the canvas element to be fully visible
                target_frame.wait_for_selector('flipp-flyerview canvas', timeout=60000)
                print("Canvas element found!")

                # Ensure the canvas is fully rendered by waiting
                target_frame.wait_for_timeout(5000)

                # Take a screenshot of the first page
                canvas = target_frame.query_selector('flipp-flyerview canvas')
                if canvas:
                    image_path = 'flyer_canvas_screenshot_page_1.png'
                    canvas.screenshot(path=image_path)
                    print(f'First screenshot saved at {image_path}')
                else:
                    print("Canvas element not found after removal of popups.")
                    return None

                # Click the 'Next Page' button five times
                for i in range(5):
                    print(f"Clicking next page button, attempt {i + 1}...")
                    next_page_button = target_frame.query_selector('button.next-page[title="Next Page"]')
                    if next_page_button:
                        next_page_button.click()
                        target_frame.wait_for_load_state('networkidle')
                        print("Next page loaded.")
                    else:
                        print("Next page button not found.")
                        return None
                
                # Wait for the next canvas to render after navigating pages
                target_frame.wait_for_timeout(5000)

                # Take a screenshot of the next page
                canvas = target_frame.query_selector('flipp-flyerview canvas')
                if canvas:
                    image_path = 'flyer_canvas_screenshot_page_6.png'
                    canvas.screenshot(path=image_path)
                    print(f'Second screenshot saved at {image_path}')
                    return image_path
                else:
                    print("Canvas element not found after page navigation.")
                    return None

            else:
                print("Canvas frame not found!")
                return None

        except Exception as e:
            print(f"Error while processing the canvas element: {e}")

        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    url = "https://flipp.com/en-ca/thunder-bay-on/flyer/6853525-no-frills-weekly-flyer-valid-thursday-october-3-wednesday-october-9?postal_code=P7A1A1"
    scrape_flyer_with_playwright(url)
