import os
from pymongo import MongoClient 
from dotenv import load_dotenv

load_dotenv()

CONNECTION_STRING = os.environ.get("CONNECTION_STRING")

client = MongoClient(CONNECTION_STRING)
mydatabase = client['mydatabase']
collection = mydatabase['collection']

def set_status(user_id, status):
    """Set the status of a user in the database."""
    collection.update_one(
        {"user_id": user_id},
        {"$set": {"status": status}},
        upsert=True
    )

def get_user_data(user_id):
    """Get the current data of a user from the database."""
    return collection.find_one({"user_id": user_id}) or {}

def add_tag(user_id, tag):
    """Add a tag to the user's tracked list."""
    collection.update_one(
        {"user_id": user_id},
        {"$set": {"status": "tracking"}, "$addToSet": {"tags": tag}},
        upsert=True
    )

def remove_all_tags(user_id):
    """Remove all tags for a user."""
    collection.update_one(
        {"user_id": user_id},
        {"$set": {"tags": []}}
    )

def remove_specific_tag(user_id, tag):
    """Remove a specific tag for a user."""
    collection.update_one(
        {"user_id": user_id},
        {"$pull": {"tags": tag}}
    )

def get_all_users():
    # Example implementation for a MongoDB database
    users = collection.find()  # Assuming `users` collection stores user data
    all_users = {}

    for user in users:
        user_id = user.get("user_id")
        user_data = {
            "tags": user.get("tags", []),
            "status": user.get("status", None)
        }
        all_users[user_id] = user_data

    return all_users
