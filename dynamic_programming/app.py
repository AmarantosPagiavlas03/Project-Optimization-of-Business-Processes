# In app.py (corrected version)
import sys
import os

# Add project root to Python path FIRST
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Now import modules
import streamlit as st
from streamlit_navigation_bar import st_navbar
from dynamic_programming.pages import home, contact  # Direct import
from database import init_db

# Add this at the top of app.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
st.set_page_config(initial_sidebar_state="collapsed", layout="wide")
init_db()
pages = ["Home", "Contact"]

options = {
    "show_menu": False,
    "show_sidebar": False,
}

page = st_navbar(
    pages,
    options=options,
)

functions = {
    "Home": home.show_home,
    "Contact": contact.show_contact
}

go_to = functions.get(page)
if go_to:
    go_to()