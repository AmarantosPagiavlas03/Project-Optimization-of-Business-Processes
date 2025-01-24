import sys
import os
import streamlit as st
from streamlit_navigation_bar import st_navbar
from dynamic_programming.pages import home, contact
from database import init_db

# Configure paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
parent_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(parent_dir, "vu_mc_logo_text.svg")

# Initialize app
st.set_page_config(
    initial_sidebar_state="collapsed",
    layout="wide",
    page_title="Business Process Optimizer",
    page_icon="⚙️"
)

# Set theme config
theme_config = {
    "primaryColor": "#f07814",
    "backgroundColor": "#FFFFFF",
    "secondaryBackgroundColor": "#F5F5F5",
    "textColor": "#000000",
    "font": "sans serif"
}
for key, value in theme_config.items():
    st._config.set_option(f"theme.{key}", value)

init_db()

# Logo handling
if not os.path.exists(logo_path):
    st.error(f"⚠️ Missing logo at: {logo_path}")
    logo_path = None

# Simplified styles focusing on logo spacing
styles = {
    "nav": {
        "justify-content": "left",
        "padding-left": "2rem",
        "gap": "4rem",
        "background-color": theme_config["primaryColor"]
    },
    "img": {
        "width": "320px",  # Increased from 200px
        "min-width": "320px",
        "padding-right": "3rem",
        "margin-left": "-1rem"  # Compensate for SVG spacing
    },
    "span": {
        "color": "white",
        "font-size": "1.1rem",
        "font-weight": "500"
    },
    "active": {
        "background-color": "transparent",  # Remove background
        "color": "black",
        "font-weight": "600",
        "padding": "14px",
        "border-radius": "0",  # Remove rounded corners
        "border-bottom": "3px solid #e6000f"  # Add underline instead
    }
}

# Navigation setup
page = st_navbar(
    ["Home", "Contact"],
    options={"show_menu": False, "show_sidebar": False},
    logo_path=logo_path,
    styles=styles
)

# Add subtle shadow to nav bar
st.markdown("""
<style>
    [data-testid="stNavigationBar"] .active {
        transform: none !important;
        margin: 0 !important;
        min-width: auto !important;
        height: auto !important;
    }
</style>
""", unsafe_allow_html=True)

# Route pages
{"Home": home.show_home, "Contact": contact.show_contact}.get(page)()