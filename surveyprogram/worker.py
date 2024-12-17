import json
import pika
import redis
import asyncio
from get_categories import scrape_flyer_categories
from get_flyer import scrape_flyer
from get_flyers_by_category import scrape_flyers_by_category

# Redis setup
redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)

# RabbitMQ setup
connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
channel = connection.channel()
channel.queue_declare(queue="task_queue", durable=True)


def process_task(ch, method, properties, body):
    task = json.loads(body)
    job_id = task["job_id"]
    redis_client.set(job_id, json.dumps({"status": "in_progress"}))

    try:
        if task["type"] == "categories":
            result = asyncio.run(scrape_flyer_categories(task["postal_code"]))
        elif task["type"] == "url":
            result = scrape_flyer(task["url"])
        elif task["type"] == "category":
            result = asyncio.run(scrape_flyers_by_category(task["category"], task["postal_code"]))
        else:
            raise ValueError("Unknown task type.")

        redis_client.set(job_id, json.dumps({"status": "completed", "result": result}))
    except Exception as e:
        redis_client.set(job_id, json.dumps({"status": "failed", "error": str(e)}))
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_consume(queue="task_queue", on_message_callback=process_task)
print("Worker is ready to process tasks.")
channel.start_consuming()
