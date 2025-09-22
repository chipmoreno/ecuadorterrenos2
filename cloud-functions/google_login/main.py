from flask import jsonify
from pymongo import MongoClient
import os
import jwt
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime, timedelta

# Function to get a MongoDB connection
def get_database():
    MONGO_URI = os.environ.get('MONGODB_URI')
    client = MongoClient(MONGO_URI)
    return client.get_database()

# Your JWT secret
JWT_SECRET = os.environ.get('JWT_SECRET')

def google_login(request):
    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    # Set CORS headers for the main request
    headers = {'Access-Control-Allow-Origin': '*'}

    if request.method != 'POST':
        return jsonify({"message": "Method not allowed"}), 405, headers

    db = get_database()
    users_collection = db.users

    try:
        request_json = request.get_json(silent=True)
        id_token_from_client = request_json.get('token')

        if not id_token_from_client:
            return jsonify({"message": "Token not provided."}), 400, headers

        # Verify the Google ID token
        # You need the Google Client ID as an environment variable
        google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
        if not google_client_id:
            return jsonify({"message": "GOOGLE_CLIENT_ID not set."}), 500, headers
            
        idinfo = id_token.verify_oauth2_token(id_token_from_client, requests.Request(), google_client_id)
        
        email = idinfo['email']
        name = idinfo.get('name', 'User') # Get name from token, default to 'User'
        google_id = idinfo['sub'] # Unique Google user ID

        # Check if the user already exists in your database
        user = users_collection.find_one({"email": email})

        if user:
            # User already exists, log them in
            user_id = str(user['_id'])
        else:
            # New user, create an account with Google ID
            new_user = {
                "email": email,
                "name": name,
                "google_id": google_id,
                "created_at": datetime.utcnow()
            }
            result = users_collection.insert_one(new_user)
            user_id = str(result.inserted_id)
            print(f"New user created with Google login: {email}")

        # Generate your own JWT for the user
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(days=7)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

        return jsonify({
            "message": "Login successful",
            "token": token
        }), 200, headers

    except ValueError as e:
        print(f"Token validation failed: {e}")
        return jsonify({"message": "Invalid token"}), 401, headers
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"message": "Authentication failed"}), 500, headers