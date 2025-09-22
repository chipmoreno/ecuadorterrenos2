import os
import functions_framework
import json
from pymongo import MongoClient
from bson.objectid import ObjectId
from auth import authenticate
from werkzeug.exceptions import BadRequest

@functions_framework.http
@authenticate
def edit_listing(request):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Allow-Methods': 'PATCH, OPTIONS'
    }

    if request.method == 'OPTIONS':
        return ('', 204, headers)

    try:
        mongo_uri = os.environ.get('MONGODB_URI')
        if not mongo_uri:
            raise ValueError('MONGODB_URI environment variable is not set.')
            
        request_json = request.get_json(silent=True)
        if not request_json:
            raise BadRequest('Invalid JSON payload.')

        # Get listing ID from the URL or query parameters
        listing_id = request.args.get('listingId')
        if not listing_id:
            return ('Listing ID is required.', 400, headers)

        # Connect to MongoDB
        client = MongoClient(mongo_uri)
        db = client.get_database('listings')
        listings_collection = db['terrenos']

        # Find the listing and verify ownership
        listing = listings_collection.find_one({'_id': ObjectId(listing_id)})
        if not listing:
            return ('Listing not found.', 404, headers)
        
        # This is the most critical security check
        if str(listing.get('user_id')) != request.user_id:
            return ('Forbidden. You do not own this listing.', 403, headers)

        # Update the listing with the provided data
        update_result = listings_collection.update_one(
            {'_id': ObjectId(listing_id)},
            {'$set': request_json}
        )

        if update_result.modified_count == 0:
            return ('No changes were made to the listing.', 200, headers)

        response_body = {'message': 'Listing updated successfully.'}
        return (json.dumps(response_body), 200, headers)

    except Exception as e:
        print(f"Error: {e}")
        response_body = {'message': 'An error occurred.', 'error': str(e)}
        return (json.dumps(response_body), 500, headers)