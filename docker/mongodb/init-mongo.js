db.createUser({
    user: process.env.MONGO_INITDB_ROOT_USERNAME,
    pwd: process.env.MONGO_INITDB_ROOT_PASSWORD,
    roles: [
        {
            role: "readWrite",
            db: process.env.MONGO_INITDB_DATABASE
        }
    ]
});

// Create collections
db = db.getSiblingDB(process.env.MONGO_INITDB_DATABASE);

db.createCollection('conversations');
db.createCollection('chat_history');
db.createCollection('user_preferences');