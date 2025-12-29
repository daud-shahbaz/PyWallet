from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHash

ph = PasswordHasher()

def hash_password(password):
    hashed = ph.hash(password)
    # print("HASH:", hashed)
    return hashed

def verify_password(password, stored_hash):
    try:
        ph.verify(stored_hash, password)
        print("Password verified")
        return True
    except VerifyMismatchError as e:
        print("Wrong password")
        return False
    except InvalidHash:
        print("Stored password hash is corrupted!")
        return False

def main():
    """Main demo function for password hashing"""
    password = input("Set Password: ")
    stored_hash = hash_password(password)

    if stored_hash:
        print("\n --- Login Attempt ---")
        attempt = input("Enter Password: ")
        result = verify_password(attempt, stored_hash)
        
        if result:
            print("Access Granted!")
        else:
            print("Access Denied!")

if __name__ == "__main__":
    main()

