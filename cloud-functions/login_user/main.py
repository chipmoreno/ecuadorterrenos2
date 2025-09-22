import os
import functions_framework
import json
import bcrypt
import jwt
from datetime import datetime, timedelta
from pymongo import MongoClient
from werkzeug.exceptions import BadRequest
from flask import jsonify

@functions_framework.http
def login_user(request):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
    }

    if request.method == 'OPTIONS':
        return ('', 204, headers)
    
    if request.method != 'POST':
        return ('', 405, headers)

    try:
        request_json = request.get_json(silent=True)
        if not request_json:
            return (jsonify({'msg': 'Invalid JSON payload.'}), 400, headers)
        
        email = request_json.get('email')
        password = request_json.get('password')

        if not email or not password:
            return (jsonify({'msg': 'Email and password are required.'}), 400, headers)

        mongo_uri = os.environ.get('MONGODB_URI')
        jwt_secret = os.environ.get('JWT_SECRET')
        if not mongo_uri or not jwt_secret:
            return (jsonify({'msg': 'One or more environment variables are not set.'}), 500, headers)

        client = MongoClient(mongo_uri)
        db = client.get_database('listings')
        users_collection = db['users']

        # Find the user by email
        user = users_collection.find_one({'email': email})
        if not user:
            return (jsonify({'msg': 'Invalid credentials.'}), 401, headers)

        # Check the password
        if not bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return (jsonify({'msg': 'Invalid credentials.'}), 401, headers)

        # Generate a new JWT
        payload = {
            'user_id': str(user['_id']),
            'exp': datetime.utcnow() + timedelta(days=7)
        }
        token = jwt.encode(payload, jwt_secret, algorithm='HS256')

        response_body = {
            'msg': 'Login successful!',
            'token': token
        }
        return (jsonify(response_body), 200, headers)

    except Exception as e:
        print(f"Login error: {e}")
        return (jsonify({'msg': 'An error occurred.', 'error': str(e)}), 500, headers)