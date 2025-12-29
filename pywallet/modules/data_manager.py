"""
Data Manager Module - Centralized data I/O operations.

Handles all persistence operations for expenses, users, and configuration.
Wraps existing utils.py patterns while providing clean, testable interface.
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
from pathlib import Path

from pywallet import config


class DataManager:
    """Centralized data I/O operations with error handling."""
    
    @staticmethod
    def load_data(filepath: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Load expense data from JSON file.
        
        Args:
            filepath: Path to JSON file (default: config.EXPENSES_FILE)
        
        Returns:
            List of expense dictionaries
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is invalid JSON
        """
        if filepath is None:
            filepath = config.EXPENSES_FILE
            
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            return []
        except json.JSONDecodeError:
            # File corrupted, return empty list
            return []
        except Exception as e:
            # Log error and return empty list
            print(f"Error loading data: {e}")
            return []
    
    @staticmethod
    def save_data(data: List[Dict[str, Any]], filepath: Optional[Path] = None) -> bool:
        """
        Save expense data to JSON file with validation.
        
        Args:
            data: List of expense dictionaries to save
            filepath: Path to JSON file (default: config.EXPENSES_FILE)
        
        Returns:
            True if successful, False otherwise
        """
        if filepath is None:
            filepath = config.EXPENSES_FILE
        
        try:
            # Ensure directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Validate data structure
            if not isinstance(data, list):
                raise ValueError("Data must be a list")
            
            # Save with pretty printing
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    @staticmethod
    def load_dataframe(filepath: Optional[Path] = None, username: str = "") -> pd.DataFrame:
        """
        Load expense data as Pandas DataFrame, optionally filtered by user.
        
        Args:
            filepath: Path to JSON file (default: config.EXPENSES_FILE)
            username: Filter by username (empty = all users)
        
        Returns:
            DataFrame with columns: id, amount, category, date, note, username
        """
        data = DataManager.load_data(filepath)
        
        # Filter by user if username provided
        if username:
            data = [e for e in data if e.get('username', '') == username]
        
        if not data:
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=['id', 'amount', 'category', 'date', 'note', 'username'])
        
        df = pd.DataFrame(data)
        
        # Ensure date column is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        return df
    
    @staticmethod
    def add_expense(
        amount: int,
        category: str,
        date: str,
        note: str = "",
        username: str = "",
        filepath: Optional[Path] = None
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Add a new expense to the data.
        
        Args:
            amount: Expense amount in PKR (validated against config)
            category: Expense category (must be in config.DEFAULT_CATEGORIES)
            date: Expense date (YYYY-MM-DD format)
            note: Optional expense note
            username: Username of expense owner (for user isolation)
            filepath: Path to data file
        
        Returns:
            Tuple of (success: bool, message: str, expense_id: Optional[int])
        """
        # Validate amount
        if not (config.MIN_EXPENSE_AMOUNT <= amount <= config.MAX_EXPENSE_AMOUNT):
            return False, f"Amount must be between {config.MIN_EXPENSE_AMOUNT} and {config.MAX_EXPENSE_AMOUNT}", None
        
        # Validate category
        if category not in config.DEFAULT_CATEGORIES:
            return False, f"Category must be one of {config.DEFAULT_CATEGORIES}", None
        
        # Validate date format
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return False, "Date must be in YYYY-MM-DD format", None
        
        # Validate note length
        if len(note) > config.MAX_NOTE_LENGTH:
            return False, f"Note must be less than {config.MAX_NOTE_LENGTH} characters", None
        
        try:
            data = DataManager.load_data(filepath)
            
            # Generate new ID
            new_id = max([e.get('id', 0) for e in data], default=0) + 1
            
            # Create expense object
            expense = {
                "id": new_id,
                "amount": int(amount),
                "category": str(category),
                "date": str(date),
                "note": str(note),
                "username": str(username)
            }
            
            data.append(expense)
            
            # Save data
            if DataManager.save_data(data, filepath):
                return True, f"Expense added successfully (ID: {new_id})", new_id
            else:
                return False, "Failed to save expense", None
                
        except Exception as e:
            return False, f"Error adding expense: {e}", None
    
    @staticmethod
    def delete_expense(expense_id: int, filepath: Optional[Path] = None) -> Tuple[bool, str]:
        """
        Delete an expense by ID.
        
        Args:
            expense_id: ID of expense to delete
            filepath: Path to data file
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            data = DataManager.load_data(filepath)
            
            # Find and remove expense
            original_length = len(data)
            data = [e for e in data if e.get('id') != expense_id]
            
            if len(data) == original_length:
                return False, f"Expense with ID {expense_id} not found"
            
            # Save updated data
            if DataManager.save_data(data, filepath):
                return True, f"Expense {expense_id} deleted successfully"
            else:
                return False, "Failed to delete expense"
                
        except Exception as e:
            return False, f"Error deleting expense: {e}"
    
    @staticmethod
    def get_expense(expense_id: int, filepath: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """
        Get a single expense by ID.
        
        Args:
            expense_id: ID of expense to retrieve
            filepath: Path to data file
        
        Returns:
            Expense dictionary or None if not found
        """
        data = DataManager.load_data(filepath)
        for expense in data:
            if expense.get('id') == expense_id:
                return expense
        return None
    
    @staticmethod
    def filter_expenses(
        filepath: Optional[Path] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_amount: Optional[int] = None,
        max_amount: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Filter expenses by various criteria.
        
        Args:
            filepath: Path to data file
            category: Filter by category
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            min_amount: Minimum amount in PKR
            max_amount: Maximum amount in PKR
        
        Returns:
            Filtered DataFrame
        """
        df = DataManager.load_dataframe(filepath)
        
        if df.empty:
            return df
        
        # Filter by category
        if category:
            df = df[df['category'] == category]
        
        # Filter by date range
        if start_date:
            df = df[df['date'] >= start_date]
        if end_date:
            df = df[df['date'] <= end_date]
        
        # Filter by amount range
        if min_amount is not None:
            df = df[df['amount'] >= min_amount]
        if max_amount is not None:
            df = df[df['amount'] <= max_amount]
        
        return df
    
    @staticmethod
    def export_to_csv(filepath: Optional[Path] = None, output_path: Optional[Path] = None) -> Tuple[bool, str]:
        """
        Export expenses to CSV file.
        
        Args:
            filepath: Source JSON file
            output_path: Destination CSV file
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            df = DataManager.load_dataframe(filepath)
            
            if df.empty:
                return False, "No data to export"
            
            if output_path is None:
                output_path = config.DATA_DIR / "expenses_export.csv"
            else:
                output_path = Path(output_path)
                # Validate output path doesn't contain traversal attempts
                if '..' in str(output_path):
                    return False, "Output path cannot contain '..' (path traversal not allowed)"
            
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(output_path, index=False)
                return True, f"Exported {len(df)} expenses to {output_path}"
            except (OSError, IOError) as e:
                return False, f"Cannot write to output path: {e}"
        except Exception as e:
            return False, f"Export failed: {e}"
    
    @staticmethod
    def import_from_csv(csv_path: Path, filepath: Optional[Path] = None) -> Tuple[bool, str, int]:
        """
        Import expenses from CSV file.
        
        Args:
            csv_path: Path to CSV file to import
            filepath: Destination JSON file
        
        Returns:
            Tuple of (success: bool, message: str, imported_count: int)
        """
        try:
            # Validate input path
            csv_path = Path(csv_path)
            if not csv_path.exists():
                return False, f"CSV file not found: {csv_path}", 0
            if not csv_path.is_file():
                return False, f"Path is not a file: {csv_path}", 0
            if csv_path.suffix.lower() != '.csv':
                return False, f"File must be a CSV file, got: {csv_path.suffix}", 0
            
            if filepath is None:
                filepath = config.EXPENSES_FILE
            
            # Read CSV
            import_df = pd.read_csv(csv_path)
            
            # Validate required columns
            required_columns = ['amount', 'category', 'date']
            if not all(col in import_df.columns for col in required_columns):
                return False, f"CSV must have columns: {required_columns}", 0
            
            # Load existing data
            existing_data = DataManager.load_data(filepath)
            next_id = max([e.get('id', 0) for e in existing_data], default=0) + 1
            
            # Process import data
            imported_count = 0
            for _, row in import_df.iterrows():
                try:
                    expense = {
                        'id': next_id,
                        'amount': int(row['amount']),
                        'category': str(row['category']),
                        'date': str(row['date']),
                        'note': str(row.get('note', ''))
                    }
                    existing_data.append(expense)
                    next_id += 1
                    imported_count += 1
                except (ValueError, TypeError, KeyError):
                    continue
            
            # Save merged data
            if DataManager.save_data(existing_data, filepath):
                return True, f"Imported {imported_count} expenses successfully", imported_count
            else:
                return False, "Failed to save imported data", 0
                
        except pd.errors.EmptyDataError:
            return False, "CSV file is empty", 0
        except pd.errors.ParserError as e:
            return False, f"CSV parsing error: {e}", 0
        except (OSError, IOError) as e:
            return False, f"File access error: {e}", 0
        except Exception as e:
            return False, f"Import failed: {e}", 0


# ============================================================================
# BACKWARD COMPATIBILITY FUNCTIONS (wrapping DataManager for legacy code)
# ============================================================================

def load_data(filepath: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Backward compatible wrapper for DataManager.load_data()"""
    return DataManager.load_data(filepath)


def save_data(data: List[Dict[str, Any]], filepath: Optional[Path] = None) -> bool:
    """Backward compatible wrapper for DataManager.save_data()"""
    return DataManager.save_data(data, filepath)


def load_dataframe(filepath: Optional[Path] = None, username: str = "") -> pd.DataFrame:
    """Backward compatible wrapper for DataManager.load_dataframe()"""
    return DataManager.load_dataframe(filepath, username)

