# auth.py

import os
import jwt
from functools import wraps
from flask import request, jsonify, make_response

# --- MODIFICATION: Define a whitelist of trusted frontend domains ---
ALLOWED_ORIGINS = [
    'http://localhost:8081',          # Your local development server
    'https://www.ecuadorterrenos.com',  # Your production domain
    'https://ecuadorterrenos.com'      # In case you use the non-www version
]

def authenticate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # The first argument for a functions_framework function is the request object.
        # This code assumes it's a Flask-like request object.
        framework_request = args[0]
        
        origin = framework_request.headers.get('Origin')

        # --- MODIFICATION: Only proceed if the origin is trusted ---
        if origin not in ALLOWED_ORIGINS:
            # If the origin is not allowed, we don't add any CORS headers.
            # The browser will then block the request by default.
            # This is a security measure.
            return jsonify({'msg': 'CORS policy: Origin not allowed.'}), 403

        # --- MODIFICATION: Handle the preflight OPTIONS request correctly ---
        if framework_request.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': origin,
                'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Authorization, Content-Type',
                'Access-Control-Allow-Credentials': 'true', # Required for authenticated requests
                'Access-Control-Max-Age': '3600'
            }
            return ('', 204, headers)

        # --- MODIFICATION: Authenticate and then call the main function ---
        try:
            auth_header = framework_request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                raise ValueError('Unauthorized: No token provided.')
            
            token = auth_header.split(' ')[1]
            JWT_SECRET = os.environ.get('JWT_SECRET')
            if not JWT_SECRET:
                raise EnvironmentError('Server configuration error: JWT_SECRET not set.')
            
            decoded_token = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            user_id = decoded_token.get('user_id')
            if not user_id:
                raise ValueError('Unauthorized: Invalid token payload.')

            # Call the original protected function (e.g., submit_listing_v2)
            # Pass the user_id as a keyword argument for the function to use
            response_tuple = func(*args, user_id=user_id, **kwargs)
            
            # Create a Flask response object to easily add headers
            response = make_response(response_tuple)

        except (ValueError, jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
            response = make_response(jsonify({'msg': str(e)}), 401)
        except Exception as e:
            response = make_response(jsonify({'msg': 'An internal error occurred.', 'error': str(e)}), 500)

        # --- MODIFICATION: Add dynamic CORS headers to the FINAL response ---
        response.headers.set('Access-Control-Allow-Origin', origin)
        response.headers.set('Access-Control-Allow-Credentials', 'true')
        
        return response
        
    return wrapper