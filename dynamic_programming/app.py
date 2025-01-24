import sys
import os
import streamlit as st
from streamlit_navigation_bar import st_navbar
from pages import home, contact
from pages.utilities.database import init_db

# Configure paths FIRST
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
parent_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(parent_dir, "vu_mc_logo_text.svg")

# Initialize app
st.set_page_config(initial_sidebar_state="collapsed", layout="wide")
init_db()

# Verify logo exists
if not os.path.exists(logo_path):
    st.error(f"⚠️ Missing logo at: {logo_path}")
    logo_path = None  # Will render without logo

# Setup navigation
page = st_navbar(
    ["Home", "Contact"],
    options={"show_menu": False, "show_sidebar": False},
    logo_path=logo_path
)

# Route pages
{"Home": home.show_home, "Contact": contact.show_contact}.get(page)()