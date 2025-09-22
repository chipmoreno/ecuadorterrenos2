# main.py for get_my_listings function (CORRECTED)

import os
import functions_framework
import json
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId
from auth import authenticate
from datetime import datetime

@functions_framework.http
@authenticate
def get_my_listings(request, user_id=None):
    if not user_id:
        return (json.dumps({'message': 'Authentication failed: User ID not provided.'}), 401)

    try:
        mongo_uri = os.environ.get('MONGODB_URI')
        if not mongo_uri:
            raise EnvironmentError('Server configuration error: MONGODB_URI not set.')

        client = MongoClient(mongo_uri)
        db = client.get_database('listings')
        listings_collection = db['terrenos']

        try:
            user_object_id = ObjectId(user_id)
        except InvalidId:
            return (json.dumps({'message': 'Invalid user identifier.'}), 400)

        user_listings_cursor = listings_collection.find(
            {'user_id': user_object_id}
        ).sort('fecha_publicacion', -1)

        # --- THIS IS THE KEY MODIFICATION ---
        # Manually build the list to ensure all ObjectIds and datetimes are converted to strings.
        listings_list = []
        for listing in user_listings_cursor:
            # Convert ObjectId fields to simple strings
            listing['_id'] = str(listing['_id'])
            listing['user_id'] = str(listing['user_id'])
            
            # Convert datetime to a standard string format (ISO 8601)
            if 'fecha_publicacion' in listing and isinstance(listing['fecha_publicacion'], datetime):
                listing['fecha_publicacion'] = listing['fecha_publicacion'].isoformat()
            
            listings_list.append(listing)
        
        response_body = {'listings': listings_list}
        return (json.dumps(response_body), 200)

    except EnvironmentError as e:
        return (json.dumps({'message': str(e)}), 500)
    except Exception as e:
        print(f"An unexpected error occurred in get_my_listings: {e}")
        return (json.dumps({'message': 'An internal error occurred while fetching listings.'}), 500)