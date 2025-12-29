"""
ML Models Package - Machine Learning and AI capabilities.

Submodules:
- models.py: Core ML algorithms (prediction, anomaly detection, classification, clustering)
- ai_coach.py: AI Coach foundation for Phase 8
"""

from pywallet.ml_models.models import (
    SpendingPredictor,
    AnomalyDetector,
    CategoryClassifier,
    SpendingClustering,
    InsightGenerator,
    generate_all_insights,
)

from pywallet.ml_models.ai_coach import AICoach, InsightFormatter

__all__ = [
    'SpendingPredictor',
    'AnomalyDetector',
    'CategoryClassifier',
    'SpendingClustering',
    'InsightGenerator',
    'AICoach',
    'InsightFormatter',
    'generate_all_insights',
]

