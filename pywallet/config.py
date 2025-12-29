"""
PyWallet Configuration Module
Central configuration for the entire application.
Keep this file as the single source of truth for settings.
"""

from pathlib import Path
from typing import List, Dict
from pywallet.utils.logger import setup_logger

# Initialize logger
logger = setup_logger("pywallet")

# ============================================================================
#                                 Paths
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "pywallet" / "data"
BACKUP_DIR = DATA_DIR / "backups"
ENCRYPTED_DIR = DATA_DIR / "encrypted"

DATA_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
ENCRYPTED_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
#                                     Data
# ============================================================================

EXPENSES_FILE = DATA_DIR / "expenses.json"
USERS_FILE = DATA_DIR / "users.json"
SESSION_FILE = DATA_DIR / "session.json"
BUDGET_FILE = DATA_DIR / "budget.json"
ENCRYPTION_KEY_FILE = DATA_DIR / "encryption.key"

# ============================================================================
#                               Settings
# ============================================================================

# Currency
DEFAULT_CURRENCY = "PKR"
SUPPORTED_CURRENCIES = ["PKR", "USD", "EUR", "GBP"]

# Timezone
DEFAULT_TIMEZONE = "Asia/Karachi"
SUPPORTED_TIMEZONES = [
    "Asia/Karachi",
    "UTC",
    "America/New_York",
    "Asia/Dubai",
]

# Categories
DEFAULT_CATEGORIES: List[str] = [
    "Food",
    "Transport",
    "Health",
    "Education",
    "Housing",
    "Entertainment",
    "Savings",
    "Shopping",
    "Travel",
    "Gifts",
    "Utilities",
    "Insurance",
    "Other",
]

# Default budgets per category (PKR)
DEFAULT_BUDGETS: Dict[str, float] = {
    "Food": 10000,
    "Transport": 5000,
    "Health": 3000,
    "Education": 5000,
    "Housing": 20000,
    "Entertainment": 2000,
    "Savings": 10000,
    "Shopping": 3000,
    "Travel": 5000,
    "Gifts": 2000,
    "Utilities": 3000,
    "Insurance": 2000,
    "Other": 1000,
}

# ============================================================================
#                              Security 
# ============================================================================

# Password hashing
PASSWORD_HASH_ALGORITHM = "argon2id"
PASSWORD_HASH_TIME_COST = 3  # Number of passes
PASSWORD_HASH_MEMORY_COST = 65536  #64MB

# Backup 
MAX_BACKUPS = 5
BACKUP_EXTENSION = ".backup"

# ============================================================================
#                                  ML 
# ============================================================================

# Anomaly threshold (std from mean)
ANOMALY_THRESHOLD_SIGMA = 2.0

# Category classifier 
MIN_NOTES_FOR_TRAINING = 50  # Min notes to train classifier
CATEGORY_CLASSIFIER_MODEL = "naive_bayes"  # naive_bayes/svm/logistic_regression

# Clustering 
KMEANS_CLUSTERS = 3  # Number of spending behavior clusters
MIN_DATA_POINTS_FOR_ML = 20  # Minimum data points

# Prediction 
PREDICTION_WINDOW_MONTHS = 6  # Months of history
FORECAST_AHEAD_MONTHS = 3  # months to forecast

# ============================================================================
#                                 Streamlit
# ============================================================================

STREAMLIT_PAGE_ICON = "$"
STREAMLIT_PAGE_TITLE = "PyWallet - Money Manager"
STREAMLIT_LAYOUT = "wide"
STREAMLIT_SIDEBAR_STATE = "expanded"

# ============================================================================
#                                logs
# ============================================================================

LOG_LEVEL = "INFO"
LOG_FILE = PROJECT_ROOT / "logs" / "pywallet.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# ============================================================================
#                              validation
# ============================================================================

# Expense
MIN_EXPENSE_AMOUNT = 0
MAX_EXPENSE_AMOUNT = 1000000
MAX_NOTE_LENGTH = 500

# Date range
MAX_FUTURE_DAYS = 90  # Can't add expenses more than 90 days in future
MAX_PAST_YEARS = 10  # Can't add expenses more than 10 years in past

# ============================================================================
# FEATURE FLAGS
# ============================================================================

ENABLE_ENCRYPTION = True  # sensitive data
ENABLE_ML_MODELS = True  # predictions
ENABLE_BACKUPS = True  # auto-backups
ENABLE_AUTHENTICATION = False  # Disable auth for now
ENABLE_ANALYTICS_CACHING = True  # Cache analytics results

# ============================================================================
#                       Database( for future refernece )
# ============================================================================

USE_DATABASE = False 
DATABASE_URL = None 

# ============================================================================
#                              Developer 
# ============================================================================

DEBUG_MODE = False
VERBOSE_LOGGING = False

# ============================================================================
#                                 Data
# ============================================================================

MONTHS_ABBREVIATION = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

