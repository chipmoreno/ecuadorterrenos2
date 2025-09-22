# main.py for submit_listing_v2 function

import os
import functions_framework
import json
import requests
from pymongo import MongoClient
from bson.objectid import ObjectId
from google.cloud import storage
import uuid
from auth import authenticate
from datetime import datetime # Import datetime for timestamps

# The decorator now handles ALL authentication and CORS logic.
# The function's only job is to handle the business logic of creating a listing.
@functions_framework.http
@authenticate
def submit_listing_v2(request, user_id=None):
    # --- MODIFICATION: All CORS headers are removed from here. The decorator handles them. ---
    
    # --- MODIFICATION: The user_id is now passed directly from the decorator ---
    if not user_id:
        # This case should ideally never be hit if the decorator works correctly
        return json.dumps({'message': 'Authentication failed.'}), 401

    try:
        # Retrieve environment variables
        mongo_uri = os.environ.get('MONGODB_URI')
        geocoding_api_key = os.environ.get('GEOCODING_API_KEY')
        bucket_name = os.environ.get('GCP_BUCKET_NAME')

        if not all([mongo_uri, geocoding_api_key, bucket_name]):
            raise EnvironmentError('Server configuration error: Missing environment variables.')

        # 1. Get data from form fields
        request_data = request.form
        
        # Geocoding API Call
        direccion = request_data.get('direccion')
        if not direccion:
            raise ValueError('Direccion is a required field for geocoding.')

        geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={direccion}, Ecuador&key={geocoding_api_key}"
        geo_response = requests.get(geocode_url)
        geo_response.raise_for_status() # Raise an exception for bad status codes
        
        geo_results = geo_response.json().get('results')
        if not geo_results:
            raise ValueError(f"Could not geocode the address: {direccion}")
        
        location = geo_results[0]['geometry']['location']
        
        # 2. Upload photos to Google Cloud Storage
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        uploaded_photo_urls = []

        # --- MODIFICATION: Correctly handle MULTIPLE file uploads ---
        photos = request.files.getlist('fotos') # Use getlist for multiple files with the same name
        for photo in photos:
            # Secure the filename and create a unique name
            filename = photo.filename.rsplit(".", 1)[-1].lower()
            blob_name = f'listings/{uuid.uuid4()}.{filename}'
            blob = bucket.blob(blob_name)
            
            # Upload the file
            blob.upload_from_file(photo.stream, content_type=photo.content_type)
            uploaded_photo_urls.append(blob.public_url)
        
        # 3. Connect to MongoDB and insert listing
        client = MongoClient(mongo_uri)
        db = client.get_database('listings') # Or your DB name
        listings_collection = db['terrenos']
        users_collection = db['users']

        # --- MODIFICATION: Fetch user details from DB instead of form ---
        # This is more secure and reliable.
        user_object_id = ObjectId(user_id)
        user = users_collection.find_one({'_id': user_object_id})
        if not user:
            raise ValueError("Authenticated user not found in database.")

        # --- MODIFICATION: Create a cleaner document, removing redundant contact fields ---
        document = {
            'user_id': user_object_id,
            'titulo': request_data.get('titulo'),
            'descripcion': request_data.get('descripcion'),
            'provincia': request_data.get('provincia'),
            'ciudad': request_data.get('ciudad'),
            'direccion': direccion,
            'area': int(request_data.get('area', 0)),
            'precio': int(request_data.get('precio', 0)),
            'location': {
                'type': 'Point',
                'coordinates': [location['lng'], location['lat']]
            },
            'photos': uploaded_photo_urls,
            'fecha_publicacion': datetime.utcnow(),
            'seller_info': {
                'name': user.get('fullname'),
                'email': user.get('email')
                # Add phone from user profile later if you store it
            }
        }

        result = listings_collection.insert_one(document)

        # Link this new listing back to the user who created it
        users_collection.update_one(
            {'_id': user_object_id},
            {'$push': {'listings': result.inserted_id}}
        )

        response_body = {
            'message': '¡Anuncio enviado exitosamente!',
            'listingId': str(result.inserted_id)
        }
        # The decorator will handle adding headers to this response
        return (json.dumps(response_body), 201)

    except (ValueError, EnvironmentError) as e:
        # Handle bad client requests or config errors
        return (json.dumps({'message': str(e)}), 400)
    except Exception as e:
        # Handle unexpected server errors
        print(f"An unexpected error occurred: {e}")
        return (json.dumps({'message': 'Hubo un error interno al procesar el anuncio.'}), 500)
