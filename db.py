# db.py
import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient

# Load .env ONLY for local development
load_dotenv()


def get_mongodb_uri():
    """
    Priority:
    1. Streamlit Cloud Secrets
    2. Local .env
    """
    try:
        if hasattr(st, "secrets") and "MONGODB_URI" in st.secrets:
            return st.secrets["MONGODB_URI"]
    except Exception:
        pass  # secrets.toml does not exist locally

    uri = os.getenv("MONGODB_URI")
    if uri:
        return uri

    raise RuntimeError(
        "MONGODB_URI not found. "
        "Add it to Streamlit Secrets or .env"
    )


def get_db_name():
    try:
        if hasattr(st, "secrets") and "MONGODB_DB" in st.secrets:
            return st.secrets["MONGODB_DB"]
    except Exception:
        pass

    return os.getenv("MONGODB_DB", "aiml_project")



# Initialize Mongo client
_client = MongoClient(
    get_mongodb_uri(),
    serverSelectionTimeoutMS=5000
)

_db = _client[get_db_name()]


def get_collection(name: str):
    """Return a collection by name, e.g. get_collection('users')."""
    return _db[name]


def get_mongo_collection():
    """
    Used by Home page to log searches.
    Returns (db, collection) for a default 'job_matches' collection.
    """
    collection_name = (
        st.secrets.get("MONGODB_COLLECTION")
        if "MONGODB_COLLECTION" in st.secrets
        else os.getenv("MONGODB_COLLECTION", "job_matches")
    )
    return _db, _db[collection_name]


class Database:
    """
    Simple wrapper for the 'users' collection.
    Passwords are stored in plain text here for simplicity.
    ⚠️ For real use, hash them with bcrypt.
    """

    def __init__(self):
        self.db = _db
        self.users = self.db["users"]

    def create_user(self, email: str, password: str, name: str | None = None):
        existing = self.users.find_one({"email": email})
        if existing:
            raise ValueError("Email already registered.")

        doc = {
            "email": email,
            "password": password,   # TODO: hash in real app
            "name": name or "",
            "created_at": datetime.utcnow(),
        }
        result = self.users.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    def authenticate_user(self, email: str, password: str):
        user = self.users.find_one({"email": email})
        if not user:
            return None
        if user.get("password") != password:
            return None
        return user
