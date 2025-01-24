import sys
import os
import streamlit as st
from streamlit_navigation_bar import st_navbar
from dynamic_programming.pages import home, contact
from database import init_db

# Configure paths FIRST
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
parent_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(parent_dir, "vu_mc_logo_text.svg")

# Initialize app
st.set_page_config(initial_sidebar_state="collapsed", layout="wide")
st._config.set_option("theme.primaryColor", "#E53935")  # Red color
st._config.set_option("theme.backgroundColor", "#FFFFFF")  # White background
st._config.set_option("theme.secondaryBackgroundColor", "#F5F5F5")  # Light gray
st._config.set_option("theme.textColor", "#000000")  # Black text
st._config.set_option("theme.font", "sans serif")
init_db()

# Verify logo exists
if not os.path.exists(logo_path):
    st.error(f"⚠️ Missing logo at: {logo_path}")
    logo_path = None  # Will render without logo

styles = {
    "nav": {
        "background-color": "#f07814",
        "justify-content": "left",
        "padding-left": "20px",
        "gap": "40px",
        "border-bottom": "2px solid #e6000f"  # Add accent line
    },
    "img": {
        "padding-right": "50px",
        "padding-left": "20px",
        "width": "200px",
        "filter": "brightness(0) invert(1)"  # Make black logo white
    },
    "span": {
        "color": "white",
        "padding": "14px",
        "font-size": "18px",
        "transition": "all 0.3s ease"  # Smooth hover effects
    },
    "active": {
        "background-color": "#e6000f",
        "color": "white",  # Better contrast than black
        "font-weight": "500",  # Semi-bold for better visibility
        "padding": "14px",
        "border-radius": "4px"  # Soften edges
    }
}

# Setup navigation
page = st_navbar(
    ["Home", "Contact"],
    options={"show_menu": False, "show_sidebar": False},
    logo_path=logo_path,
    styles=styles 
)
# Route pages
{"Home": home.show_home, "Contact": contact.show_contact}.get(page)()