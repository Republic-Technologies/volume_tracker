"""
Authentication Helper Module for Stockwatch

Loads username and password from secrets.json file.
"""

import json
import os
from typing import Dict, Any


def load_stockwatch_auth() -> Dict[str, str]:
    """
    Load Stockwatch username and password from secrets.json file.
    
    Returns:
        Dictionary with 'username' and 'password' keys
        
    Raises:
        FileNotFoundError: If secrets.json file doesn't exist
        json.JSONDecodeError: If secrets.json contains invalid JSON
        ValueError: If secrets.json doesn't contain username and password
    """
    secrets_file = "secrets.json"
    
    # Check if file exists
    if not os.path.isfile(secrets_file):
        raise FileNotFoundError(
            f"Authentication file '{secrets_file}' not found.\n"
            f"Please create {secrets_file} with your Stockwatch username and password:\n"
            f'  {{\n'
            f'    "username": "your_username",\n'
            f'    "password": "your_password"\n'
            f'  }}'
        )
    
    # Read and parse JSON file
    try:
        with open(secrets_file, 'r', encoding='utf-8') as f:
            auth_data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in {secrets_file}: {e.msg}",
            e.doc,
            e.pos
        )
    
    # Validate that we have username and password
    if not isinstance(auth_data, dict):
        raise ValueError(
            f"{secrets_file} must contain a JSON object (dictionary).\n"
            f"Found: {type(auth_data).__name__}"
        )
    
    if "username" not in auth_data or "password" not in auth_data:
        raise ValueError(
            f"{secrets_file} must contain 'username' and 'password' fields:\n"
            f'  {{\n'
            f'    "username": "your_username",\n'
            f'    "password": "your_password"\n'
            f'  }}'
        )
    
    return auth_data

