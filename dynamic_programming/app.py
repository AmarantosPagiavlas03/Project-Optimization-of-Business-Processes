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


st.set_page_config(
    initial_sidebar_state="collapsed",
    layout="centered",
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


# Verify logo exists
if not os.path.exists(logo_path):
    st.error(f"⚠️ Missing logo at: {logo_path}")
    logo_path = None  # Will render without logo

styles = {
    "nav": {
        "justify-content": "left",
        "padding-left": "2rem",
        "gap": "4rem",
        "background-color": theme_config["primaryColor"],
    },
    "img": {
        "width": "200px",
        "max-width": "100%",
        "min-width": "120px",
        "padding-right": "3rem",
        "margin-left": "-1rem"
    },
    "span": {
        "color": "white",
        "font-size": "1.1rem",
        "font-weight": "500",
        "position": "relative",
        "transition": "none"  # Disable default transitions
    },
    "active": {
        "background-color": "transparent",
        "color": "#e6000f",
        "font-weight": "800",
        "transform": "none", 
    }
}
# Setup navigation
page = st_navbar(
    ["Home", "Contact"],
    options={"show_menu": False, "show_sidebar": False},
    logo_path=logo_path
)

# Route pages
{"Home": home.show_home, "Contact": contact.show_contact}.get(page)()