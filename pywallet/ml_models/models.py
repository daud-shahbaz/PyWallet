"""
Machine Learning Models Module - Predictive analytics and insights.

Implements:
- Spending prediction using linear regression
- Anomaly detection for unusual transactions
- Category classification from notes (NLP)
- Clustering for spending behavior analysis
- Insight generation for user-facing summaries
"""

import json
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pathlib import Path
import pickle
import warnings

warnings.filterwarnings('ignore')

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import IsolationForest
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from pywallet.modules.data_manager import DataManager
from pywallet import config


# ============================================================================
#                          Regression - Spending Pattern
# ============================================================================

class SpendingPredictor:
    """Predict future spending by category using linear regression."""
    
    @staticmethod
    def predict_next_month(filepath: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
        """
        Predict next month's spending by category.
        
        Args:
            filepath: Path to data file
        
        Returns:
            Dict with predictions for each category
        """
        if not SKLEARN_AVAILABLE:
            return {'error': 'scikit-learn not installed', 'predictions': {}}
        
        df = DataManager.load_dataframe(filepath)
        
        if df.empty or len(df) < config.MIN_DATA_POINTS_FOR_ML:
            return {
                'status': 'Insufficient data',
                'required_data_points': config.MIN_DATA_POINTS_FOR_ML,
                'available_data_points': len(df),
                'predictions': {}
            }
        
        # Get last N months
        cutoff = datetime.now() - timedelta(days=config.PREDICTION_WINDOW_MONTHS * 30)
        historical = df[df['date'] >= cutoff]
        
        predictions = {}
        
        for category in config.DEFAULT_CATEGORIES:
            cat_data = historical[historical['category'] == category]
            
            if len(cat_data) < 3:  # Need at least 3 months
                continue
            
            # Get monthly totals
            monthly = cat_data.set_index('date').resample('MS')['amount'].sum()
            
            if len(monthly) < 2:
                continue
            
            try:
                # Prepare training data
                X = np.arange(len(monthly)).reshape(-1, 1)
                y = monthly.values
                
                # Train model
                model = LinearRegression()
                model.fit(X, y)
                
                # Predict next month
                next_month_idx = len(monthly)
                predicted_amount = int(model.predict([[next_month_idx]])[0])
                
                # Calculate confidence (R-squared)
                r_squared = float(model.score(X, y))
                
                # Trend
                trend_slope = float(model.coef_[0])
                trend_direction = 'increasing' if trend_slope > 0 else 'decreasing' if trend_slope < 0 else 'stable'
                
                predictions[category] = {
                    'predicted_amount': max(0, predicted_amount),  # Don't predict negative
                    'confidence': r_squared,
                    'trend': trend_direction,
                    'historical_average': float(monthly.mean()),
                    'historical_min': float(monthly.min()),
                    'historical_max': float(monthly.max()),
                    'data_points': len(monthly)
                }
            except Exception as e:
                continue
        
        return {
            'period': 'next_month',
            'forecast_months': config.FORECAST_AHEAD_MONTHS,
            'predictions': predictions,
            'generated_at': datetime.now().isoformat()
        }
    
    @staticmethod
    def predict_spending_trajectory(filepath: Optional[Path] = None, 
                                   category: str = None) -> Dict[str, Any]:
        """
        Predict spending trajectory for specific category.
        
        Args:
            filepath: Path to data file
            category: Category to forecast
        
        Returns:
            Trajectory with forecasted amounts
        """
        if not SKLEARN_AVAILABLE or not category:
            return {'error': 'Invalid parameters'}
        
        df = DataManager.load_dataframe(filepath)
        cat_data = df[df['category'] == category]
        
        if len(cat_data) < 3:
            return {'error': 'Insufficient data for this category'}
        
        try:
            # Get monthly totals
            monthly = cat_data.set_index('date').resample('MS')['amount'].sum()
            
            X = np.arange(len(monthly)).reshape(-1, 1)
            y = monthly.values
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Generate trajectory
            trajectory = []
            for i in range(config.FORECAST_AHEAD_MONTHS):
                pred_idx = len(monthly) + i
                pred_value = float(model.predict([[pred_idx]])[0])
                trajectory.append({
                    'month_ahead': i + 1,
                    'predicted_amount': max(0, pred_value),
                    'uncertainty': float(abs(model.coef_[0]))
                })
            
            return {
                'category': category,
                'trajectory': trajectory,
                'baseline': float(monthly.mean())
            }
        except (ValueError, IndexError, KeyError):
            return {'error': 'Prediction failed'}


# ============================================================================
#                        Anomaly Detection
# ============================================================================

class AnomalyDetector:
    """Detect unusual transactions using statistical methods."""
    
    @staticmethod
    def detect_anomalies(filepath: Optional[Path] = None) -> Dict[str, Any]:
        """
        Detect unusual spending patterns.
        
        Args:
            filepath: Path to data file
        
        Returns:
            Dict with anomalies and details
        """
        df = DataManager.load_dataframe(filepath)
        
        if df.empty or len(df) < config.MIN_DATA_POINTS_FOR_ML:
            return {'anomalies': [], 'status': 'Insufficient data'}
        
        anomalies = []
        
        # Check each category for outliers
        for category in config.DEFAULT_CATEGORIES:
            cat_data = df[df['category'] == category]
            
            if len(cat_data) < 5:
                continue
            
            amounts = cat_data['amount'].values
            mean = np.mean(amounts)
            std = np.std(amounts)
            
            # Find values beyond threshold
            threshold = mean + (config.ANOMALY_THRESHOLD_SIGMA * std)
            
            outliers = cat_data[cat_data['amount'] > threshold]
            
            for _, expense in outliers.iterrows():
                z_score = (expense['amount'] - mean) / std if std > 0 else 0
                anomalies.append({
                    'id': expense['id'],
                    'category': category,
                    'amount': int(expense['amount']),
                    'date': str(expense['date'].date()),
                    'note': expense['note'],
                    'z_score': float(z_score),
                    'deviation': int(expense['amount'] - mean),
                    'reason': f"Unusually high for {category}: {z_score:.2f} std devs above mean"
                })
        
        # Sort by z-score high to low
        anomalies.sort(key=lambda x: x['z_score'], reverse=True)
        
        return {
            'anomalies': anomalies[:10],
            'total_anomalies_found': len(anomalies),
            'anomaly_threshold_sigma': config.ANOMALY_THRESHOLD_SIGMA,
            'method': 'statistical_zscore'
        }
    
    @staticmethod
    def flag_recent_anomalies(filepath: Optional[Path] = None, days: int = 30) -> List[Dict[str, Any]]:
        """
        Find anomalies in recent transactions.
        
        Args:
            filepath: Path to data file
            days: Look back period
        
        Returns:
            List of recent anomalies
        """
        df = DataManager.load_dataframe(filepath)
        
        cutoff = datetime.now() - timedelta(days=days)
        recent = df[df['date'] >= cutoff]
        
        if recent.empty:
            return []
        
        anomalies = []
        
        for category in recent['category'].unique():
            cat_data = df[df['category'] == category]  # Full history for stats
            
            if len(cat_data) < 5:
                continue
            
            mean = cat_data['amount'].mean()
            std = cat_data['amount'].std()
            threshold = mean + (2 * std)
            
            recent_cat = recent[(recent['category'] == category) & (recent['amount'] > threshold)]
            
            for _, exp in recent_cat.iterrows():
                anomalies.append({
                    'id': exp['id'],
                    'date': str(exp['date'].date()),
                    'category': category,
                    'amount': int(exp['amount']),
                    'mean': int(mean),
                    'note': exp['note']
                })
        
        return anomalies


# ============================================================================
#                             category nlp
# ============================================================================

class CategoryClassifier:
    """Predict expense category from notes using NLP."""
    
    @staticmethod
    def train_classifier(filepath: Optional[Path] = None) -> Tuple[bool, str]:
        """
        Train category classifier on historical notes.
        
        Args:
            filepath: Path to data file
        
        Returns:
            Tuple of (success, message)
        """
        if not SKLEARN_AVAILABLE:
            return False, 'scikit-learn not installed'
        
        try:
            df = DataManager.load_dataframe(filepath)
            
            # Filter entries with non-empty notes
            df = df[df['note'].notna() & (df['note'] != '')]
            
            if len(df) < config.MIN_NOTES_FOR_TRAINING:
                return False, f"Need at least {config.MIN_NOTES_FOR_TRAINING} entries with notes"
            
            # Prepare training data
            X = df['note'].values
            y = df['category'].values
            
            # Vectorize text
            vectorizer = TfidfVectorizer(max_features=100, lowercase=True, stop_words='english')
            X_vec = vectorizer.fit_transform(X)
            
            # Train classifier
            classifier = MultinomialNB()
            classifier.fit(X_vec, y)
            
            # Save model
            model_dir = config.DATA_DIR / 'ml_models'
            model_dir.mkdir(parents=True, exist_ok=True)
            
            with open(model_dir / 'classifier_model.pkl', 'wb') as f:
                pickle.dump(classifier, f)
            
            with open(model_dir / 'classifier_vectorizer.pkl', 'wb') as f:
                pickle.dump(vectorizer, f)
            
            return True, f"Classifier trained on {len(df)} entries"
        except Exception as e:
            return False, f"Training failed: {e}"
    
    @staticmethod
    def predict_category(note: str) -> Dict[str, Any]:
        """
        Predict category for a note.
        
        Args:
            note: Expense note/description
        
        Returns:
            Dict with predicted category and confidence
        """
        if not SKLEARN_AVAILABLE:
            return {'error': 'scikit-learn not installed', 'default_category': 'Other'}
        
        try:
            model_dir = config.DATA_DIR / 'ml_models'
            
            # Load model and vectorizer
            with open(model_dir / 'classifier_model.pkl', 'rb') as f:
                classifier = pickle.load(f)
            
            with open(model_dir / 'classifier_vectorizer.pkl', 'rb') as f:
                vectorizer = pickle.load(f)
            
            # Vectorize input
            X = vectorizer.transform([note])
            
            # Predict
            category = classifier.predict(X)[0]
            confidence = float(np.max(classifier.predict_proba(X)))
            
            return {
                'predicted_category': category,
                'confidence': confidence,
                'note': note,
                'recommended': confidence > 0.5  # High confidence threshold
            }
        except (ValueError, AttributeError, TypeError):
            return {
                'error': 'Model not trained yet',
                'default_category': 'Other',
                'note': note
            }
    
    @staticmethod
    def get_category_keywords(category: str, filepath: Optional[Path] = None) -> List[str]:
        """
        Get common keywords for a category.
        
        Args:
            category: Category name
            filepath: Path to data file
        
        Returns:
            List of keywords
        """
        df = DataManager.load_dataframe(filepath)
        
        cat_data = df[(df['category'] == category) & (df['note'].notna())]
        
        if cat_data.empty:
            return []
        
        # Simple keyword extraction (first words from notes)
        all_notes = ' '.join(cat_data['note'].values)
        words = all_notes.lower().split()
        
        # Count word frequency
        from collections import Counter
        word_counts = Counter(words)
        
        # Get top keywords (filter short words)
        keywords = [word for word, count in word_counts.most_common(10) if len(word) > 3]
        
        return keywords


# ============================================================================
#                         Clustering
# ============================================================================

class SpendingClustering:
    """Analyze spending behavior patterns using clustering."""
    
    @staticmethod
    def cluster_spending_patterns(filepath: Optional[Path] = None) -> Dict[str, Any]:
        """
        Cluster users into spending behavior groups.
        
        Args:
            filepath: Path to data file
        
        Returns:
            Dict with cluster assignments and characteristics
        """
        if not SKLEARN_AVAILABLE:
            return {'error': 'scikit-learn not installed', 'clusters': {}}
        
        df = DataManager.load_dataframe(filepath)
        
        if df.empty or len(df) < config.MIN_DATA_POINTS_FOR_ML:
            return {'error': 'Insufficient data', 'clusters': {}}
        
        try:
            # Create feature matrix: spending by category
            category_spending = df.groupby('category')['amount'].sum().reindex(
                config.DEFAULT_CATEGORIES, fill_value=0
            ).values.reshape(1, -1)
            
            if category_spending.sum() == 0:
                return {'error': 'No spending data', 'clusters': {}}
            
            # Normalize
            category_spending = category_spending / category_spending.sum()
            
            # Clustering
            kmeans = KMeans(n_clusters=config.KMEANS_CLUSTERS, random_state=42)
            cluster_label = kmeans.fit_predict(category_spending)[0]
            
            # Analyze cluster
            clusters = {}
            for i, center in enumerate(kmeans.cluster_centers_):
                top_categories = sorted(
                    zip(config.DEFAULT_CATEGORIES, center),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
                
                clusters[f'cluster_{i}'] = {
                    'name': f"Spending Pattern {i + 1}",
                    'top_categories': [cat for cat, _ in top_categories],
                    'characteristics': 'High spending in ' + ', '.join([cat for cat, _ in top_categories])
                }
            
            return {
                'assigned_cluster': f'cluster_{cluster_label}',
                'cluster_name': f"Spending Pattern {cluster_label + 1}",
                'clusters': clusters,
                'num_clusters': config.KMEANS_CLUSTERS,
                'method': 'kmeans'
            }
        except Exception as e:
            return {'error': str(e), 'clusters': {}}
    
    @staticmethod
    def compare_to_clusters(filepath: Optional[Path] = None) -> Dict[str, Any]:
        """
        Compare current spending to typical cluster profiles.
        
        Args:
            filepath: Path to data file
        
        Returns:
            Comparison metrics
        """
        df = DataManager.load_dataframe(filepath)
        
        if df.empty:
            return {'error': 'No data', 'comparison': {}}
        
        # Get category distribution
        category_dist = df.groupby('category')['amount'].sum()
        total = category_dist.sum()
        
        if total == 0:
            return {'error': 'No spending', 'comparison': {}}
        
        percentages = (category_dist / total * 100).to_dict()
        
        # Identify dominant categories
        sorted_cats = sorted(percentages.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_spending': float(total),
            'category_distribution': {k: float(v) for k, v in percentages.items()},
            'dominant_category': sorted_cats[0][0] if sorted_cats else 'Unknown',
            'top_3_categories': [cat for cat, _ in sorted_cats[:3]],
            'spending_diversity': len([c for c, pct in sorted_cats if pct > 5])
        }


# ============================================================================
#                         ml insight generation
# ============================================================================

class InsightGenerator:
    """Generate insights from ML models."""
    
    @staticmethod
    def generate_ml_insights(filepath: Optional[Path] = None) -> Dict[str, Any]:
        """
        Generate comprehensive ML-based insights.
        Args:
            filepath: Path to data file
        Returns:
            Dict with various insights
        """
        insights = {
            'generated_at': datetime.now().isoformat(),
            'predictions': {},
            'anomalies': {},
            'clustering': {},
            'recommendations': []
        }
        
        try:
            # Get predictions
            predictor = SpendingPredictor()
            insights['predictions'] = predictor.predict_next_month(filepath)
        except (ValueError, KeyError, TypeError):
            pass
        
        try:
            # Get anomalies
            detector = AnomalyDetector()
            insights['anomalies'] = detector.detect_anomalies(filepath)
        except (ValueError, KeyError, TypeError):
            pass
        
        try:
            # Get clustering
            clusterer = SpendingClustering()
            insights['clustering'] = clusterer.cluster_spending_patterns(filepath)
        except (ValueError, KeyError, TypeError):
            pass
        
        # Generate recommendations
        try:
            insights['recommendations'] = InsightGenerator._generate_recommendations(filepath)
        except (ValueError, KeyError, TypeError):
            pass
        
        return insights
    
    @staticmethod
    def _generate_recommendations(filepath: Optional[Path] = None) -> List[str]:
        """Generate actionable recommendations."""
        from pywallet.modules.analytics import Analytics
        
        recommendations = []
        
        try:
            # Check budget status
            budget_status = Analytics.budget_alert(filepath)
            
            if budget_status['critical_count'] > 0:
                recommendations.append(f"Warning: {budget_status['critical_count']} categories over budget!")
            
            if budget_status['warning_count'] > 0:
                recommendations.append(f"Caution: {budget_status['warning_count']} categories near budget limits")
            
            # Check trends
            trends = Analytics.detect_trends(filepath)
            if 'trends' in trends:
                for cat, trend in list(trends['trends'].items())[:2]:
                    if trend['direction'] == 'increasing' and trend['percent_change'] > 20:
                        recommendations.append(f"Spending on {cat} increased {trend['percent_change']:.0f}% - consider reducing")
            
            if len(recommendations) == 0:
                recommendations.append("Your spending looks healthy! Keep it up.")
        
        except:
            recommendations.append("Unable to generate recommendations at this time")
        
        return recommendations


# ============================================================================
#                               API
# ============================================================================

def generate_all_insights(filepath: Optional[Path] = None) -> Dict[str, Any]:
    """Generate all ML insights (main entry point)."""
    return InsightGenerator.generate_ml_insights(filepath)

