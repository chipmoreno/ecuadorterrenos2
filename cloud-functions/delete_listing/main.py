# main.py for delete_listing function

import os
import functions_framework
import json
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId
from auth import authenticate
from google.cloud import storage
from urllib.parse import urlparse # Needed to parse GCS URLs

# The decorator now handles ALL authentication and CORS logic.
@functions_framework.http
@authenticate
def delete_listing(request, user_id=None):
    """
    HTTP Cloud Function to delete a specific listing for the authenticated user.
    - The user_id is injected by the @authenticate decorator.
    - The listingId is passed as a URL query parameter.
    - Also deletes associated images from Google Cloud Storage.
    """
    
    if not user_id:
        # Safeguard, though the decorator should prevent this.
        return (json.dumps({'message': 'Authentication failed: User ID not provided.'}), 401)

    try:
        # 1. Retrieve environment variables
        mongo_uri = os.environ.get('MONGODB_URI')
        bucket_name = os.environ.get('GCP_BUCKET_NAME') # Needed for deleting photos

        if not all([mongo_uri, bucket_name]):
            raise EnvironmentError('Server configuration error: Missing environment variables.')

        # 2. Get listing ID from the URL query parameters
        listing_id = request.args.get('listingId')
        if not listing_id:
            return (json.dumps({'message': 'Listing ID is required.'}), 400)

        # 3. Connect to MongoDB
        client = MongoClient(mongo_uri)
        db = client.get_database('listings')
        listings_collection = db['terrenos']
        users_collection = db['users']

        # 4. Find the listing and verify ownership
        try:
            listing_object_id = ObjectId(listing_id)
            user_object_id = ObjectId(user_id)
        except InvalidId:
            return (json.dumps({'message': 'Invalid ID format provided.'}), 400)

        listing = listings_collection.find_one({'_id': listing_object_id})
        
        if not listing:
            return (json.dumps({'message': 'Listing not found.'}), 404)
        
        # This is the most critical security check
        if listing.get('user_id') != user_object_id:
            return (json.dumps({'message': 'Forbidden. You do not own this listing.'}), 403)

        # 5. BONUS: Delete associated photos from Google Cloud Storage
        photo_urls = listing.get('photos', [])
        if photo_urls:
            try:
                storage_client = storage.Client()
                bucket = storage_client.bucket(bucket_name)
                
                for url in photo_urls:
                    # Parse the URL to get the object path (e.g., 'listings/uuid.jpg')
                    parsed_url = urlparse(url)
                    blob_name = parsed_url.path.lstrip('/')
                    
                    if blob_name:
                        blob = bucket.blob(blob_name)
                        blob.delete()
                        print(f"Successfully deleted photo: {blob_name}")

            except Exception as e:
                # Log the error but don't stop the database deletion
                print(f"Warning: Failed to delete one or more photos from GCS for listing {listing_id}. Error: {e}")

        # 6. Delete the listing from the 'terrenos' collection
        delete_result = listings_collection.delete_one(
            {'_id': listing_object_id}
        )

        if delete_result.deleted_count == 0:
            # This might happen in a race condition, but it's good to handle
            return (json.dumps({'message': 'Listing was found but could not be deleted.'}), 500)

        # 7. Remove the listing reference from the user's document
        users_collection.update_one(
            {'_id': user_object_id},
            {'$pull': {'listings': listing_object_id}}
        )

        response_body = {'message': 'Listing deleted successfully.'}
        # The decorator will add CORS headers to this response
        return (json.dumps(response_body), 200)

    except EnvironmentError as e:
        return (json.dumps({'message': str(e)}), 500)
    except Exception as e:
        print(f"An unexpected error occurred in delete_listing: {e}")
        return (json.dumps({'message': 'An internal error occurred while deleting the listing.'}), 500)
