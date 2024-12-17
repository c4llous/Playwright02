import os
import logging
from flask import Flask, request, jsonify, abort
import sqlite3
import secrets
from functools import wraps
from datetime import datetime

app = Flask(__name__)

# Database initialization
DB_NAME = "user_management.db"

# Create logs directory if not exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging
log_filename = os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()  # Optional: Logs to the console as well
    ]
)

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            api_key TEXT
        )
    ''')
    conn.commit()
    conn.close()
    logging.info("Database initialized.")

# Restrict to localhost
def localhost_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.remote_addr != "127.0.0.1":
            logging.warning(f"Unauthorized access attempt from {request.remote_addr}")
            abort(403, description="Access forbidden: Only localhost allowed.")
        return f(*args, **kwargs)
    return decorated_function

# Helper functions
def execute_query(query, params=(), fetch_one=False, fetch_all=False):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = None
            conn.commit()
        return result
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        raise
    finally:
        conn.close()

def generate_api_key():
    return secrets.token_hex(32)

# Routes
@app.route("/user", methods=["POST"])
@localhost_only
def create_user():
    data = request.json
    email = data.get("email")
    username = data.get("username")

    if not email or not username:
        logging.error("Validation error: Missing email or username.")
        return jsonify({"error": "Email and username are required"}), 400

    # Check if the user already exists
    existing_user = execute_query("SELECT email FROM users WHERE email = ?", (email,), fetch_one=True)
    if existing_user:
        logging.warning(f"Attempt to create duplicate user: {email}")
        return jsonify({"error": "User with this email already exists"}), 400

    # Create the user
    execute_query("INSERT INTO users (email, username) VALUES (?, ?)", (email, username))
    logging.info(f"User created successfully: {email}")
    return jsonify({"message": "User created successfully"}), 201

@app.route("/user/<email>", methods=["PUT"])
@localhost_only
def edit_user(email):
    data = request.json
    username = data.get("username")

    if not username:
        logging.error(f"Validation error: Missing username for user {email}.")
        return jsonify({"error": "Username is required"}), 400

    # Update the user
    rows_affected = execute_query("UPDATE users SET username = ? WHERE email = ?", (username, email))
    if rows_affected == 0:
        logging.warning(f"User not found for edit: {email}")
        return jsonify({"error": "User not found"}), 404

    logging.info(f"User updated successfully: {email}")
    return jsonify({"message": "User updated successfully"})

@app.route("/user/<email>", methods=["DELETE"])
@localhost_only
def delete_user(email):
    rows_affected = execute_query("DELETE FROM users WHERE email = ?", (email,))
    if rows_affected == 0:
        logging.warning(f"User not found for delete: {email}")
        return jsonify({"error": "User not found"}), 404

    logging.info(f"User deleted successfully: {email}")
    return jsonify({"message": "User deleted successfully"})

@app.route("/user/<email>", methods=["GET"])
@localhost_only
def get_user_details(email):
    user = execute_query("SELECT email, username, api_key FROM users WHERE email = ?", (email,), fetch_one=True)
    if not user:
        logging.warning(f"User not found for details: {email}")
        return jsonify({"error": "User not found"}), 404
    logging.info(f"User details fetched: {email}")
    return jsonify({"email": user[0], "username": user[1], "api_key": user[2]})

@app.route("/users", methods=["GET"])
@localhost_only
def get_all_users():
    users = execute_query("SELECT email, username, api_key FROM users", fetch_all=True)
    logging.info("All user details fetched.")
    return jsonify([{"email": user[0], "username": user[1], "api_key": user[2]} for user in users])

@app.route("/user/<email>/api_key", methods=["POST"])
@localhost_only
def create_user_api_key(email):
    user = execute_query("SELECT email FROM users WHERE email = ?", (email,), fetch_one=True)
    if not user:
        logging.warning(f"User not found for API key creation: {email}")
        return jsonify({"error": "User not found"}), 404

    api_key = generate_api_key()
    execute_query("UPDATE users SET api_key = ? WHERE email = ?", (api_key, email))
    logging.info(f"API key created for user: {email}")
    return jsonify({"message": "API key created", "api_key": api_key})

@app.route("/user/<email>/api_key", methods=["PUT"])
@localhost_only
def regenerate_user_api_key(email):
    user = execute_query("SELECT email FROM users WHERE email = ?", (email,), fetch_one=True)
    if not user:
        logging.warning(f"User not found for API key regeneration: {email}")
        return jsonify({"error": "User not found"}), 404

    api_key = generate_api_key()
    execute_query("UPDATE users SET api_key = ? WHERE email = ?", (api_key, email))
    logging.info(f"API key regenerated for user: {email}")
    return jsonify({"message": "API key regenerated", "api_key": api_key})

# Run server
if __name__ == "__main__":
    init_db()
    logging.info("Starting the Flask application.")
    app.run(debug=True, host="127.0.0.1", port=5000)
