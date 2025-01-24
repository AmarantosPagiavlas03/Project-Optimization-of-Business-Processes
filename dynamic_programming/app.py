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

init_db()

# Logo handling
if not os.path.exists(logo_path):
    st.error(f"⚠️ Missing logo at: {logo_path}")
    logo_path = None

styles = {
    "nav": {
        "justify-content": "left",
        "padding-left": "2rem",
        "gap": "4rem",
        "background-color": theme_config["primaryColor"],
        "position": "relative"  # Add positioning context
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
        "position": "relative",  # Needed for pseudo-element
        "transition": "all 0.2s ease"  # Smooth transitions
    },
    "active": {
        "background-color": "transparent",
        "color": "#e6000f",
        "font-weight": "800",
        "transform": "translateY(-2px)"  # Vertical lift instead of scale
    },
    "hover": {
        "background-color": "transparent",
        "color": "#e6000f",
        "transform": "translateY(-1px)"
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
    [data-testid="stNavigationBar"] span {
        display: inline-block;
        transition: all 0.2s ease;
    }
    
    [data-testid="stNavigationBar"] .active::after {
        content: "";
        display: block;
        width: 100%;
        height: 2px;
        background: #e6000f;
        position: absolute;
        bottom: -4px;
        left: 0;
        transform: scaleX(1.1);
        transform-origin: center;
    }
    
    [data-testid="stNavigationBar"] span:hover {
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# Route pages
{"Home": home.show_home, "Contact": contact.show_contact}.get(page)()