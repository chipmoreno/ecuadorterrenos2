import os
import functions_framework
from pymongo import MongoClient
import json
import requests
from bson.objectid import ObjectId
from google.cloud import storage
import uuid
from auth import authenticate

@functions_framework.http
@authenticate
def submit_listing(request):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization', # <-- Add Authorization
        'Access-Control-Allow-Methods': 'POST'
    }

    if request.method == 'OPTIONS':
        return ('', 204, headers)
    
    # The rest of your existing try...except block
    try:
        request_data = dict(request.form)
        # ... (your existing code for geocoding and photo uploads) ...

        client = MongoClient(mongo_uri)
        db = client.get_database('listings')
        collection = db['terrenos']
        users_collection = db['users'] # <-- Add a reference to the users collection

        document = {
            **request_data,
            'location': {
                'type': 'Point',
                'coordinates': [longitude, latitude]
            },
            'fecha_publicacion': request.headers.get('x-client-timestamp', None),
            'photos': uploaded_photo_urls,
            'user_id': request.user_id # <-- Add the user_id here
        }

        # Insert the document
        result = collection.insert_one(document)

        # Update the user's document to add the new listing ID
        users_collection.update_one(
            {'_id': ObjectId(request.user_id)},
            {'$push': {'listings': result.inserted_id}}
        )

        response_body = {
            'message': '¡Anuncio enviado exitosamente!',
            'insertedId': str(result.inserted_id),
            'latitude': latitude,
            'longitude': longitude,
            'photo_urls': uploaded_photo_urls
        }
        return (json.dumps(response_body), 200, headers)

    except Exception as e:
        print(f"Error: {e}")
        response_body = {
            'message': 'Hubo un error al enviar el anuncio.',
            'error': str(e)
        }
        return (json.dumps(response_body), 500, headers)