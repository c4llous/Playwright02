import os
import uuid
import json
import logging
from flask import Flask, request, jsonify
import pika
import redis

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Setup logging
log_directory = "logs"
os.makedirs(log_directory, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_directory, "app.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Redis setup for job status
redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)

# RabbitMQ setup
rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
channel = connection.channel()
channel.queue_declare(queue="task_queue", durable=True)

# API Key for securing routes
API_KEY = os.getenv("API_KEY", "default_api_key")


# Utility to validate API key
def validate_api_key():
    api_key = request.headers.get("X-API-Key")
    if api_key != API_KEY:
        return False
    return True


@app.route('/scrape/categories', methods=['POST'])
def scrape_categories():
    if not validate_api_key():
        return jsonify({"error": "Invalid API Key."}), 401

    data = request.json
    postal_code = data.get("postal_code")
    if not postal_code:
        return jsonify({"error": "Postal code is required."}), 400

    job_id = str(uuid.uuid4())
    task_data = {"type": "categories", "postal_code": postal_code, "job_id": job_id}
    channel.basic_publish(
        exchange="",
        routing_key="task_queue",
        body=json.dumps(task_data),
        properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
    )
    redis_client.set(job_id, json.dumps({"status": "pending"}))
    logging.info(f"Job {job_id} added for scrape_categories with postal code {postal_code}")
    return jsonify({"job_id": job_id})


@app.route('/scrape/url', methods=['POST'])
def scrape_url():
    if not validate_api_key():
        return jsonify({"error": "Invalid API Key."}), 401

    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"error": "URL is required."}), 400

    job_id = str(uuid.uuid4())
    task_data = {"type": "url", "url": url, "job_id": job_id}
    channel.basic_publish(
        exchange="",
        routing_key="task_queue",
        body=json.dumps(task_data),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    redis_client.set(job_id, json.dumps({"status": "pending"}))
    logging.info(f"Job {job_id} added for scrape_url with URL {url}")
    return jsonify({"job_id": job_id})


@app.route('/scrape/category', methods=['POST'])
def scrape_by_category():
    if not validate_api_key():
        return jsonify({"error": "Invalid API Key."}), 401

    data = request.json
    postal_code = data.get("postal_code")
    category = data.get("category")
    if not postal_code or not category:
        return jsonify({"error": "Postal code and category are required."}), 400

    job_id = str(uuid.uuid4())
    task_data = {"type": "category", "postal_code": postal_code, "category": category, "job_id": job_id}
    channel.basic_publish(
        exchange="",
        routing_key="task_queue",
        body=json.dumps(task_data),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    redis_client.set(job_id, json.dumps({"status": "pending"}))
    logging.info(f"Job {job_id} added for scrape_by_category with postal code {postal_code} and category {category}")
    return jsonify({"job_id": job_id})


@app.route('/job/status/<job_id>', methods=['GET'])
def job_status(job_id):
    job_data = redis_client.get(job_id)
    if not job_data:
        return jsonify({"error": "Job ID not found."}), 404

    job_data = json.loads(job_data)
    return jsonify(job_data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
