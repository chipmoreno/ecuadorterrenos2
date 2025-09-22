# auth.py
from functools import wraps
import jwt
import os
from flask import jsonify

def authenticate(func):
    @wraps(func)
    def wrapper(request):
        # Allow OPTIONS requests to pass through without authentication
        if request.method == 'OPTIONS':
            return func(request)

        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'msg': 'Unauthorized: No token provided.'}), 401

        try:
            JWT_SECRET = os.environ.get('JWT_SECRET')
            if not JWT_SECRET:
                return jsonify({'msg': 'JWT_SECRET environment variable not set.'}), 500
            
            decoded_token = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            # NOTE: Use 'user_id' to match your login_user function's payload
            request.user_id = decoded_token.get('user_id')
            
            if not request.user_id:
                return jsonify({'msg': 'Unauthorized: Invalid token payload.'}), 401
        
        except jwt.ExpiredSignatureError:
            return jsonify({'msg': 'Unauthorized: Token has expired.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'msg': 'Unauthorized: Invalid token.'}), 401
        except Exception as e:
            print(f"Token validation error: {e}")
            return jsonify({'msg': 'Unauthorized: Authentication failed.'}), 500
        
        return func(request)
    return wrapper