from cryptography.fernet import Fernet, InvalidToken
import os
import json
from pathlib import Path

import sys
config_path = Path(__file__).parent.parent / "pywallet" / "config.py"
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from pywallet import config
    key_file = str(config.ENCRYPTION_KEY_FILE)
except ImportError:
    key_file = "config/encryption.key"

def load_or_generate_key():
    try:
        if os.path.exists(key_file):
            with open(key_file, 'rb') as file:
                key = file.read()

            try:
                f = Fernet(key)
                return f
            except Exception as e:
                print("Key is corrupted, Generating new key")
                key = Fernet.generate_key()

        else:
            print("Generating key")
            key = Fernet.generate_key()

        os.makedirs(os.path.dirname(key_file), exist_ok=True)

        with open(key_file, 'wb') as file:
            file.write(key)
        
        f = Fernet(key)
        return f
    
    except Exception as e:
        print("Error loading or generating key")
        key = Fernet.generate_key()

def encrypt_data(raw_json_string):
    f = load_or_generate_key()
    raw_bytes = raw_json_string.encode("utf-8")
    try:
        token = f.encrypt(raw_bytes)
        return token
    except TypeError as e:
        print("Data is not in bytes")

def decrypt_data(encrypted_bytes):
    f = load_or_generate_key()
    try:
        token = f.decrypt(encrypted_bytes)
        json_string = token.decode("utf-8")
        return json_string
    except InvalidToken:
        print("Data is not in bytes")


def save_encrypted(file_path, data_dict):
    raw_json = json.dumps(data_dict, indent=4)
    encrypted_bytes = encrypt_data(raw_json)
    with open(file_path, "wb") as file:
        file.write(encrypted_bytes)
    create_backup()

def load_encrypted(file_path):
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, "rb") as file:
        encrypted_bytes = file.read()

    json_string = decrypt_data(encrypted_bytes)
    return json.loads(json_string)


