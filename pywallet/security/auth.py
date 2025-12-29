import json
from pathlib import Path
from .password_hashing import verify_password, hash_password

# Import config from parent pywallet package
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from pywallet import config
    user_file = str(config.USERS_FILE)
    session_file = str(config.SESSION_FILE)
except ImportError:
    user_file = 'security/users.json'
    session_file = 'security/session.json'

def register(username, password):
    """
    Register a new user account.
    
    Args:
        username: Username for new account (unique)
        password: Password for new account
    
    Returns:
        bool: True if registration successful, False otherwise
    """
    if not username or len(username) < 3:
        return False
    
    if not password or len(password) < 8:
        return False
    
    try:
        with open(user_file,'r') as file:
            users = json.load(file)
            if not isinstance(users, list):
                users = []
    except FileNotFoundError:
        users = []
    except json.JSONDecodeError:
        users = []

    if any(user.get("username") == username for user in users):
        return False
    
    users.append({"username": username, "password": hash_password(password)})

    try:
        with open(user_file,'w') as file:
            json.dump(users, file, indent=4)
        return True
    except IOError as e:
        return False
    except Exception as e:
        return False

def login(username, password):
    """
    Authenticate user with username and password.
    
    Args:
        username: Username to authenticate
        password: Password to verify
    
    Returns:
        bool: True if authentication successful, False otherwise
    """
    try:
        with open(user_file,'r') as file:
            users = json.load(file)
            if not isinstance(users, list):
                users = []

            user = next((u for u in users if u.get("username") == username), None)
            
            if user:
                stored_hash = user["password"]

                if verify_password(password, stored_hash):
                        set_session(username)
                        return True
                else:
                    return False
                
            return False
    except FileNotFoundError:
        return False
    except json.JSONDecodeError:
        return False
    except Exception as e:
        return False

def is_logged_in():
    try:
        with open(session_file, 'r') as file:
            session = json.load(file)
            return session.get("logged_in", False)
    except (FileNotFoundError, json.JSONDecodeError):
        return False

def set_session(username):
    session = {
        "logged_in": True,
        "username": username
    }
    with open(session_file, 'w') as file:
        json.dump(session, file, indent=4)


def logout():
    session = {
        "logged_in": False,
        "username": None
        }

    with open(session_file,'w') as file:
        json.dump(session, file, indent=4)

def get_current_user():
    """Get the currently logged-in user."""
    try:
        with open(session_file, 'r') as file:
            session = json.load(file)
            if session.get("logged_in"):
                return session.get("username")
            return None
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def main():
    if is_logged_in():
        print("You are already logged in!")
        return
    
    username = input("Enter username: ")
    password = input("Enter password: ")
    login(username, password)

if __name__ == "__main__":
    main()
