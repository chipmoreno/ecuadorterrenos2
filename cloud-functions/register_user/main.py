import os
import functions_framework
import json
import jwt
import bcrypt
from datetime import datetime, timedelta
from pymongo import MongoClient
from werkzeug.exceptions import BadRequest

@functions_framework.http
def register_user(request):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
    }

    if request.method == 'OPTIONS':
        return ('', 204, headers)
    
    try:
        mongo_uri = os.environ.get('MONGODB_URI')
        jwt_secret = os.environ.get('JWT_SECRET')
        if not mongo_uri or not jwt_secret:
            raise ValueError('Environment variables are not set.')

        request_json = request.get_json(silent=True)
        if not request_json:
            raise BadRequest('Invalid JSON payload.')

        # Validate required fields
        email = request_json.get('email')
        username = request_json.get('username')
        fullname = request_json.get('fullname')
        password = request_json.get('password')
        if not email or not username or not fullname or not password:
            return (json.dumps({'msg': 'Missing required fields.'}), 400, headers)

        # Connect to MongoDB
        client = MongoClient(mongo_uri)
        db = client.get_database('listings')
        users_collection = db['users']

        # Check if user already exists
        if users_collection.find_one({'$or': [{'email': email}, {'username': username}]}):
            return (json.dumps({'msg': 'User with this email or username already exists.'}), 409, headers)
            
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user document
        user_document = {
            'email': email,
            'username': username,
            'fullname': fullname,
            'password': hashed_password,
            'listings': [],
            'created_at': datetime.utcnow()
        }

        # Insert user into the database
        result = users_collection.insert_one(user_document)
        user_id = str(result.inserted_id)

        # Generate JWT token
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(days=7) # Token expires in 7 days
        }
        token = jwt.encode(payload, jwt_secret, algorithm='HS256')

        response_body = {
            'msg': 'User registered successfully.',
            'token': token
        }
        return (json.dumps(response_body), 200, headers)

    except BadRequest as e:
        return (json.dumps({'msg': str(e)}), 400, headers)
    except Exception as e:
        print(f"Error: {e}")
        response_body = {'msg': 'An internal error occurred.', 'error': str(e)}
        return (json.dumps(response_body), 500, headers)