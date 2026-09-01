"""
Serialization utilities for converting data to JSON-serializable format.
"""
import json
from datetime import datetime


def serialize_item_data(item_dict):
    """Serialize item data to JSON string"""
    return json.dumps(item_dict, ensure_ascii=False, default=str)


def json_safe(obj):
    """Turn datetimes and other objects into JSON-compatible values."""
    return json.loads(
        json.dumps(
            obj,
            default=lambda o: o.isoformat() if isinstance(o, datetime) else str(o),
        )
    )
