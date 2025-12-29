"""
PyWallet - Personal Money Manager
A comprehensive financial tracking and analytics application with:
- Expense tracking and management
- Budget monitoring and alerts
- Financial analysis and trends
- Machine learning predictions
- Secure data storage
- Web-based UI

Main Modules:
- config: Central configuration
- modules: Core logic
- ml_models: maths
- security: Authentication and encryption
- utils: helpers
"""

from pywallet import config

__author__ = "Daud Shahbaz"

# Expose main classes
from pywallet.modules import DataManager, Analytics
from pywallet.ml_models import (
    SpendingPredictor,
    AnomalyDetector,
    CategoryClassifier,
    SpendingClustering,
    generate_all_insights,
)

__all__ = [
    'config',
    'DataManager',
    'Analytics',
    'SpendingPredictor',
    'AnomalyDetector',
    'CategoryClassifier',
    'SpendingClustering',
    'generate_all_insights',
]

