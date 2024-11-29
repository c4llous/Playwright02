from flask import Flask, request, jsonify
import asyncio


from get_categories import scrape_flyer_categories
from get_flyer import scrape_flyer
from get_flyers_by_category import scrape_flyers_by_category

app = Flask(__name__)

@app.route('/scrape/categories', methods=['POST'])
def scrape_categories():
    data = request.json
    postal_code = data.get('postal_code')
    
    if not postal_code:
        return jsonify({"error": "Postal code is required."}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(scrape_flyer_categories(postal_code))
    
    return jsonify(result)

@app.route('/scrape/url', methods=['POST'])
def scrape_url():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({"error": "URL is required."}), 400

    # Directly call the synchronous scrape function
    result = scrape_flyer(url)

    return jsonify({"result": result})

@app.route('/scrape/category', methods=['POST'])
def scrape_by_category():
    data = request.json
    postal_code = data.get('postal_code')
    category = data.get('category')

    if not postal_code or not category:
        return jsonify({"error": "Postal code and category are required."}), 400

    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(scrape_flyers_by_category(category, postal_code))
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)  # Set debug=False in production
  