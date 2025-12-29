"""
Authentication helper utilities for Streamlit pages.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pywallet.security.auth import is_logged_in, get_current_user, logout

def require_login():
    """
    Decorator/check to ensure user is authenticated.
    Call this at the top of each page that requires authentication.
    """
    if not is_logged_in():
        st.warning("Please log in first!")
        st.info("Return to the Home page to log in.")
        st.stop()

def show_user_info():
    """Display current user info in sidebar."""
    current_user = get_current_user()
    if current_user:
        col1, col2 = st.sidebar.columns([4, 1])
        with col1:
            st.sidebar.caption(f"Logged in as: **{current_user}**")
        with col2:
            if st.sidebar.button("Logout", use_container_width=True):
                logout()
                st.rerun()

