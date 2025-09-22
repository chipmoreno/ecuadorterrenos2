import os
import functions_framework
from pymongo import MongoClient
import json
from bson import json_util

@functions_framework.http
def fetch_listings(request):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET'
    }

    if request.method == 'OPTIONS':
        return ('', 204, headers)

    try:
        mongo_uri = os.environ.get('MONGO_URI')
        if not mongo_uri:
            raise ValueError('MONGO_URI environment variable is not set.')

        client = MongoClient(mongo_uri)
        db = client.get_database('listings')
        collection = db['terrenos']

        # Find all documents in the collection
        listings_cursor = collection.find({})
        
        # Use json_util to handle MongoDB's ObjectId and other BSON types
        listings_list = json.loads(json_util.dumps(listings_cursor))

        return (json.dumps(listings_list), 200, headers)

    except Exception as e:
        print(f"Error fetching listings: {e}")
        response_body = {
            'message': 'Hubo un error al obtener los anuncios.',
            'error': str(e)
        }
        return (json.dumps(response_body), 500, headers)