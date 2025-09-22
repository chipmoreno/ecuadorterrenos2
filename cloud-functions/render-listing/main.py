# main.py
import os
from flask import Flask, render_template, abort
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv

# Load environment variables from a .env file for local development
load_dotenv()

# Initialize the Flask app
app = Flask(__name__)

# --- Database Connection ---
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.get_database("your_db_name") # Replace with your database name
listings_collection = db.get_collection("your_collection_name") # Replace with your collection name

# --- Custom Template Filter ---
# This is how you can add custom formatting functions to Jinja
@app.template_filter('format_price')
def format_price(value):
    """Formats a number with commas as thousands separators."""
    if isinstance(value, (int, float)):
        return f"{value:,}"
    return value

# --- The Main Route ---
# This defines a dynamic route. The part in < > is a variable.
@app.route("/anuncios/<listing_id>")
def serve_listing_page(listing_id):
    """
    Fetches a single listing from MongoDB and renders the HTML page.
    """
    try:
        # Validate that the provided ID is a valid MongoDB ObjectId
        if not ObjectId.is_valid(listing_id):
            abort(400, description="Invalid Listing ID format.")

        # Fetch the specific document from the collection
        query = {"_id": ObjectId(listing_id)}
        listing = listings_collection.find_one(query)

        # If no listing is found, return a 404 Not Found error
        if not listing:
            abort(404, description="Listing not found.")
        
        # If found, render the 'anuncio.html' template, passing the data to it
        return render_template("anuncio.html", listing=listing)

    except Exception as e:
        print(f"An error occurred: {e}")
        abort(500, description="An internal server error occurred.")

# To run this locally for testing:
# In your terminal, run: flask --app main run