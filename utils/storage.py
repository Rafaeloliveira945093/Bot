import json
import os
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Simple JSON file storage for bot data
STORAGE_FILE = "bot_data.json"

def load_bot_data() -> Dict[str, Any]:
    """Load bot data from storage file."""
    try:
        if os.path.exists(STORAGE_FILE):
            with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading bot data: {e}")
        return {}

def save_bot_data(data: Dict[str, Any]) -> bool:
    """Save bot data to storage file."""
    try:
        with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving bot data: {e}")
        return False

def get_destination_group() -> Optional[int]:
    """Get the registered destination group ID."""
    data = load_bot_data()
    return data.get("destination_group_id")

def set_destination_group(group_id: int) -> bool:
    """Set the destination group ID."""
    data = load_bot_data()
    data["destination_group_id"] = group_id
    return save_bot_data(data)

def get_user_data(user_id: int, key: str, default=None):
    """Get user-specific data."""
    data = load_bot_data()
    return data.get(f"user_{user_id}", {}).get(key, default)

def set_user_data(user_id: int, key: str, value) -> bool:
    """Set user-specific data."""
    data = load_bot_data()
    if f"user_{user_id}" not in data:
        data[f"user_{user_id}"] = {}
    data[f"user_{user_id}"][key] = value
    return save_bot_data(data)

def get_destination_groups() -> Dict[str, int]:
    """Get all registered destination groups."""
    data = load_bot_data()
    return data.get('destination_groups', {})

def set_destination_groups(groups_dict: Dict[str, int]) -> bool:
    """Set the destination groups dictionary."""
    data = load_bot_data()
    data['destination_groups'] = groups_dict
    return save_bot_data(data)

def add_destination_group(name: str, group_id: int) -> bool:
    """Add a new destination group."""
    groups = get_destination_groups()
    groups[name] = group_id
    return set_destination_groups(groups)

def remove_destination_group(name: str) -> bool:
    """Remove a destination group."""
    groups = get_destination_groups()
    if name in groups:
        del groups[name]
        return set_destination_groups(groups)
    return False