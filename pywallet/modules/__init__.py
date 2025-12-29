"""
Modules Package - Core business logic and analytics.

Submodules:
- data_manager.py: Data I/O and persistence
- analytics.py: Financial analysis and reporting
- validator.py: Input validation (planned)
- budget.py: Budget management (planned)
"""

from pywallet.modules.data_manager import DataManager
from pywallet.modules.analytics import Analytics

__all__ = [
    'DataManager',
    'Analytics',
]

