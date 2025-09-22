
const { MongoClient } = require('mongodb');

const uri = "mongodb+srv://chipmoreno_db_user:HykwdNGLHrS6muKP@cluster0.g9pj6vg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"; // Replace with your full connection string
const client = new MongoClient(uri);

async function run() {
  try {
    await client.connect();
    console.log("Connected successfully to MongoDB Atlas!");
    // You can return the database object here for use in your app
    return client.db("EcuadorTerrenos"); // Replace with your desired database name
  } catch (e) {
    console.error("Connection failed!", e);
  }
}

// Call the function to connect
const db = run();

module.exports = db;