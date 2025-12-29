"""
Reusable chart components for Streamlit.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Any, Optional


def expense_chart(df: pd.DataFrame, title: str = "Expenses Over Time") -> None:
    """
    Display an expense over time chart.
    
    Args:
        df: DataFrame with 'date' and 'amount' columns
        title: Chart title
    """
    if df.empty:
        st.info("No data available for chart")
        return
    
    # Group by date and sum amounts
    daily = df.groupby(df['date'].dt.date)['amount'].sum().reset_index()
    
    fig = px.line(
        daily,
        x="date",
        y="amount",
        title=title,
        markers=True
    )
    
    fig.update_layout(
        hovermode="x unified",
        xaxis_title="Date",
        yaxis_title="Amount (PKR)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def category_chart(df: pd.DataFrame, title: str = "Spending by Category") -> None:
    """
    Display a category spending pie chart.
    
    Args:
        df: DataFrame with 'category' and 'amount' columns
        title: Chart title
    """
    if df.empty:
        st.info("No data available for chart")
        return
    
    category_data = df.groupby('category')['amount'].sum().reset_index()
    
    fig = px.pie(
        category_data,
        values="amount",
        names="category",
        title=title,
        hole=0.3
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)


def monthly_trend_chart(monthly_data: Dict[str, float]) -> None:
    """
    Display monthly spending trend.
    
    Args:
        monthly_data: Dictionary with months and amounts
    """
    if not monthly_data:
        st.info("No monthly data available")
        return
    
    months = list(monthly_data.keys())
    amounts = list(monthly_data.values())
    
    fig = px.bar(
        x=months,
        y=amounts,
        title="Monthly Spending Trend",
        labels={"x": "Month", "y": "Amount (PKR)"}
    )
    
    fig.update_layout(height=400, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)


def comparison_chart(categories: List[str], budgets: List[float], spent: List[float]) -> None:
    """
    Display budget vs spent comparison chart.
    
    Args:
        categories: List of category names
        budgets: List of budget amounts
        spent: List of spent amounts
    """
    df = pd.DataFrame({
        'Category': categories,
        'Budget': budgets,
        'Spent': spent
    })
    
    fig = px.bar(
        df,
        x="Category",
        y=["Budget", "Spent"],
        title="Budget vs Actual Spending",
        barmode="group",
        labels={"value": "Amount (PKR)"}
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
