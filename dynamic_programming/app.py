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
logo_path = os.path.join(parent_dir, "vu_mc_logo.svg")

# Initialize app
st.set_page_config(initial_sidebar_state="collapsed", layout="wide")
init_db()

# Verify logo exists
if not os.path.exists(logo_path):
    st.error(f"⚠️ Missing logo at: {logo_path}")
    logo_path = None  # Will render without logo
styles = {
    "nav": {
        "background-color": "royalblue",
        "justify-content": "left",
        "padding-left": "30px",
        "gap": "80px",  # Increased space between logo and menu items
    },
    "img": {
        "width": "400px",  # Match SVG's aspect ratio (551x91 = ~6:1)
        "min-width": "400px",  # Prevent compression
        "padding-right": "100px",  # Right margin for logo
        "object-fit": "contain",  # Maintain aspect ratio
        "margin-left": "-20px",  # Compensate for SVG's internal padding
    },
    "span": {
        "color": "white",
        "padding": "18px",
        "font-size": "20px",
        "letter-spacing": "1px",  # Improve menu item readability
    },
    "active": {
        "background-color": "white",
        "color": "var(--text-color)",
        "padding": "18px",
    }
}
st.markdown("""
<style>
    [data-testid="stNavigationBar"] {
        height: 85px !important;  # Match logo height
    }
    [data-testid="stNavigationBar"] img {
        margin-top: -5px;  # Vertical centering adjustment
    }
</style>
""", unsafe_allow_html=True)
# Setup navigation
page = st_navbar(
    ["Home", "Contact"],
    options={"show_menu": False, "show_sidebar": False},
    logo_path=logo_path,
    styles=styles,
)

# Route pages
{"Home": home.show_home, "Contact": contact.show_contact}.get(page)()