from pymongo import MongoClient

# 1. Your Firestore with MongoDB Compatibility connection string
MONGO_URI = 'mongodb://admin-user:x1P77S1tomPOzUa3nHZCBClH8UeYockBZH7AQgogz8B1GA7-@77e1067a-e0a0-4977-a057-7869e4995eb7.nam5.firestore.goog:443/listings?loadBalanced=true&tls=true&authMechanism=SCRAM-SHA-256&retryWrites=false'

# 2. Establish the connection to your database
client = MongoClient(MONGO_URI)

# 3. Select your database
# This is the 'listings' database you already have.
db = client['listings']

# 4. Select your new collection
# MongoDB will create this collection automatically on the first insert.
users_collection = db['users']

# 5. Define the user document to insert
# This is an example document. In a real application, you'd get this data from a user form.
test_user_document = {
    "userId": "test-user-id-12345",
    "name": "Juan Pérez",
    "email": "juan@example.com",
    "listings": [] 
}

# 6. Insert the document into the collection
try:
    result = users_collection.insert_one(test_user_document)
    print(f"User document inserted with _id: {result.inserted_id}")
    
except Exception as e:
    print(f"An error occurred: {e}")

# Don't forget to close the connection
client.close()