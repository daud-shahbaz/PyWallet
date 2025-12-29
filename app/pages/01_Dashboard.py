"""
Dashboard - Consolidated Financial Overview:
- Key metrics and KPIs
- Spending trends and forecasts
- Category breakdown visuals
- Budget health at a glance
- Quick action buttons
- Income vs Expenses comparison
- Financial health score
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import json
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pywallet.modules.data_manager import DataManager
from pywallet.modules.analytics import Analytics
from pywallet import config
from pywallet.security.auth_utils import require_login, show_user_info

st.set_page_config(page_title="Dashboard - PyWallet", page_icon=config.STREAMLIT_PAGE_ICON, layout="wide")

# Check authentication
require_login()
show_user_info()

st.title("Dashboard")
st.markdown("Your Financial Overview at a Glance")

# ============================================================================
#                          Load Data
# ============================================================================

df = DataManager.load_dataframe()

if df.empty:
    st.info("No transactions found. Start by adding your first expense to see your financial overview!")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Add Transaction", use_container_width=True):
            st.switch_page("pages/02_Transactions.py")
    with col2:
        if st.button("View Analytics", use_container_width=True):
            st.switch_page("pages/03_Analytics.py")
    with col3:
        if st.button("Settings", use_container_width=True):
            st.switch_page("pages/05_Settings.py")
else:
    # ============================================================================
    #                    Key Metrics & KPIs
    # ============================================================================
    
    st.subheader("Key Metrics")
    
    # Today's spending
    today = datetime.now().strftime("%Y-%m-%d")
    today_data = df[df['date'].dt.strftime("%Y-%m-%d") == today]
    today_total = float(today_data['amount'].sum())
    
    # This month
    month_summary = Analytics.monthly_summary()
    month_total = month_summary['total']
    month_count = month_summary['transaction_count']
    
    # All time
    all_total = float(df['amount'].sum())
    all_count = len(df)
    
    # Average calculations
    avg_daily_spend = all_total / len(df) if len(df) > 0 else 0
    avg_transaction = all_total / all_count if all_count > 0 else 0
    
    # Projected month total (if we're mid-month)
    current_day = datetime.now().day
    days_in_month = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    days_in_month = days_in_month.day
    projected_month = (month_total / current_day * days_in_month) if current_day > 0 else month_total
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Today's Spending", f"PKR {today_total:.0f}", help="Amount spent today")
    with col2:
        st.metric("This Month", f"PKR {month_total:,.0f}", delta=f"{month_count} txns", help="Current month total")
    with col3:
        st.metric("Avg Per Day", f"PKR {avg_daily_spend:,.0f}", help="Average daily spending")
    with col4:
        st.metric("Projected Month", f"PKR {projected_month:,.0f}", help="Estimated month total if spending continues")
    with col5:
        st.metric("Total (All-Time)", f"PKR {all_total:,.0f}", delta=f"{all_count} txns", help="Total spending all-time")
    
    st.divider()
    
    # ============================================================================
    #                    Spending Trends & Visuals
    # ============================================================================
    
    col1, col2 = st.columns(2)
    
    # ============================================================================
    #                    Monthly Spending Trend
    # ============================================================================
    
    with col1:
        st.subheader("Monthly Spending Trend")
        
        # Get last 6 months data
        today_date = datetime.now()
        months_data = []
        
        for i in range(5, -1, -1):
            month_date = today_date - timedelta(days=30*i)
            year = month_date.year
            month = month_date.month
            
            monthly_sum = Analytics.monthly_summary(year=year, month=month)
            months_data.append({
                'Month': month_date.strftime('%b %Y'),
                'Amount': monthly_sum['total'],
                'YearMonth': month_date.strftime('%Y-%m')
            })
        
        df_trend = pd.DataFrame(months_data)
        
        fig_trend = px.line(
            df_trend,
            x='Month',
            y='Amount',
            markers=True,
            title='Last 6 Months Spending Trend',
            labels={'Amount': 'Spending (PKR)', 'Month': 'Month'},
            template='plotly_white',
            height=350
        )
        fig_trend.update_traces(line=dict(color='#FF6B6B', width=3), marker=dict(size=8))
        fig_trend.update_layout(hovermode='x unified')
        st.plotly_chart(fig_trend, use_container_width=True)
    
    # ============================================================================
    #                    Top Spending Categories
    # ============================================================================
    
    with col2:
        st.subheader("Top Spending Categories")
        
        category_spending = df.groupby('category')['amount'].sum().sort_values(ascending=False).head(8)
        
        fig_pie = px.pie(
            values=category_spending.values,
            names=category_spending.index,
            title='Spending by Category',
            template='plotly_white',
            hole=0.4,
            height=350
        )
        fig_pie.update_traces(textposition='inside', textinfo='label+percent')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    st.divider()
    
    # ============================================================================
    #                    Income vs Expenses & Financial Health
    # ============================================================================
    
    col1, col2 = st.columns(2)
    
    # ============================================================================
    #                    Income vs Expenses
    # ============================================================================
    
    with col1:
        st.subheader("Income vs Expenses")
        
        # Load income data
        income_file = Path(str(Path(__file__).parent.parent.parent)) / "pywallet" / "data" / "income.json"
        income_data = []
        if income_file.exists():
            try:
                with open(income_file, 'r') as f:
                    income_data = json.load(f)
            except:
                income_data = []
        
        current_year = datetime.now().year
        current_month = datetime.now().month
        current_month_income = [inc for inc in income_data if inc.get('month') == current_month and inc.get('year') == current_year]
        total_income = sum([inc.get('amount', 0) for inc in current_month_income])
        total_expenses = df['amount'].sum() if not df.empty else 0
        savings = total_income - total_expenses
        savings_rate = (savings / total_income * 100) if total_income > 0 else 0
        
        # Create comparison chart
        fig_comparison = go.Figure(data=[
            go.Bar(name='Income', x=['This Month'], y=[total_income], marker_color='rgba(0, 200, 100, 0.7)'),
            go.Bar(name='Expenses', x=['This Month'], y=[total_expenses], marker_color='rgba(255, 100, 100, 0.7)')
        ])
        fig_comparison.update_layout(
            barmode='group',
            title='Income vs Expenses (This Month)',
            yaxis_title='Amount (PKR)',
            height=300,
            hovermode='x unified',
            showlegend=True
        )
        st.plotly_chart(fig_comparison, use_container_width=True)
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Income", f"PKR {int(total_income):,}")
        with col_b:
            st.metric("Expenses", f"PKR {int(total_expenses):,}")
        with col_c:
            st.metric("Net Savings", f"PKR {int(savings):,}", delta=f"{max(0, savings_rate):.1f}%")
    
    # ============================================================================
    #                    Budget Health Score
    # ============================================================================
    
    with col2:
        st.subheader("Budget Health")
        
        budget_status = Analytics.budget_alert()
        total_budget = sum(config.DEFAULT_BUDGETS.values())
        total_spent = df['amount'].sum() if not df.empty else 0
        overall_utilization = (total_spent / total_budget * 100) if total_budget > 0 else 0
        
        # Create gauge chart for budget health
        fig_gauge = go.Figure(data=[go.Indicator(
            mode="gauge+number+delta",
            value=overall_utilization,
            title={'text': "Budget Utilization %"},
            delta={'reference': 80, 'suffix': "% vs Warning"},
            gauge={
                'axis': {'range': [0, 150]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgreen"},
                    {'range': [50, 80], 'color': "lightyellow"},
                    {'range': [80, 100], 'color': "orange"},
                    {'range': [100, 150], 'color': "lightcoral"}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 100
                }
            }
        )])
        fig_gauge.update_layout(height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            on_track = budget_status['on_track_count']
            st.metric("On Track", on_track)
        with col_b:
            warnings = budget_status['warning_count']
            st.metric("Warnings", warnings)
        with col_c:
            critical = budget_status['critical_count']
            st.metric("Critical", critical)
    
    st.divider()
    
    # ============================================================================
    #                    Recent Transactions
    # ============================================================================
    
    st.subheader("Recent Transactions")
    recent = df.sort_values('date', ascending=False).head(8)
    display_cols = ['id', 'date', 'category', 'amount', 'note']
    
    df_display = recent[display_cols].copy()
    df_display['date'] = df_display['date'].dt.strftime('%Y-%m-%d')
    
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            'id': st.column_config.NumberColumn('ID', width=50),
            'date': st.column_config.TextColumn('Date', width=100),
            'category': st.column_config.TextColumn('Category', width=100),
            'amount': st.column_config.NumberColumn('Amount (PKR)', format="PKR %d"),
            'note': st.column_config.TextColumn('Note', width=200)
        }
    )
    
    st.divider()
    
    # ============================================================================
    #                    Quick Actions
    # ============================================================================
    
    st.subheader("Quick Actions")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("Add Transaction", use_container_width=True, key="quick_add"):
            st.switch_page("pages/02_Transactions.py")
    
    with col2:
        if st.button("Transactions", use_container_width=True, key="quick_trans"):
            st.switch_page("pages/02_Transactions.py")
    
    with col3:
        if st.button("Analytics", use_container_width=True, key="quick_analytics"):
            st.switch_page("pages/03_Analytics.py")
    
    with col4:
        if st.button("Forecasts", use_container_width=True, key="quick_forecast"):
            st.switch_page("pages/04_Forecasts.py")
    
    with col5:
        if st.button("Settings", use_container_width=True, key="quick_settings"):
            st.switch_page("pages/05_Settings.py")
    
    st.divider()
    
    # ============================================================================
    #                                Tabs
    # ============================================================================
    
    tab1, tab2, tab3 = st.tabs(["Cash Flow Details", "Income Tracker", "Subscriptions"])
    
    # ============================================================================
    #                            Cash Flow Details
    # ============================================================================
    
    with tab1:
        st.subheader("Cash Flow Analysis")
        
        income_file = Path(str(Path(__file__).parent.parent.parent)) / "pywallet" / "data" / "income.json"
        income_data = []
        if income_file.exists():
            try:
                with open(income_file, 'r') as f:
                    income_data = json.load(f)
            except:
                income_data = []
        
        current_year = datetime.now().year
        current_month = datetime.now().month
        current_month_income = [inc for inc in income_data if inc.get('month') == current_month and inc.get('year') == current_year]
        total_income = sum([inc.get('amount', 0) for inc in current_month_income])
        total_expenses = df['amount'].sum() if not df.empty else 0
        savings = total_income - total_expenses
        savings_rate = (savings / total_income * 100) if total_income > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Income", f"PKR {int(total_income):,}")
        with col2:
            st.metric("Expenses", f"PKR {int(total_expenses):,}")
        with col3:
            st.metric("Savings", f"PKR {int(savings):,}", delta=f"{savings_rate:.1f}%")
        with col4:
            st.metric("Savings Rate", f"{max(0, savings_rate):.1f}%")
    
    # ============================================================================
    #                            Income Tracking
    # ============================================================================
    
    with tab2:
        st.subheader("Record Income")
        st.caption("Add your income sources here (salary, freelance, gifts, etc)")
        
        col1, col2 = st.columns([2.5, 1])
        
        with col1:
            income_amount = st.number_input("Income Amount (PKR)", min_value=0, step=1000, value=0, key="income_input", help="How much did you earn?")
        with col2:
            if st.button("Add Income", use_container_width=True, key="btn_add_income", help="No category needed - just amount"):
                if income_amount > 0:
                    new_income = {
                        'id': len(income_data) + 1,
                        'amount': int(income_amount),
                        'source': "Income",
                        'date': datetime.now().strftime("%Y-%m-%d"),
                        'month': datetime.now().month,
                        'year': datetime.now().year
                    }
                    income_data.append(new_income)
                    income_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(income_file, 'w') as f:
                        json.dump(income_data, f, indent=2)
                    st.success(f"Added Income: PKR {int(income_amount):,}")
                    st.rerun()
                else:
                    st.error("Please enter an income amount")
        
        if current_month_income:
            st.write("**This Month's Income**")
            df_inc = pd.DataFrame(current_month_income)
            df_inc['Amount'] = df_inc['amount'].apply(lambda x: f"PKR {int(x):,}")
            st.dataframe(df_inc[['source', 'Amount', 'date']], use_container_width=True, hide_index=True)
        else:
            st.info("No income recorded this month yet")
    
    # ============================================================================
    #                            Subscriptions
    # ============================================================================
    
    with tab3:
        st.subheader("Subscriptions and Recurring Expenses")
        
        recurring_file = Path(str(Path(__file__).parent.parent.parent)) / "pywallet" / "data" / "recurring_expenses.json"
        recurring_data = []
        if recurring_file.exists():
            try:
                with open(recurring_file, 'r') as f:
                    recurring_data = json.load(f)
            except:
                recurring_data = []
        
        col1, col2, col3 = st.columns([2, 1.2, 1])
        
        with col1:
            rec_name = st.text_input("Name", placeholder="Netflix, Internet, etc", key="rec_name")
        with col2:
            rec_amount = st.number_input("Cost (PKR)", min_value=0, step=100, value=0, key="rec_amount")
        with col3:
            if st.button("Add Subscription", use_container_width=True, key="btn_add_sub"):
                if rec_name and rec_amount > 0:
                    new_rec = {
                        'id': len(recurring_data) + 1,
                        'name': rec_name,
                        'amount': int(rec_amount),
                        'category': "Other",
                        'frequency': "Monthly",
                        'start_date': datetime.now().strftime("%Y-%m-%d"),
                        'status': 'Active',
                        'created_date': datetime.now().strftime("%Y-%m-%d")
                    }
                    recurring_data.append(new_rec)
                    recurring_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(recurring_file, 'w') as f:
                        json.dump(recurring_data, f, indent=2)
                    st.success(f"Added: {rec_name}")
                    st.rerun()
        
        active_recurring = [r for r in recurring_data if r['status'] == 'Active']
        
        if active_recurring:
            total_monthly = sum([r['amount'] for r in active_recurring])
            st.metric("Total Monthly Cost", f"PKR {int(total_monthly):,}")
            
            st.write("**Active Subscriptions:**")
            for rec in active_recurring[:10]:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"* **{rec['name']}**: PKR {int(rec['amount']):,}/month")
                with col2:
                    if st.button("Remove", key=f"rem_{rec['id']}", use_container_width=True):
                        recurring_data = [r for r in recurring_data if r['id'] != rec['id']]
                        with open(recurring_file, 'w') as f:
                            json.dump(recurring_data, f, indent=2)
                        st.success("Subscription removed")
                        st.rerun()
        else:
            st.info("No active subscriptions tracked yet")
    
    st.divider()
    
    st.caption("Dashboard updated in real-time | Last sync: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
