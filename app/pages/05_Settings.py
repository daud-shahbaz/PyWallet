"""
Settings:
- Account and Profile management
- Notification preferences
- Data and Privacy controls
- Category customization
- Budget defaults
- System preferences
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import json
from datetime import datetime
import os

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pywallet import config
import pywallet
from pywallet.security.auth_utils import require_login, show_user_info
from pywallet.security.auth import get_current_user

st.set_page_config(page_title="Settings - PyWallet", page_icon=config.STREAMLIT_PAGE_ICON, layout="wide")

# Check authentication
require_login()
show_user_info()

st.title("Settings")

# Get current user
current_user = get_current_user()

# ============================================================================
#                           Setting Storage
# ============================================================================

SETTINGS_FILE = Path(config.DATA_DIR) / f"{current_user}_settings.json"

def load_user_settings():
    """Load user settings from file"""
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return get_default_settings()

def get_default_settings():
    """Get default settings"""
    return {
        'currency': 'PKR',
        'timezone': 'Asia/Karachi',
        'date_format': 'YYYY-MM-DD',
        'theme': 'Light',
        'dashboard_view': 'Summary',
        'items_per_page': 25,
        'decimal_places': 2,
        'default_expense_type': 'Need',
        'recurring_default': False,
        'auto_categorize': True,
        'round_to_nearest': 'None',
        'budget_alert_threshold': 80,
        'critical_alert_threshold': 95,
        'budget_exceeded_alert': True,
        'high_spending_alert': True,
        'anomaly_alert': True,
        'bill_reminder_alert': True,
        'budget_alert_freq': 'Immediate',
        'spending_alert_freq': 'Daily',
        'anomaly_alert_freq': 'Daily',
        'bill_reminder_freq': '1 day before',
        'email_notifications': False,
        'push_notifications': True,
        'sms_notifications': False,
        'auto_backup': True,
        'backup_frequency': 'Weekly',
        'backup_retention': '90 days',
        'encryption_enabled': True,
        'auto_logout': True,
        'auto_logout_timeout': 30,
    }

def save_user_settings(settings):
    """Save settings to file"""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

# Load settings at page start
if 'user_settings' not in st.session_state:
    st.session_state.user_settings = load_user_settings()

# ============================================================================
#                                Main Content
# ============================================================================

st.title("Settings")
current_user = get_current_user()

if 'user_settings' not in st.session_state:
    st.session_state.user_settings = load_user_settings()

# Account Section
st.header("Account and Profile")

col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("Your Account")
    with st.container(border=True):
        st.markdown(f"**Username:** `{current_user}`")
        st.markdown(f"**Status:** Active")
        st.markdown(f"**Created:** (Auto-managed)")
        st.markdown(f"**Last Login:** Today")

with col2:
    st.subheader("Account Actions")
    st.markdown("Manage your account security and preferences")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        if st.button("Change Password", key="change_pwd", use_container_width=True):
            st.session_state.show_pwd_modal = True
    
    with col_b:
        if st.button("Two-Factor Auth", key="2fa", use_container_width=True, disabled=True):
            st.info("Coming Soon")
    
st.divider()

st.subheader("Sessions and Devices")

session_data = {
    "Device": ["Current Browser", "Last Device"],
    "Last Active": ["Just now", "2 days ago"],
    "Location": ["Local", "Local"],
    "Action": ["Active", "Log Out"]
}

session_df = pd.DataFrame(session_data)
st.dataframe(session_df, use_container_width=True, hide_index=True)

