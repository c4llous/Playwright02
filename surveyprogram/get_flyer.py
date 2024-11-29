import requests
import re

def scrape_flyer(url):
    # Extract the flyer ID from the URL using regex
    match = re.search(r'/flyer/(\d+)-', url)
    if not match:
        raise ValueError("Flyer ID not found in the URL.")
    flyer_id = match.group(1)

    # API URL
    api_url = f"https://flyers-ng.flippback.com/api/flipp/flyers/{flyer_id}/flyer_items"

    # Fetch data from the API
    response = requests.get(api_url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data from API. Status code: {response.status_code}")
    data = response.json()

    # Process the data
    processed_data = []
    for item in data:
        processed_item = {
            "id": item["id"],
            "sku": item["flyer_id"],  # Renaming flyer_id to sku
            "name": item["name"],
            "cutout_image_url": item["cutout_image_url"],
            "brand": item["brand"],
            "valid_from": item["valid_from"],
            "valid_to": item["valid_to"],
            "price": item["price"]
        }
        processed_data.append(processed_item)

    return processed_data

# Example usage
url = "https://flipp.com/en-ca/thunder-bay-on/flyer/6952741-sephora-holiday?postal_code=P7A1A1"
# result = process_flyer_data(url)

# Print the output
# print(result)
