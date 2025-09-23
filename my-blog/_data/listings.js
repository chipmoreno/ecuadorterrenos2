// This script runs once at build time to fetch all listings from MongoDB.
// It requires the 'mongodb' package: npm install mongodb

const { MongoClient } = require('mongodb');

// A simple function to create a URL-friendly "slug" from a title
function slugify(text) {
  return text
    .toString()
    .toLowerCase()
    .replace(/\s+/g, '-')      // Replace spaces with -
    .replace(/[^\w-]+/g, '')   // Remove all non-word chars
    .replace(/--+/g, '-')      // Replace multiple - with single -
    .replace(/^-+/, '')        // Trim - from start of text
    .replace(/-+$/, '');       // Trim - from end of text
}

// Your MongoDB connection string. Use an environment variable for security.
const MONGO_URI = process.env.MONGODB_URI;

if (!MONGO_URI) {
  throw new Error("Missing environment variable MONGODB_URI");
}

module.exports = async function() {
  console.log("Connecting to MongoDB to fetch listings...");

  const client = new MongoClient(MONGO_URI);
  
  try {
    await client.connect();
    const db = client.db('listings');
    const listingsCollection = db.collection('terrenos');
    
    // Fetch all listings. You might want to filter for "active" listings in the future.
    const listings = await listingsCollection.find({}).toArray();
    
    console.log(`Fetched ${listings.length} listings from the database.`);
    
    // Process each listing to add a slug and ensure IDs are strings
    return listings.map(listing => {
      return {
        ...listing,
        _id: listing._id.toString(), // Convert ObjectId to string
        user_id: listing.user_id.toString(), // Convert ObjectId to string
        // Create a unique, SEO-friendly slug for the URL
        slug: `${slugify(listing.titulo)}-${listing._id.toString().slice(-6)}`
      };
    });

  } catch (err) {
    console.error("Error fetching listings from MongoDB:", err);
    return []; // Return an empty array on error
  } finally {
    await client.close();
  }
};