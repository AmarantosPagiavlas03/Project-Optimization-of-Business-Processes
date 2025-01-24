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
        z-index: 1;
    }

    [data-testid="stNavigationBar"] .active::before {
        content: "";
        position: absolute;
        top: 50%;
        left: 50%;
        width: 110%;
        height: 140%;
        background: rgba(230, 0, 15, 0.1);
        transform: translate(-50%, -50%) scale(0);
        border-radius: 8px;
        transition: transform 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.28);
        z-index: -1;
    }

    [data-testid="stNavigationBar"] .active:hover::before,
    [data-testid="stNavigationBar"] .active:active::before {
        transform: translate(-50%, -50%) scale(1);
    }

    [data-testid="stNavigationBar"] span {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 14px 16px;
    }
</style>
""", unsafe_allow_html=True)

# Route pages
{"Home": home.show_home, "Contact": contact.show_contact}.get(page)()