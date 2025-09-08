// MongoDB initialization script
// This script runs when the MongoDB container starts for the first time

// Switch to the hetzner database
db = db.getSiblingDB('hetzner');

// Create a user for the application
db.createUser({
  user: 'hetzner_bot',
  pwd: 'hetzner_bot_password',
  roles: [
    {
      role: 'readWrite',
      db: 'hetzner'
    }
  ]
});

// Create the hetzner collection with some basic indexes
db.hetzner.createIndex({ "user_id": 1 });
db.hetzner.createIndex({ "timestamp": 1 });
db.hetzner.createIndex({ "user_id": 1, "timestamp": 1 });

print('MongoDB initialization completed successfully!');