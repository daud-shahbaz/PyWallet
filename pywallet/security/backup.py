import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .encrypted_storage import encrypt_data, decrypt_data

import sys
from pathlib import Path as PathlibPath
config_path = PathlibPath(__file__).parent.parent / "pywallet" / "config.py"
sys.path.insert(0, str(PathlibPath(__file__).parent.parent))

try:
    from pywallet import config
    backup_dir = str(config.BACKUP_DIR)
    expenses_file = str(config.ENCRYPTED_DIR / "expenses.enc")
except ImportError:
    backup_dir = "data/backups/"
    expenses_file = "data/expenses.enc"

max_backups = 5

def ensure_backup_dir() -> None:
    """Create backup directory if it doesn't exist."""
    os.makedirs(backup_dir, exist_ok=True)

def create_backup() -> bool:
    """
    Create a backup of the main expenses file.
    
    Returns:
        bool: True if backup created successfully, False otherwise
    """
    ensure_backup_dir()

    if not os.path.exists(expenses_file):
        print("No main file exists, cannot create backup")
        return False

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = os.path.join(backup_dir, f"backup_{timestamp}.bin")

    try:
        shutil.copy2(expenses_file, backup_path)
        print(f"Backup created: {backup_path}")
        rotate_backups()
        return True
    except (OSError, IOError) as e:
        print(f"Failed to create backup: {e}")
        return False


def rotate_backups() -> None:
    """Keep only the most recent max_backups files."""
    try:
        backups = sorted(os.listdir(backup_dir))

        if len(backups) <= max_backups:
            return

        to_delete = backups[0:len(backups) - max_backups]
        for file in to_delete:
            try:
                os.remove(os.path.join(backup_dir, file))
                print(f"Old backup deleted: {file}")
            except (OSError, IOError):
                pass
    except OSError:
        pass


def list_backups() -> List[str]:
    """
    List all available backups.
    Returns:
        List of backup filenames
    """
    ensure_backup_dir()
    try:
        return sorted(os.listdir(backup_dir))
    except OSError:
        return []


def restore_backup(backup_filename: str) -> bool:
    """
    Restore expenses file from a backup.
    Args:
        backup_filename: Name of backup file to restore

    Returns:
        bool: True if restoration successful, False otherwise
    """
    ensure_backup_dir()

    # prevent path traversal
    if '..' in backup_filename or '/' in backup_filename or '\\' in backup_filename:
        print("Invalid backup filename")
        return False

    path = os.path.join(backup_dir, backup_filename)

    if not os.path.exists(path):
        print("Backup does not exist!")
        return False

    try:
        shutil.copy2(path, expenses_file)
        print(f"Restored backup: {backup_filename}")
        return True
    except (OSError, IOError) as e:
        print(f"Failed to restore backup: {e}")
        return False


def verify_backup(backup_filename: str) -> bool:
    """
    Check if a backup file is valid (decryptable).
    
    Args:
        backup_filename: Name of backup file to verify
    
    Returns:
        bool: True if backup is valid, False otherwise
    """
    # prevent path traversal
    if '..' in backup_filename or '/' in backup_filename or '\\' in backup_filename:
        print("Invalid backup filename")
        return False
    
    path = os.path.join(backup_dir, backup_filename)

    if not os.path.exists(path):
        print("Backup does not exist!")
        return False

    try:
        with open(path, "rb") as file:
            encrypted = file.read()
        decrypt_data(encrypted)
        print("Backup is valid and decryptable.")
        return True
    except:
        print("Backup is corrupted or unreadable.")
        return False



