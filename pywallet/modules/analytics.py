"""
Analytics Module - All financial analysis and reporting.

Handles daily/monthly/category summaries, trend detection, budget alerts,
and export functionality. Wraps existing analysis.py patterns.
"""

from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pathlib import Path

from pywallet.modules.data_manager import DataManager
from pywallet import config


class Analytics:
    """Financial analysis and reporting engine."""
    
    @staticmethod
    def daily_summary(filepath: Optional[Path] = None, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate daily expense summary.
        
        Args:
            filepath: Path to data file
            date: Specific date (YYYY-MM-DD) or None for today
        
        Returns:
            Dict with total, by_category, transaction_count
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        df = DataManager.load_dataframe(filepath)
        
        if df.empty:
            return {
                'date': date,
                'total': 0,
                'by_category': {},
                'transaction_count': 0
            }
        
        # Filter to specific date
        day_data = df[df['date'].dt.strftime("%Y-%m-%d") == date]
        
        total = float(day_data['amount'].sum())
        by_category = day_data.groupby('category')['amount'].sum().to_dict()
        
        return {
            'date': date,
            'total': total,
            'by_category': by_category,
            'transaction_count': len(day_data)
        }
    
    @staticmethod
    def monthly_summary(filepath: Optional[Path] = None, year: Optional[int] = None, 
                       month: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculate monthly expense summary.
        
        Args:
            filepath: Path to data file
            year: Year (default: current)
            month: Month 1-12 (default: current)
        
        Returns:
            Dict with total, by_category, daily_breakdown, transaction_count
        """
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        
        df = DataManager.load_dataframe(filepath)
        
        if df.empty:
            return {
                'year': year,
                'month': month,
                'month_name': config.MONTHS_ABBREVIATION[month - 1],
                'total': 0,
                'by_category': {},
                'daily_breakdown': {},
                'transaction_count': 0
            }
        
        # Filter to specific month
        month_data = df[(df['date'].dt.year == year) & (df['date'].dt.month == month)]
        
        total = float(month_data['amount'].sum())
        by_category = month_data.groupby('category')['amount'].sum().to_dict()
        
        # Daily breakdown
        daily_breakdown = {}
        for day in range(1, 32):
            try:
                day_data = month_data[month_data['date'].dt.day == day]
                if len(day_data) > 0:
                    daily_breakdown[day] = float(day_data['amount'].sum())
            except:
                pass
        
        return {
            'year': year,
            'month': month,
            'month_name': config.MONTHS_ABBREVIATION[month - 1],
            'total': total,
            'by_category': by_category,
            'daily_breakdown': daily_breakdown,
            'transaction_count': len(month_data)
        }
    
    @staticmethod
    def category_summary(filepath: Optional[Path] = None, 
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Calculate spending by category for date range.
        
        Args:
            filepath: Path to data file
            start_date: Start date (YYYY-MM-DD) or None for all
            end_date: End date (YYYY-MM-DD) or None for all
        
        Returns:
            Dict with category stats: total, percentage, count
        """
        df = DataManager.load_dataframe(filepath)
        
        if df.empty:
            return {}
        
        # Filter by date range
        if start_date:
            df = df[df['date'] >= start_date]
        if end_date:
            df = df[df['date'] <= end_date]
        
        if df.empty:
            return {}
        
        # Calculate totals
        total_spending = df['amount'].sum()
        category_totals = df.groupby('category')['amount'].agg(['sum', 'count']).to_dict('index')
        
        result = {}
        for category, stats in category_totals.items():
            result[category] = {
                'total': float(stats['sum']),
                'count': int(stats['count']),
                'percentage': float((stats['sum'] / total_spending * 100) if total_spending > 0 else 0),
                'average': float(stats['sum'] / stats['count'])
            }
        
        return result
    
    @staticmethod
    def detect_trends(filepath: Optional[Path] = None, months: int = 3) -> Dict[str, Any]:
        """
        Detect spending trends over recent months.
        
        Args:
            filepath: Path to data file
            months: Number of months to analyze
        
        Returns:
            Dict with trend analysis by category
        """
        df = DataManager.load_dataframe(filepath)
        
        if df.empty or len(df) < 2:
            return {'status': 'Insufficient data for trend analysis'}
        
        # Get last N months of data
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        recent_data = df[df['date'] >= cutoff_date]
        
        if recent_data.empty:
            return {'status': 'No data in specified period'}
        
        # Calculate trend by category
        trends = {}
        for category in config.DEFAULT_CATEGORIES:
            cat_data = recent_data[recent_data['category'] == category]
            
            if len(cat_data) < 2:
                continue
            
            # Sort by date and get monthly totals
            monthly_totals = cat_data.set_index('date').resample('MS')['amount'].sum()
            
            if len(monthly_totals) >= 2:
                values = monthly_totals.values
                # Calculate trend: positive = increasing, negative = decreasing
                trend_direction = 'increasing' if values[-1] > values[0] else 'decreasing'
                trend_percent = ((values[-1] - values[0]) / values[0] * 100) if values[0] > 0 else 0
                
                trends[category] = {
                    'direction': trend_direction,
                    'percent_change': float(trend_percent),
                    'current_average': float(monthly_totals.iloc[-1]),
                    'previous_average': float(monthly_totals.iloc[0])
                }
        
        return {'trends': trends, 'analysis_period_months': months}
    
    @staticmethod
    def budget_alert(filepath: Optional[Path] = None, 
                    custom_budgets: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Check current spending against budgets.
        
        Args:
            filepath: Path to data file
            custom_budgets: Custom budget dict (default: config.DEFAULT_BUDGETS)
        
        Returns:
            Dict with budget status, warnings, and overspending
        """
        if custom_budgets is None:
            custom_budgets = config.DEFAULT_BUDGETS
        
        df = DataManager.load_dataframe(filepath)
        
        if df.empty:
            return {
                'status': 'No data',
                'alerts': [],
                'on_track_count': len(custom_budgets),
                'warning_count': 0,
                'critical_count': 0,
                'total_categories': len(custom_budgets)
            }
        
        # Current month
        now = datetime.now()
        current_month = df[(df['date'].dt.year == now.year) & (df['date'].dt.month == now.month)]
        
        alerts = []
        on_track = 0
        warning = 0
        critical = 0
        
        for category, budget in custom_budgets.items():
            spending = float(current_month[current_month['category'] == category]['amount'].sum())
            percentage = (spending / budget * 100) if budget > 0 else 0
            
            if percentage >= 100:
                alerts.append({
                    'category': category,
                    'status': 'critical',
                    'budget': budget,
                    'spending': spending,
                    'percentage': percentage,
                    'message': f"{category} budget exceeded by {spending - budget:.2f}"
                })
                critical += 1
            elif percentage >= 80:
                alerts.append({
                    'category': category,
                    'status': 'warning',
                    'budget': budget,
                    'spending': spending,
                    'percentage': percentage,
                    'message': f"{category} at {percentage:.1f}% of budget"
                })
                warning += 1
            else:
                on_track += 1
        
        return {
            'month': config.MONTHS_ABBREVIATION[now.month - 1],
            'year': now.year,
            'alerts': alerts,
            'on_track_count': on_track,
            'warning_count': warning,
            'critical_count': critical,
            'total_categories': len(custom_budgets)
        }
    
    @staticmethod
    def export_to_csv(filepath: Optional[Path] = None, output_path: Optional[Path] = None) -> Tuple[bool, str]:
        """
        Export data to CSV.
        
        Args:
            filepath: Source JSON file
            output_path: Destination CSV file
        
        Returns:
            Tuple of (success, message)
        """
        return DataManager.export_to_csv(filepath, output_path)
    
    @staticmethod
    def import_from_csv(csv_path: Path, filepath: Optional[Path] = None) -> Tuple[bool, str, int]:
        """
        Import data from CSV.
        
        Args:
            csv_path: CSV file to import
            filepath: Destination JSON file
        
        Returns:
            Tuple of (success, message, imported_count)
        """
        return DataManager.import_from_csv(csv_path, filepath)
    
    @staticmethod
    def get_date_range_summary(filepath: Optional[Path] = None,
                              start_date: str = None,
                              end_date: str = None) -> Dict[str, Any]:
        """
        Get comprehensive summary for date range.
        
        Args:
            filepath: Path to data file
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            Dict with total, average daily, category breakdown
        """
        df = DataManager.filter_expenses(filepath, start_date=start_date, end_date=end_date)
        
        if df.empty:
            return {
                'period': f"{start_date} to {end_date}",
                'total': 0,
                'average_daily': 0,
                'average_transaction': 0,
                'by_category': {},
                'transaction_count': 0,
                'day_count': 0
            }
        
        # Calculate statistics
        total = float(df['amount'].sum())
        transaction_count = len(df)
        
        # Count distinct days
        if not df.empty:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            day_count = (end - start).days + 1
        else:
            day_count = 1
        
        average_daily = total / day_count if day_count > 0 else 0
        average_transaction = total / transaction_count if transaction_count > 0 else 0
        
        by_category = df.groupby('category')['amount'].sum().to_dict()
        
        return {
            'period': f"{start_date} to {end_date}",
            'total': total,
            'average_daily': float(average_daily),
            'average_transaction': float(average_transaction),
            'by_category': by_category,
            'transaction_count': transaction_count,
            'day_count': day_count
        }


# ============================================================================
# BACKWARD COMPATIBILITY FUNCTIONS
# ============================================================================

def daily_summary(filepath: Optional[Path] = None, date: Optional[str] = None) -> Dict[str, Any]:
    """Backward compatible wrapper"""
    return Analytics.daily_summary(filepath, date)


def monthly_summary(filepath: Optional[Path] = None, year: Optional[int] = None,
                   month: Optional[int] = None) -> Dict[str, Any]:
    """Backward compatible wrapper"""
    return Analytics.monthly_summary(filepath, year, month)


def category_summary(filepath: Optional[Path] = None, start_date: Optional[str] = None,
                    end_date: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """Backward compatible wrapper"""
    return Analytics.category_summary(filepath, start_date, end_date)


def detect_trends(filepath: Optional[Path] = None, months: int = 3) -> Dict[str, Any]:
    """Backward compatible wrapper"""
    return Analytics.detect_trends(filepath, months)


def budget_alert(filepath: Optional[Path] = None,
                custom_budgets: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """Backward compatible wrapper"""
    return Analytics.budget_alert(filepath, custom_budgets)

