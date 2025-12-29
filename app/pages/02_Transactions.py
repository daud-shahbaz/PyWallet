"""
Transactions - Add, Manage, Budget, Import/Export transactions and expenses
Displays:
- Add Transaction (Income/Expense)
- List of transactions with filters
- Delete Transaction
- Budget Management & Tracking
- Budget vs Actual Spending
- Category-wise budget tracking
- Import/Export data
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import json
import tempfile
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pywallet.modules.data_manager import DataManager
from pywallet.modules.analytics import Analytics
from pywallet import config
from pywallet.security.auth_utils import require_login, show_user_info

st.set_page_config(page_title="Transactions - PyWallet", page_icon=config.STREAMLIT_PAGE_ICON, layout="wide")

# Check authentication
require_login()
show_user_info()

st.title("Transactions & Budget Management")
st.markdown("Manage expenses and track your budget in one place")

# ============================================================================
#                                 Tabs
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Add Expense", 
    "View & Delete", 
    "Budget Tracking",
    "Budget Alerts",
    "Import/Export",
    "Data Management"
])

# ============================================================================
#                           Add Expense
# ============================================================================

with tab1:
    st.subheader("Record New Expense")
    st.markdown("Add an expense to track your spending. To add income, go to Dashboard > Income Tracker")
    
    with st.form("add_expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            expense_amount = st.number_input(
                "Expense Amount (PKR)",
                min_value=int(config.MIN_EXPENSE_AMOUNT),
                max_value=int(config.MAX_EXPENSE_AMOUNT),
                value=0,
                step=100,
                help="How much did you spend?",
                key="expense_amount_input"
            )
        
        with col2:
            expense_category = st.selectbox(
                "Category",
                options=config.DEFAULT_CATEGORIES,
                help="What category does this expense belong to?",
                key="expense_category_input"
            )
        
        col3, col4 = st.columns(2)
        
        with col3:
            expense_date = st.date_input(
                "Date",
                value=datetime.now(),
                help="When did this expense occur?",
                key="expense_date_input"
            )
        
        with col4:
            expense_note = st.text_input(
                "Description (Optional)",
                max_chars=config.MAX_NOTE_LENGTH,
                placeholder="e.g., 'Grocery shopping at Carrefour'",
                help="What did you buy?",
                key="expense_note_input"
            )
        
        if st.form_submit_button("Add Expense", use_container_width=True, type="primary"):
            if expense_amount > 0:
                from pywallet.security.auth import get_current_user
                current_user = get_current_user()
                success, message, transaction_id = DataManager.add_expense(
                    amount=expense_amount,
                    category=expense_category,
                    date=expense_date.strftime("%Y-%m-%d"),
                    note=expense_note or expense_category,
                    username=current_user
                )
                
                if success:
                    st.success(f"Expense Added: PKR {int(expense_amount):,}")
                    st.session_state.expenses_refreshed = True
                else:
                    st.error(message)
            else:
                st.error("Please enter an expense amount")

# ============================================================================
#                   View and Delete Transactions
# ============================================================================

with tab2:
    st.subheader("View & Manage Transactions")
    st.markdown("View your transactions and delete if needed")
    
    # Filters
    st.markdown("**Filters**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_category = st.multiselect(
            "By Category",
            options=["All"] + config.DEFAULT_CATEGORIES,
            default=["All"],
            help="Select categories to display"
        )
    
    with col2:
        filter_start_date = st.date_input(
            "From Date",
            value=None,
            help="Start date for filter"
        )
    
    with col3:
        filter_end_date = st.date_input(
            "To Date",
            value=None,
            help="End date for filter"
        )
    
    st.divider()
    
    # Apply filters
    if "All" in filter_category:
        categories = None
    else:
        categories = filter_category
    
    from pywallet.security.auth import get_current_user
    current_user = get_current_user()
    df = DataManager.load_dataframe(username=current_user)
    
    if df.empty:
        st.info("No expenses yet. Add your first expense in the 'Add Expense' tab!")
    else:
        # Apply category filter
        if categories:
            df = df[df['category'].isin(categories)]
        
        if filter_start_date:
            df = df[df['date'].dt.date >= filter_start_date]
        
        if filter_end_date:
            df = df[df['date'].dt.date <= filter_end_date]
        
        # Display
        if df.empty:
            st.info("No expenses match the selected filters.")
        else:
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Expenses", len(df))
            with col2:
                st.metric("Total Amount", f"PKR {df['amount'].sum():,.0f}")
            with col3:
                st.metric("Average Expense", f"PKR {df['amount'].mean():,.0f}")
            
            st.divider()
            
            # Display table
            st.markdown("**Expense Table**")
            df_display = df.sort_values('date', ascending=False).copy()
            df_display['date'] = df_display['date'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(
                df_display[['id', 'date', 'category', 'amount', 'note']],
                use_container_width=True,
                hide_index=True
            )
            
            st.divider()
            
            # Delete expense section
            st.markdown("**Delete Expense**")
            
            expense_ids = sorted(df['id'].unique())
            col1, col2 = st.columns([3, 1])
            
            with col1:
                selected_id = st.selectbox(
                    "Select expense to delete:",
                    options=expense_ids,
                    format_func=lambda x: f"ID {x}",
                    label_visibility="collapsed"
                )
            
            with col2:
                if st.button("Delete", use_container_width=True, type="secondary"):
                    success, message = DataManager.delete_expense(selected_id)
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

# ============================================================================
#                        Budget Tracking
# ============================================================================

with tab3:
    st.subheader("Budget Tracking & Management")
    st.markdown("Monitor spending, track budgets, and optimize your finances")
    
    @st.cache_data
    def load_budget_data():
        """Load and cache budget data"""
        df = DataManager.load_dataframe()
        budget_status = Analytics.budget_alert()
        return df, budget_status

    @st.cache_data
    def calculate_category_stats(df):
        """Calculate statistics for all categories"""
        stats = []
        for category in config.DEFAULT_CATEGORIES:
            budget_amt = config.DEFAULT_BUDGETS.get(category, 0)
            spending = df[df['category'] == category]['amount'].sum() if not df.empty else 0
            utilization = (spending / budget_amt * 100) if budget_amt > 0 else 0
            
            # Determine status
            if utilization > 100:
                status = 'critical'
            elif utilization >= 80:
                status = 'warning'
            else:
                status = 'ok'
            
            stats.append({
                'Category': category,
                'Budget': budget_amt,
                'Spending': int(spending),
                'Remaining': max(0, budget_amt - spending),
                'Utilization': utilization,
                'Status': status,
                'Over': max(0, spending - budget_amt)
            })
        
        return pd.DataFrame(stats).sort_values('Spending', ascending=False)
    
    # Load data
    df, budget_status = load_budget_data()
    df_stats = calculate_category_stats(df)
    
    # Budget Health
    st.subheader("Budget Health")
    
    # Calculate metrics
    total_budget = sum(config.DEFAULT_BUDGETS.values())
    total_spent = df['amount'].sum() if not df.empty else 0
    overall_utilization = (total_spent / total_budget * 100) if total_budget > 0 else 0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        on_track_pct = (budget_status['on_track_count'] / budget_status['total_categories'] * 100) if budget_status['total_categories'] > 0 else 0
        st.metric("On Track", f"{budget_status['on_track_count']}/{budget_status['total_categories']}", f"{on_track_pct:.0f}%")
    
    with col2:
        warning_pct = (budget_status['warning_count'] / budget_status['total_categories'] * 100) if budget_status['total_categories'] > 0 else 0
        st.metric("Warnings", f"{budget_status['warning_count']}/{budget_status['total_categories']}", f"{warning_pct:.0f}%")
    
    with col3:
        critical_pct = (budget_status['critical_count'] / budget_status['total_categories'] * 100) if budget_status['total_categories'] > 0 else 0
        st.metric("Critical", f"{budget_status['critical_count']}/{budget_status['total_categories']}", f"{critical_pct:.0f}%")
    
    with col4:
        st.metric("Total Budget", f"PKR {int(total_budget):,}")
    
    with col5:
        if overall_utilization > 100:
            st.metric("Total Usage", f"{overall_utilization:.1f}%", delta=f"Over by PKR {int(total_spent - total_budget):,}", delta_color="inverse")
        elif overall_utilization >= 80:
            st.metric("Total Usage", f"{overall_utilization:.1f}%", delta="Caution")
        else:
            st.metric("Total Usage", f"{overall_utilization:.1f}%", delta="On Track", delta_color="off")
    
    st.divider()
    
    # Budget vs Spending
    st.subheader("Budget vs Actual Spending")
    
    fig_comparison = go.Figure()
    
    fig_comparison.add_trace(go.Bar(
        name='Budget',
        x=df_stats['Category'],
        y=df_stats['Budget'],
        marker_color='rgba(100, 150, 255, 0.6)',
        hovertemplate='<b>%{x}</b><br>Budget: PKR %{y:,}<extra></extra>'
    ))
    
    fig_comparison.add_trace(go.Bar(
        name='Spending',
        x=df_stats['Category'],
        y=df_stats['Spending'],
        marker_color='rgba(255, 100, 100, 0.7)',
        hovertemplate='<b>%{x}</b><br>Spending: PKR %{y:,}<extra></extra>'
    ))
    
    fig_comparison.update_layout(
        barmode='group',
        title='Budget vs Actual Spending by Category',
        xaxis_title='Category',
        yaxis_title='Amount (PKR)',
        height=400,
        hovermode='x unified',
        showlegend=True,
        template='plotly_white'
    )
    
    st.plotly_chart(fig_comparison, use_container_width=True)
    
    st.divider()
    
    # Budget Utilization
    st.subheader("Budget Utilization by Category")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Top 5 Categories by Spending**")
        
        for idx, row in df_stats.head(5).iterrows():
            utilization = min(100, row['Utilization'])
            
            if row['Status'] == 'critical':
                status_text = '[CRITICAL]'
            elif row['Status'] == 'warning':
                status_text = '[WARNING]'
            else:
                status_text = '[OK]'
            
            st.write(f"**{row['Category']}** {status_text}")
            st.progress(utilization / 100)
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.caption(f"Spent: PKR {row['Spending']:,}")
            with col_b:
                st.caption(f"Budget: PKR {int(row['Budget']):,}")
            with col_c:
                st.caption(f"{utilization:.0f}% Used")
    
    with col2:
        st.write("**Categories Summary**")
        
        heatmap_data = df_stats[['Category', 'Utilization']].copy()
        heatmap_data['Utilization'] = heatmap_data['Utilization'].clip(0, 150)
        
        fig_heat = px.bar(
            heatmap_data.sort_values('Utilization', ascending=True).tail(10),
            x='Utilization',
            y='Category',
            orientation='h',
            color='Utilization',
            color_continuous_scale='RdYlGn_r',
            title='Budget Utilization Distribution',
            height=350,
            labels={'Utilization': 'Used %'}
        )
        
        fig_heat.add_vline(x=100, line_dash='dash', line_color='red', annotation_text='100% Limit')
        fig_heat.add_vline(x=80, line_dash='dot', line_color='orange', annotation_text='Warning')
        
        st.plotly_chart(fig_heat, use_container_width=True)
    
    st.divider()
    
    # Budget Reference Table
    st.subheader("Budget Reference")
    
    display_df = df_stats[['Category', 'Budget', 'Spending', 'Remaining', 'Utilization', 'Status']].copy()
    display_df.columns = ['Category', 'Budget (PKR)', 'Spending (PKR)', 'Remaining (PKR)', 'Used %', 'Status']
    
    display_df['Budget (PKR)'] = display_df['Budget (PKR)'].apply(lambda x: f"PKR {int(x):,}")
    display_df['Spending (PKR)'] = display_df['Spending (PKR)'].apply(lambda x: f"PKR {int(x):,}")
    display_df['Remaining (PKR)'] = display_df['Remaining (PKR)'].apply(lambda x: f"PKR {int(x):,}")
    display_df['Used %'] = display_df['Used %'].apply(lambda x: f"{x:.1f}%")
    display_df['Status'] = display_df['Status'].apply(lambda x: f"[{x.upper()}]")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# ============================================================================
#                          Budget Alerts
# ============================================================================

with tab4:
    st.subheader("Budget Alerts & Warnings")
    st.markdown("Real-time alerts for budget overages and warnings")
    
    df, budget_status = load_budget_data()
    
    if budget_status['alerts']:
        critical_alerts = [a for a in budget_status['alerts'] if a['status'] == 'critical']
        warning_alerts = [a for a in budget_status['alerts'] if a['status'] == 'warning']
        
        col1, col2 = st.columns(2)
        
        if critical_alerts:
            with col1:
                st.subheader("Critical Alerts")
                for alert in critical_alerts[:3]:
                    over_budget = int(alert['spending'] - alert['budget'])
                    with st.container():
                        st.error(f"**{alert['category']}** - Over by PKR {over_budget:,}")
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Spending", f"PKR {int(alert['spending']):,}")
                        with col_b:
                            st.metric("Budget", f"PKR {int(alert['budget']):,}")
                        with col_c:
                            st.metric("Used", f"{alert['percentage']:.0f}%")
        
        if warning_alerts:
            with col2:
                st.subheader("Warnings")
                for alert in warning_alerts[:3]:
                    remaining = int(alert['budget'] - alert['spending'])
                    with st.container():
                        st.warning(f"**{alert['category']}** - PKR {remaining:,} remaining")
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Spending", f"PKR {int(alert['spending']):,}")
                        with col_b:
                            st.metric("Budget", f"PKR {int(alert['budget']):,}")
                        with col_c:
                            st.metric("Used", f"{alert['percentage']:.0f}%")
    else:
        st.success("All budgets are on track! Keep up the good spending habits!")

# ============================================================================
#                        Import and Export
# ============================================================================

with tab5:
    st.subheader("Import Transactions from CSV")
    st.markdown("Upload a CSV file to import transactions")
    
    st.info("""
    **CSV Format Required:**
    - **amount**: Numeric value (e.g., 500, 1200.50)
    - **category**: Must match one of the available categories
    - **date**: YYYY-MM-DD format (e.g., 2024-01-15)
    - **note** (optional): Text description
    
    **Example:**
    ```
    amount,category,date,note
    500,Food,2024-01-15,Grocery shopping
    1200,Transport,2024-01-16,Taxi fare
    ```
    """)
    
    uploaded_file = st.file_uploader(
        "Choose CSV file to import:",
        type=["csv"],
        help="Maximum 200MB"
    )
    
    if uploaded_file:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(f"File: {uploaded_file.name}")
        with col2:
            import_btn = st.button("Import", use_container_width=True, type="primary")
        
        if import_btn:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name
            
            try:
                with st.spinner("Importing data..."):
                    success, message, imported_count = DataManager.import_from_csv(Path(tmp_path))
                    
                    if success:
                        st.success(message)
                        st.balloons()
                        st.info(f"Imported {imported_count} transactions successfully!")
                    else:
                        st.error(message)
            finally:
                os.unlink(tmp_path)
    
    st.divider()
    
    st.subheader("Export Transactions")
    st.markdown("Download your transaction data for backup or transfer")
    
    current_user = get_current_user()
    df = DataManager.load_dataframe(username=current_user)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### CSV Format")
        st.caption("Good for: Excel, Google Sheets, other apps")
        if st.button("Export as CSV", use_container_width=True):
            try:
                success, message = Analytics.export_to_csv()
                if success:
                    try:
                        with open(config.DATA_DIR / "expenses_export.csv", 'r') as f:
                            csv_content = f.read()
                        st.download_button(
                            label="Download CSV",
                            data=csv_content,
                            file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    except:
                        st.error("Could not read exported file")
                else:
                    st.error(message)
            except Exception as e:
                st.error(f"Export failed: {e}")
    
    with col2:
        st.markdown("### JSON Format")
        st.caption("Good for: Full backup, preservation")
        if st.button("Export as JSON", use_container_width=True):
            try:
                data = DataManager.load_data()
                json_str = json.dumps(data, indent=2, default=str)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Export failed: {e}")

# ============================================================================
#                        Data Management
# ============================================================================

with tab6:
    st.subheader("Data Management")
    st.markdown("View and manage your transaction data")
    
    current_user = get_current_user()
    df = DataManager.load_dataframe(username=current_user)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Transactions", len(df))
    with col2:
        if not df.empty:
            st.metric("Total Amount", f"PKR {df['amount'].sum():,.0f}")
        else:
            st.metric("Total Amount", "PKR 0")
    with col3:
        if not df.empty:
            st.metric("Date Range", f"{df['date'].min().date()} to {df['date'].max().date()}")
        else:
            st.metric("Date Range", "No data")
    
    st.divider()
    
    # Data storage info
    st.markdown("**Data Storage Information**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Primary File**")
        st.code(str(config.EXPENSES_FILE), language="")
        if config.EXPENSES_FILE.exists():
            size_mb = config.EXPENSES_FILE.stat().st_size / (1024 * 1024)
            st.caption(f"Size: {size_mb:.2f} MB")
    
    with col2:
        st.markdown("**Backup Directory**")
        st.code(str(config.BACKUP_DIR), language="")
        if config.BACKUP_DIR.exists():
            backup_count = len(list(config.BACKUP_DIR.glob("*")))
            st.caption(f"Backups created: {backup_count}")
    
    st.divider()
    
    # Categories in use
    st.markdown("**Categories in Use**")
    
    if not df.empty:
        categories_used = df['category'].value_counts().to_dict()
        cat_data = [
            {'Category': k, 'Count': v, 'Percentage': f"{(v/len(df)*100):.1f}%"}
            for k, v in sorted(categories_used.items(), key=lambda x: x[1], reverse=True)
        ]
        st.dataframe(cat_data, use_container_width=True, hide_index=True)
    else:
        st.info("No transactions yet")

