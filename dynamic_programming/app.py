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
        transform: translateZ(0);  /* GPU acceleration */
        will-change: transform;
        transition: 
            transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94),
            color 0.3s ease;
    }

    [data-testid="stNavigationBar"] .active {
        transform: translateY(-2px);
        animation: active-pulse 1.5s ease-in-out infinite;
    }

    [data-testid="stNavigationBar"] span:hover {
        transform: translateY(-1px);
    }

    @keyframes active-pulse {
        0%, 100% { transform: translateY(-2px); }
        50% { transform: translateY(-3px); }
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
        animation: underline-grow 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    }

    @keyframes underline-grow {
        from { transform: scaleX(0); }
        to { transform: scaleX(1); }
    }
</style>
""", unsafe_allow_html=True)

# Route pages
{"Home": home.show_home, "Contact": contact.show_contact}.get(page)()