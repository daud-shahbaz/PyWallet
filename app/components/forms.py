"""
Reusable form components for Streamlit.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from pywallet import config


def expense_form() -> Dict[str, Any]:
    """
    Render an expense entry form.
    
    Returns:
        Dictionary with form data (amount, category, description, date)
    """
    with st.form("add_expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            amount = st.number_input(
                "Amount (PKR)",
                min_value=int(config.MIN_EXPENSE_AMOUNT),
                max_value=int(config.MAX_EXPENSE_AMOUNT),
                value=0,
                step=1,
                help="Expense amount in PKR"
            )
        
        with col2:
            category = st.selectbox(
                "Category",
                options=config.DEFAULT_CATEGORIES,
                help="Select expense category"
            )
        
        col3, col4 = st.columns(2)
        
        with col3:
            date = st.date_input(
                "Date",
                value=datetime.now(),
                help="When did you make this expense?"
            )
        
        with col4:
            note = st.text_input(
                "Note",
                max_chars=config.MAX_NOTE_LENGTH,
                placeholder="e.g., 'Grocery shopping'",
                help="Optional description"
            )
        
        submitted = st.form_submit_button("Add Expense", use_container_width=True, type="primary")
        
        if submitted:
            return {
                "amount": amount,
                "category": category,
                "description": note,
                "date": date.strftime("%Y-%m-%d"),
                "submitted": True
            }
    
    return {"submitted": False}


def budget_form() -> Dict[str, Any]:
    """
    Render a budget entry form.
    
    Returns:
        Dictionary with form data (category, limit, alert_threshold)
    """
    with st.form("add_budget_form", clear_on_submit=True):
        category = st.selectbox(
            "Category",
            options=config.DEFAULT_CATEGORIES
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            limit = st.number_input(
                "Budget Limit (PKR)",
                min_value=0,
                step=100,
                help="Monthly budget limit"
            )
        
        with col2:
            alert_threshold = st.slider(
                "Alert at (% of limit)",
                0,
                100,
                80,
                help="Trigger alert when spending reaches this percentage"
            )
        
        submitted = st.form_submit_button("Set Budget", use_container_width=True, type="primary")
        
        if submitted:
            return {
                "category": category,
                "limit": limit,
                "alert_threshold": alert_threshold,
                "submitted": True
            }
    
    return {"submitted": False}

