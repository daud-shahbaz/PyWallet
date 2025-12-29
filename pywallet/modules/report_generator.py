"""
Report Generator Module for PyWallet

Generates comprehensive financial reports with monthly/yearly summaries,
budget performance, income tracking, and spending analysis.
Also supports PDF and CSV export.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import pandas as pd
from pathlib import Path
import json

from pywallet.modules.data_manager import DataManager
from pywallet.modules.analytics import Analytics
from pywallet import config


class ReportGenerator:
    """Generate comprehensive financial reports."""

    @staticmethod
    def generate_monthly_report(year: int, month: int) -> Dict:
        """
        Generate comprehensive report for a specific month.
        
        Args:
            year: Report year (e.g., 2024)
            month: Report month (1-12)
            
        Returns:
            Dictionary containing all report sections
        """
        try:
            report = {
                'period': f"{datetime(year, month, 1).strftime('%B %Y')}",
                'year': year,
                'month': month,
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'sections': {}
            }
            
            # Get analytics data
            monthly = Analytics.monthly_summary(year=year, month=month)
            
            # 1. Spending Summary
            report['sections']['spending_summary'] = {
                'total_spending': monthly['total'],
                'transaction_count': monthly['transaction_count'],
                'by_category': monthly['by_category'],
                'daily_breakdown': monthly['daily_breakdown']
            }
            
            # 2. Budget Performance
            budget_perf = ReportGenerator._get_budget_performance(year, month, monthly)
            report['sections']['budget_performance'] = budget_perf
            
            # 3. Income & Savings
            income_section = ReportGenerator._get_income_section(year, month)
            report['sections']['income_savings'] = income_section
            
            # 4. Top Expenses
            report['sections']['top_expenses'] = ReportGenerator._get_top_expenses(monthly, limit=5)
            
            # 5. Spending Insights
            insights = ReportGenerator._get_spending_insights(monthly)
            report['sections']['insights'] = insights
            
            # 6. Month-over-Month Comparison
            mom_comparison = ReportGenerator._get_month_over_month(year, month)
            report['sections']['month_comparison'] = mom_comparison
            
            return report
            
        except Exception as e:
            return {'error': f'Failed to generate report: {str(e)}'}

    @staticmethod
    def generate_yearly_report(year: int) -> Dict:
        """
        Generate comprehensive report for an entire year.
        
        Args:
            year: Report year (e.g., 2024)
            
        Returns:
            Dictionary containing yearly report sections
        """
        try:
            report = {
                'period': str(year),
                'year': year,
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'sections': {}
            }
            
            # Monthly summaries
            monthly_data = []
            yearly_total = 0
            yearly_count = 0
            yearly_by_category = {}
            
            for month in range(1, 13):
                monthly = Analytics.monthly_summary(year=year, month=month)
                month_name = datetime(year, month, 1).strftime('%B')
                
                monthly_data.append({
                    'month': month_name,
                    'month_num': month,
                    'total': monthly['total'],
                    'transactions': monthly['transaction_count'],
                    'categories': len(monthly['by_category'])
                })
                
                yearly_total += monthly['total']
                yearly_count += monthly['transaction_count']
                
                # Aggregate categories
                for cat, amount in monthly['by_category'].items():
                    yearly_by_category[cat] = yearly_by_category.get(cat, 0) + amount
            
            # 1. Yearly Overview
            report['sections']['yearly_overview'] = {
                'total_spending': yearly_total,
                'total_transactions': yearly_count,
                'average_monthly': yearly_total / 12,
                'categories_tracked': len(yearly_by_category),
                'top_category': max(yearly_by_category, key=yearly_by_category.get) if yearly_by_category else 'N/A',
                'top_category_amount': max(yearly_by_category.values()) if yearly_by_category else 0
            }
            
            # 2. Monthly Breakdown
            report['sections']['monthly_breakdown'] = monthly_data
            
            # 3. Category Summary
            sorted_categories = sorted(yearly_by_category.items(), key=lambda x: x[1], reverse=True)
            report['sections']['category_summary'] = {
                'total_by_category': dict(sorted_categories),
                'category_percentage': {
                    cat: round((amount / yearly_total * 100), 1) 
                    for cat, amount in sorted_categories
                }
            }
            
            # 4. Trends
            trends = ReportGenerator._analyze_yearly_trends(monthly_data, yearly_total)
            report['sections']['trends'] = trends
            
            return report
            
        except Exception as e:
            return {'error': f'Failed to generate yearly report: {str(e)}'}

    @staticmethod
    def _get_budget_performance(year: int, month: int, monthly: Dict) -> Dict:
        """Get budget performance for the month."""
        try:
            budget_file = Path(config.DATA_DIR) / config.BUDGET_FILE
            
            if not budget_file.exists():
                return {'status': 'no_budgets_set', 'message': 'No budgets configured'}
            
            import json
            with open(budget_file) as f:
                budgets = json.load(f)
            
            performance = {'total_budget': 0, 'total_spent': 0, 'categories': {}}
            
            for category, by_cat in monthly['by_category'].items():
                budget_amount = budgets.get(category, 0)
                spent = by_cat
                
                performance['total_budget'] += budget_amount
                performance['total_spent'] += spent
                
                if budget_amount > 0:
                    utilization = (spent / budget_amount) * 100
                    status = 'over_budget' if utilization > 100 else 'on_track'
                else:
                    utilization = 0
                    status = 'no_budget'
                
                performance['categories'][category] = {
                    'budget': budget_amount,
                    'spent': spent,
                    'utilization_percent': round(utilization, 1),
                    'status': status,
                    'remaining': budget_amount - spent
                }
            
            return performance
            
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def _get_income_section(year: int, month: int) -> Dict:
        """Get income and savings data for the month."""
        try:
            income_file = Path(config.DATA_DIR) / 'income.json'
            savings_file = Path(config.DATA_DIR) / 'savings_goals.json'
            
            income_data = {'total_income': 0, 'sources': []}
            savings_data = {'total_goals': 0, 'goals': []}
            
            # Load income data
            if income_file.exists():
                import json
                with open(income_file) as f:
                    incomes = json.load(f)
                    for inc in incomes:
                        income_data['sources'].append({
                            'source': inc.get('source', 'Unknown'),
                            'amount': inc.get('amount', 0),
                            'date': inc.get('date', 'N/A')
                        })
                        income_data['total_income'] += inc.get('amount', 0)
            
            # Load savings goals
            if savings_file.exists():
                with open(savings_file) as f:
                    goals = json.load(f)
                    for goal in goals:
                        savings_data['goals'].append({
                            'goal_name': goal.get('name', 'Unknown'),
                            'target': goal.get('target', 0),
                            'current': goal.get('current', 0),
                            'progress_percent': round((goal.get('current', 0) / max(goal.get('target', 1), 1)) * 100, 1)
                        })
                        savings_data['total_goals'] += goal.get('target', 0)
            
            return {'income': income_data, 'savings_goals': savings_data}
            
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def _get_top_expenses(monthly: Dict, limit: int = 5) -> List[Dict]:
        """Get top expenses by category."""
        try:
            categories = monthly['by_category']
            sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
            
            return [
                {'category': cat, 'amount': amount, 'rank': i+1}
                for i, (cat, amount) in enumerate(sorted_cats[:limit])
            ]
        except Exception as e:
            return [{'error': str(e)}]

    @staticmethod
    def _get_spending_insights(monthly: Dict) -> Dict:
        """Generate spending insights and analysis."""
        try:
            total = monthly['total']
            categories = monthly['by_category']
            daily = monthly['daily_breakdown']
            
            insights = {
                'average_daily_spending': round(total / 30, 2),
                'highest_spending_day': 0,
                'lowest_spending_day': 0,
                'most_expensive_category': '',
                'category_concentration': {}
            }
            
            # Daily analysis
            if daily:
                daily_amounts = [d.get('total', 0) for d in daily]
                insights['highest_spending_day'] = max(daily_amounts) if daily_amounts else 0
                insights['lowest_spending_day'] = min([d for d in daily_amounts if d > 0]) if daily_amounts else 0
            
            # Category concentration
            if categories:
                most_exp_cat = max(categories, key=categories.get)
                insights['most_expensive_category'] = most_exp_cat
                
                for cat, amount in categories.items():
                    insights['category_concentration'][cat] = round((amount / total * 100), 1)
            
            return insights
            
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def _get_month_over_month(year: int, month: int) -> Dict:
        """Get month-over-month comparison."""
        try:
            current = Analytics.monthly_summary(year=year, month=month)
            
            # Get previous month
            prev_month = month - 1
            prev_year = year
            if prev_month < 1:
                prev_month = 12
                prev_year -= 1
            
            previous = Analytics.monthly_summary(year=prev_year, month=prev_month)
            
            current_total = current['total']
            previous_total = previous['total']
            
            change = current_total - previous_total
            change_percent = (change / previous_total * 100) if previous_total > 0 else 0
            
            return {
                'current_month_total': current_total,
                'previous_month_total': previous_total,
                'change_amount': change,
                'change_percent': round(change_percent, 1),
                'trend': 'increased' if change > 0 else 'decreased'
            }
            
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def _analyze_yearly_trends(monthly_data: List[Dict], yearly_total: float) -> Dict:
        """Analyze trends across the year."""
        try:
            if not monthly_data:
                return {}
            
            totals = [m['total'] for m in monthly_data]
            
            trends = {
                'highest_spending_month': max(monthly_data, key=lambda x: x['total'])['month'],
                'lowest_spending_month': min(monthly_data, key=lambda x: x['total'])['month'],
                'highest_amount': max(totals),
                'lowest_amount': min(totals),
                'average_monthly': yearly_total / 12,
                'trend_direction': 'increasing' if totals[-1] > totals[0] else 'decreasing'
            }
            
            return trends
            
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def export_report_to_pdf(report: Dict, filename: str = None) -> str:
        """
        Export report to PDF format.
        
        Args:
            report: Report dictionary
            filename: Output filename (optional)
            
        Returns:
            Path to generated PDF file or error message
        """
        try:
            try:
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.lib import colors
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
                from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
            except ImportError:
                return "Error: reportlab not installed. Install with: pip install reportlab"
            
            if filename is None:
                period = report.get('period', 'report').replace(' ', '_').replace('/', '-')
                filename = f"PyWallet_Report_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            filepath = Path(config.DATA_DIR) / filename
            
            # Create PDF
            doc = SimpleDocTemplate(str(filepath), pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1f77b4'),
                spaceAfter=12,
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=10,
                spaceBefore=10
            )
            
            # Title
            story.append(Paragraph("PyWallet Financial Report", title_style))
            story.append(Paragraph(f"Period: {report.get('period', 'N/A')}", styles['Normal']))
            story.append(Paragraph(f"Generated: {report.get('generated_at', 'N/A')}", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # Add sections
            for section_name, section_data in report.get('sections', {}).items():
                story.append(Paragraph(section_name.replace('_', ' ').title(), heading_style))
                
                if isinstance(section_data, dict):
                    # Convert dict to table
                    table_data = [['Item', 'Value']]
                    
                    for key, value in section_data.items():
                        if not isinstance(value, (dict, list)):
                            # Format key
                            formatted_key = key.replace('_', ' ').title()
                            
                            # Format value
                            if isinstance(value, float):
                                formatted_value = f"{value:,.2f}"
                            else:
                                formatted_value = str(value)
                            
                            table_data.append([formatted_key, formatted_value])
                    
                    if len(table_data) > 1:
                        table = Table(table_data, colWidths=[3*inch, 2*inch])
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ]))
                        story.append(table)
                
                elif isinstance(section_data, list):
                    # Convert list to table
                    if section_data and isinstance(section_data[0], dict):
                        headers = list(section_data[0].keys())
                        table_data = [headers]
                        
                        for item in section_data:
                            row = [str(item.get(h, '')) for h in headers]
                            table_data.append(row)
                        
                        col_widths = [5.5*inch / len(headers)] * len(headers)
                        table = Table(table_data, colWidths=col_widths)
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 9),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ]))
                        story.append(table)
                
                story.append(Spacer(1, 0.2*inch))
            
            # Build PDF
            doc.build(story)
            
            return str(filepath)
            
        except Exception as e:
            return f'Error: {str(e)}'
