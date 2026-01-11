# db.py
import os
from datetime import datetime
from functools import lru_cache

import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


def _get_secret(key: str, default=None):
    try:
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)


@lru_cache(maxsize=1)
def get_client():
    uri = _get_secret("MONGODB_URI")
    if not uri:
        raise RuntimeError("MONGODB_URI not set")

    return MongoClient(uri, serverSelectionTimeoutMS=3000)


_db = get_client()[_get_secret("MONGODB_DB", "aiml_project")]


def get_collection(name: str):
    return _db[name]


def get_mongo_collection():
    collection = _get_secret("MONGODB_COLLECTION", "job_matches")
    return _db, _db[collection]


class Database:
    def __init__(self):
        self.users = _db["users"]

    def create_user(self, email, password, name=None):
        if self.users.find_one({"email": email}):
            raise ValueError("Email already registered")

        doc = {
            "email": email,
            "password": password,
            "name": name or "",
            "created_at": datetime.utcnow(),
        }
        self.users.insert_one(doc)
        return doc

    def authenticate_user(self, email, password):
        user = self.users.find_one({"email": email})
        if not user or user["password"] != password:
            return None
        return user
