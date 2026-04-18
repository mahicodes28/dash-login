from flask import Flask, request, jsonify, session
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# Add a secret key for session encryption, now loaded from .env
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret-key-for-dev")

# Ensure cross-domain cookie sending is permitted
CORS(app, supports_credentials=True, origins=["http://localhost:3000"]) 

MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["interviewDB"]

# Collections
collection = db["interviews"]
users_collection = db["users"] # New collection for users

@app.route("/", methods=["GET"])
def home():
    return "Backend"

# --- USER AUTHENTICATION ROUTES ---

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    # Ensure user logic - don't add duplicates
    if users_collection.find_one({"username": username}):
        return jsonify({"message": "User already exists"}), 409

    hashed_password = generate_password_hash(password)
    users_collection.insert_one({"username": username, "password": hashed_password})
    
    return jsonify({"message": "User registered successfully"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user = users_collection.find_one({"username": username})
    
    if user and check_password_hash(user["password"], password):
        # Create a session variable marking user log in
        session['user'] = username
        return jsonify({"message": "Login successful", "username": username}), 200
        
    return jsonify({"message": "Invalid username or password"}), 401

@app.route("/logout", methods=["POST"])
def logout():
    session.pop('user', None) # Remove the user parameter from the session
    return jsonify({"message": "Logged out successfully"}), 200

@app.route("/check_session", methods=["GET"])
def check_session():
    # Helper route to verify if a user is currently logged in on page load
    if 'user' in session:
        return jsonify({"loggedIn": True, "username": session['user']}), 200
    return jsonify({"loggedIn": False}), 401

# --- EXISTING ROUTES ---

@app.route("/interviews", methods=["GET"])
def get_interviews():
    data = list(collection.find({}, {"_id": 0}))
    return jsonify(data)

@app.route("/interviews", methods=["POST"])
def add_interview():
    new_data = request.json
    collection.insert_one(new_data)
    return jsonify({"message": "Data added successfully"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
