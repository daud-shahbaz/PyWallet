"""
AI Coach Module - Hooks for Phase 8 AI Coach integration.

Provides foundation for future LLM-based coaching and recommendations.
Currently uses rule-based logic; will be upgraded to LLM calls in Phase 8.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from pywallet.modules.analytics import Analytics
from pywallet.modules.data_manager import DataManager
from pywallet import config


class AICoach:
    """AI-powered personal finance coaching """
    
    @staticmethod
    def generate_monthly_summary(filepath: Optional[Path] = None) -> str:
        """
        Generate natural language monthly summary.
        Args:
            filepath: Path to data file
        Returns:
            Natural language summary
        """
        now = datetime.now()
        summary = Analytics.monthly_summary(filepath, now.year, now.month)
        
        if summary['transaction_count'] == 0:
            return "No expenses recorded this month yet."
        
        lines = [
            f"Monthly Summary - {summary['month_name']} {summary['year']}",
            f"Total Spending: PKR {summary['total']:.2f}",
            f"Transactions: {summary['transaction_count']}",
        ]
        
        if summary['by_category']:
            lines.append("\nSpending by Category:")
            for cat, amount in sorted(summary['by_category'].items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  - {cat}: PKR {amount:.2f}")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_personalized_advice(filepath: Optional[Path] = None) -> List[str]:
        """
        Generate personalized financial advice.
        
        PHASE 8 TODO: Upgrade to LLM-based generation with user profile.
        
        Args:
            filepath: Path to data file
        
        Returns:
            List of advice strings
        """
        advice = []
        
        try:
            # Check budget compliance
            budget_status = Analytics.budget_alert(filepath)
            
            if budget_status['critical_count'] > 0:
                advice.append(
                    f"You've exceeded budget in {budget_status['critical_count']} categories. "
                    "Consider reviewing your spending habits or adjusting your budgets."
                )
            
            if budget_status['warning_count'] > 0:
                advice.append(
                    f"You're approaching budget limits in {budget_status['warning_count']} categories. "
                    "Be mindful of expenses for the rest of the month."
                )
            
            # Check trends
            trends = Analytics.detect_trends(filepath, months=3)
            if 'trends' in trends:
                for cat, trend_data in list(trends['trends'].items())[:3]:
                    if trend_data['direction'] == 'increasing' and trend_data['percent_change'] > 25:
                        advice.append(
                            f"Your {cat} spending has increased by {trend_data['percent_change']:.0f}%. "
                            f"Consider finding ways to reduce costs in this area."
                        )
            
            # Check category concentr ation
            category_data = Analytics.category_summary(filepath)
            if category_data:
                spending_list = sorted(
                    [(cat, data['percentage']) for cat, data in category_data.items()],
                    key=lambda x: x[1],
                    reverse=True
                )
                
                if spending_list and spending_list[0][1] > 40:
                    advice.append(
                        f"Your spending is heavily concentrated in {spending_list[0][0]} "
                        f"({spending_list[0][1]:.0f}% of total). Consider diversifying."
                    )
            
            if not advice:
                advice.append("Your spending patterns look balanced! Keep up the good financial discipline.")
        
        except Exception as e:
            advice.append(f"Unable to generate advice at this time: {e}")
        
        return advice
    
    @staticmethod
    def analyze_spending_patterns(filepath: Optional[Path] = None) -> str:
        """
        Analyze and describe spending patterns in natural language.
        
        PHASE 8 TODO: Upgrade to LLM for more nuanced analysis.
        
        Args:
            filepath: Path to data file
        
        Returns:
            Natural language analysis
        """
        df = DataManager.load_dataframe(filepath)
        
        if df.empty:
            return "No spending data available for analysis."
        
        analysis_lines = ["Spending Pattern Analysis", "=" * 40]
        
        # Total spending
        total = df['amount'].sum()
        avg_transaction = df['amount'].mean()
        analysis_lines.append(f"Total Spending: PKR {total:.2f}")
        analysis_lines.append(f"Average Transaction: PKR {avg_transaction:.2f}")
        analysis_lines.append(f"Total Transactions: {len(df)}")
        
        # Category analysis
        by_category = df.groupby('category').agg({
            'amount': ['sum', 'count', 'mean']
        })
        
        if not by_category.empty:
            analysis_lines.append("\nTop Spending Categories:")
            sorted_cats = by_category['amount']['sum'].sort_values(ascending=False)
            
            for i, (cat, amount) in enumerate(sorted_cats.head(3).items(), 1):
                count = int(by_category.loc[cat, ('amount', 'count')])
                avg = float(by_category.loc[cat, ('amount', 'mean')])
                percentage = (amount / total * 100)
                analysis_lines.append(
                    f"  {i}. {cat}: PKR {amount:.2f} ({percentage:.1f}%) - {count} transactions"
                )
        
        # Recent activity
        last_7_days = df[df['date'] >= (datetime.now() - pd.Timedelta(days=7))]
        if not last_7_days.empty:
            analysis_lines.append(f"\nLast 7 Days: PKR {last_7_days['amount'].sum():.2f} spent")
        
        return "\n".join(analysis_lines)
    
    @staticmethod
    def suggest_next_actions(filepath: Optional[Path] = None) -> List[str]:
        """
        Suggest actionable next steps for user.
        
        PHASE 8 TODO: Upgrade to context-aware LLM suggestions.
        
        Args:
            filepath: Path to data file
        
        Returns:
            List of action suggestions
        """
        actions = []
        
        try:
            df = DataManager.load_dataframe(filepath)
            
            if df.empty:
                return ["Start tracking your expenses by adding your first transaction."]
            
            # Check for missing categories
            used_cats = set(df['category'].unique())
            unused_cats = [c for c in config.DEFAULT_CATEGORIES if c not in used_cats]
            
            if unused_cats and len(used_cats) < 5:
                actions.append(f"Expand tracking to more categories like {unused_cats[0]}")
            
            # Check for recent entries
            last_entry = df['date'].max()
            days_since = (datetime.now() - last_entry).days
            
            if days_since > 7:
                actions.append("You haven't added any expenses in over a week. Update your records!")
            
            # Check for notes
            entries_with_notes = len(df[df['note'].notna() & (df['note'] != '')])
            if entries_with_notes < len(df) / 2:
                actions.append("Add notes to your expenses to enable smarter category predictions")
            
            if not actions:
                actions.append("Review your budget allocation to optimize spending")
        
        except (ValueError, KeyError, AttributeError):
            pass
        
        if not actions:
            actions.append("Check your spending reports in the Analytics section")
        
        return actions


# ============================================================================
#                              Formatter
# ============================================================================

class InsightFormatter:
    """Format insights for display in web."""
    
    @staticmethod
    def format_prediction_insight(predictions: Dict[str, Any]) -> str:
        """Format spending predictions for display."""
        if 'error' in predictions:
            return f"Predictions unavailable: {predictions['error']}"
        
        if not predictions.get('predictions'):
            return "No predictions available yet. Need more data."
        
        lines = ["Next Month Spending Forecast:", "-" * 30]
        
        for category, pred in list(predictions['predictions'].items())[:5]:
            amount = pred['predicted_amount']
            confidence = pred['confidence']
            trend = pred['trend']
            
            lines.append(
                f"- {category}: PKR {amount:.0f} ({confidence:.0%} confidence, {trend})"
            )
        
        return "\n".join(lines)
    
    @staticmethod
    def format_anomaly_insight(anomalies: Dict[str, Any]) -> str:
        """Format anomaly detection for display."""
        if 'error' in anomalies:
            return f"Anomaly detection unavailable: {anomalies['error']}"
        
        anomaly_list = anomalies.get('anomalies', [])
        
        if not anomaly_list:
            return "No unusual transactions detected. Spending looks normal!"
        
        lines = [f"Unusual Transactions Found ({len(anomaly_list)}):", "-" * 30]
        
        for anom in anomaly_list[:5]:
            lines.append(
                f"- {anom['date']}: PKR {anom['amount']:.0f} on {anom['category']} "
                f"(z-score: {anom['z_score']:.2f})"
            )
        
        return "\n".join(lines)
    
    @staticmethod
    def format_cluster_insight(clustering: Dict[str, Any]) -> str:
        """Format clustering analysis for display."""
        if 'error' in clustering:
            return f"Clustering analysis unavailable: {clustering['error']}"
        
        lines = [f"Your Spending Profile: {clustering.get('cluster_name', 'Unknown')}", "-" * 40]
        
        comparison = SpendingClustering.compare_to_clusters()
        if 'top_3_categories' in comparison:
            lines.append("Top spending categories:")
            for cat in comparison['top_3_categories']:
                lines.append(f"  - {cat}")
        
        return "\n".join(lines)


# Import necessary for AI Coach
import pandas as pd
from pywallet.ml_models.models import SpendingClustering

