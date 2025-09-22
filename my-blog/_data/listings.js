// FILE: _data/listings.js (CORRECTED)

const { MongoClient } = require('mongodb');

function slugify(text) {
  return text
    .toString()
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^\w-]+/g, '')
    .replace(/--+/g, '-')
    .replace(/^-+/, '')
    .replace(/-+$/, '');
}

const MONGO_URI = process.env.MONGODB_URI;
if (!MONGO_URI) {
  throw new Error("Missing environment variable MONGODB_URI");
}

module.exports = async function() {
  console.log("Connecting to MongoDB to fetch listings...");
  const client = new MongoClient(MONGO_URI);
  
  try {
    await client.connect();
    
    // ===================================================================
    // THIS IS THE CORRECTED LINE:
    // Changed client.getDatabase('listings') to client.db('listings')
    const db = client.db('listings'); 
    // ===================================================================

    // IMPORTANT: If your database is not named 'listings', change it in the line above.

    const listingsCollection = db.collection('terrenos');
    const listings = await listingsCollection.find({}).toArray();
    
    console.log(`✅ Fetched ${listings.length} listings from the database.`);
    
    return listings.map(listing => {
      // Ensure _id and user_id exist before converting
      const listingId = listing._id ? listing._id.toString() : '';
      const userId = listing.user_id ? listing.user_id.toString() : '';
      
      return {
        ...listing,
        _id: listingId,
        user_id: userId,
        slug: `${slugify(listing.titulo)}-${listingId.slice(-6)}`
      };
    });

  } catch (err) {
    console.error("Error fetching listings from MongoDB:", err);
    return [];
  } finally {
    await client.close();
  }
};