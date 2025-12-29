"""
PyWallet - Multipage Streamlit Application with User Authentication

Structure:
- Login/Register: User authentication
- Dashboard: Overview and key metrics
- Transactions: Add/manage expenses, budget tracking, and alerts
- Analytics: Financial analysis and insights
- Forecasts: ML predictions, anomaly detection, and patterns
- Settings: Configuration and preferences
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import pywallet
from pywallet import config
from pywallet.security.auth import login, register, is_logged_in, logout, get_current_user

# ============================================================================
#                              Page Configuration
# ============================================================================

st.set_page_config(
    page_title=config.STREAMLIT_PAGE_TITLE,
    page_icon=config.STREAMLIT_PAGE_ICON,
    layout=config.STREAMLIT_LAYOUT,
    initial_sidebar_state=config.STREAMLIT_SIDEBAR_STATE,
)

# ============================================================================
#                            Authentication Check
# ============================================================================

def show_login_page():
    """Display login/register page."""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("PyWallet")
        st.markdown("### Secure Personal Finance Manager")
        st.markdown("---")
        
        auth_tab1, auth_tab2 = st.tabs(["Login", "Register"])
        
        with auth_tab1:
            st.subheader("Login to Your Account")
            login_username = st.text_input("Username", key="login_user")
            login_password = st.text_input("Password", type="password", key="login_pass")
            
            if st.button("Login", use_container_width=True, type="primary"):
                if login(login_username, login_password):
                    st.success("Logged in successfully!")
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")
        
        with auth_tab2:
            st.subheader("Create a New Account")
            reg_username = st.text_input("Choose a Username (min 3 chars)", key="reg_user")
            reg_password = st.text_input("Choose a Password (min 8 chars)", type="password", key="reg_pass")
            reg_password_confirm = st.text_input("Confirm Password", type="password", key="reg_pass_confirm")
            
            if st.button("Register", use_container_width=True, type="primary"):
                if reg_password != reg_password_confirm:
                    st.error("Passwords do not match!")
                elif register(reg_username, reg_password):
                    st.success("Account created successfully! Please log in.")
                else:
                    st.error("Registration failed. Please try again.")
        

def show_main_app():
    """Display the main application."""
    # ========================================================================
    #                                  Sidebar
    # ========================================================================
    
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        st.sidebar.title("PyWallet")
    with col2:
        if st.sidebar.button("Logout", use_container_width=True):
            logout()
            st.session_state.authenticated = False
            st.rerun()
    
    st.sidebar.markdown("---")
    
    current_user = get_current_user()
    st.sidebar.markdown(
        f"Personal Finance Manager  \n"
        f"*User: {current_user}*"
    )
    st.sidebar.markdown("---")

# ============================================================================
#                               Session State
# ============================================================================

def init_session_state():
    """Initialize Streamlit session state variables."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = is_logged_in()
    
    if 'expenses_refreshed' not in st.session_state:
        st.session_state.expenses_refreshed = False
    
    if 'last_added_expense' not in st.session_state:
        st.session_state.last_added_expense = None
    
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = 'All'
    
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = 'table'

init_session_state()

# ============================================================================
#                                Main Logic
# ============================================================================

if not st.session_state.authenticated:
    show_login_page()
else:
    show_main_app()
    
    # ========================================================================
    #                               Main Page Content
    # ========================================================================
    
    st.title("PyWallet - Personal Money Manager")
    st.markdown("""
    **Your secure personal finance manager**
    
    Track expenses, manage budgets, and get AI-powered insights. All your data stays on your device - no cloud, no internet required.
    
    **Getting Started:**
    1. **Transactions** - Add income and expenses with categories and notes
    2. **Budget Tracking** - Set spending limits per category, get alerts at 80% and when over budget
    3. **Analytics** - View monthly spending trends, category breakdowns, and patterns
    4. **Forecasts** - Get AI predictions for next month, detect unusual transactions, receive recommendations
    5. **Settings** - Customize currency, timezone, categories, and export/import data as CSV or JSON
    
    **Key Features:**
    - Real-time budget monitoring with visual progress indicators
    - Month-over-month spending analysis and trends
    - Import/export data (CSV for spreadsheets, JSON for backups)
    - Local storage with optional encryption
    - No internet connection required
    - Each user has isolated, secure data access
    
    **Tips for Best Results:**
    - Add transactions regularly for accurate insights
    - Use clear descriptions to remember spending context
    - Review analytics monthly to track progress
    - Export data regularly as backup
    """)
    
    st.markdown("---")
    st.caption(
        f"PyWallet | User: {get_current_user()} | Secure - Local - Private"
    )

