# save_tools.py
from __future__ import annotations
from datetime import datetime

from db import get_collection


def ensure_indexes(col):
    """Create helpful indexes for saved_jobs collection."""
    try:
        col.create_index("user_email")
        col.create_index("created_at")
    except Exception:
        # Don't crash if index creation fails
        pass


def save_single_job(user_email: str, match_obj: dict, context: dict | None = None):
    """
    Save one matched job for a user into 'saved_jobs' collection.
    We use user_email as the key, to avoid ObjectId / string mismatch issues.
    """
    if not user_email:
        raise ValueError("User email is required to save jobs.")

    col = get_collection("saved_jobs")
    ensure_indexes(col)

    doc = {
        "user_email": user_email,
        "job": match_obj,
        "meta": context or {},
        "created_at": datetime.utcnow(),
    }
    col.insert_one(doc)
