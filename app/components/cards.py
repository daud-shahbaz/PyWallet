import streamlit as st
from typing import Union, Optional


def metric_card(label: str, value: Union[int, float], suffix: str = "", delta: Optional[str] = None) -> None:
    """
    Display a metric card with label, value, and optional delta.
    
    Args:
        label: Card label
        value: Metric value
        suffix: PKR, $
        delta: Optional change indicator
    """
    st.metric(label, f"{value}{suffix}", delta=delta)


def summary_card(title: str, content: str, color: str = "blue") -> None:
    """
    Display a summary card.
    
    Args:
        title: Card title
        content: Card content
        color: Card color theme (blue, green, red, orange)
    """
    st.markdown(
        f"""
        <div style="
            background-color: {_get_color(color)};
            padding: 20px;
            border-radius: 10px;
            color: white;
            margin-bottom: 10px;
        ">
            <h3>{title}</h3>
            <p>{content}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def budget_status_card(budget_status: dict) -> None:
    """
    Display budget status summary.
    
    Args:
        budget_status: Dictionary with budget status information
    """
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("On Track", budget_status.get('on_track_count', 0))
    with col2:
        st.metric("Warnings", budget_status.get('warning_count', 0), 
                 delta="Caution" if budget_status.get('warning_count', 0) > 0 else "")
    with col3:
        st.metric("Critical", budget_status.get('critical_count', 0), 
                 delta="Exceeded" if budget_status.get('critical_count', 0) > 0 else "")
    
    if budget_status.get('alerts'):
        st.warning("Budget Alerts:")
        for alert in budget_status['alerts']:
            st.markdown(f"• **{alert.get('message')}** - {alert.get('percentage', 0):.0f}% of budget used")


def metrics(today_total: float, month_total: float, month_count: int, all_total: float, all_count: int) -> None:
    """
    Display Metrics dashboard
    
    Args:
        today_total: Today's spending total
        month_total: This month's total
        month_count: This month's transaction count
        all_total: All time total
        all_count: All time transaction count
    """
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Today's Spending", f"PKR {today_total:.0f}")
    with col2:
        st.metric("This Month", f"PKR {month_total:.0f}", delta=f"{month_count} transactions")
    with col3:
        st.metric("Total Spending", f"PKR {all_total:.0f}")
    with col4:
        st.metric("Total Transactions", all_count)


def _get_color(color: str) -> str:
    """Map color name to hex value."""
    colors = {
        "blue": "#1f77b4",
        "green": "#2ca02c",
        "red": "#d62728",
        "orange": "#ff7f0e",
    }
    return colors.get(color, "#1f77b4")
