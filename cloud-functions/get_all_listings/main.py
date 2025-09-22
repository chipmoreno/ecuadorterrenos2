# main.py inside cloud-functions/get_all_listings/
from flask import jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId # Ensure this is imported
import os
import json

# Function to establish a MongoDB connection
def get_database():
    MONGO_URI = os.environ.get('MONGODB_URI')
    client = MongoClient(MONGO_URI)
    return client.get_database()

def get_all_listings(request):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600'
    }

    if request.method == 'OPTIONS':
        return ('', 204, headers)

    db = get_database()
    terrenos_collection = db.terrenos
    
    try:
        listings_cursor = terrenos_collection.find({})
        listings_list = []
        for doc in listings_cursor:
            # THIS IS THE CRITICAL FIX: Convert ObjectId to string
            doc['_id'] = str(doc['_id'])
            
            # Additional Fix: Convert other BSON types if they exist
            # For example, if you have a `user_id` which is an ObjectId
            if 'user_id' in doc and isinstance(doc['user_id'], ObjectId):
                doc['user_id'] = str(doc['user_id'])
                
            listings_list.append(doc)

        response_body = {"listings": listings_list}
        return jsonify(response_body), 200, headers
    
    except Exception as e:
        # A good practice is to return a clear, JSON-formatted error
        print(f"Error during listing fetch: {e}")
        return jsonify({"message": f"An error occurred: {e}"}), 500, headers