import os
import streamlit as st
from streamlit_navigation_bar import st_navbar
from dynamic_programming.database import init_db
import time
from dynamic_programming.pages import home
from pages import contact

# Configure paths FIRST to ensure proper imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)




# Constant configurations
THEME_CONFIG = {
    "primaryColor": "#f07814",
    "backgroundColor": "#FFFFFF",
    "secondaryBackgroundColor": "#F5F5F5",
    "textColor": "#000000",
    "font": "sans serif"
}

NAV_STYLES = {
    "nav": {
        "justify-content": "left",
        "padding-left": "2rem",
        "gap": "4rem",
        "background-color": THEME_CONFIG["primaryColor"],
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
        "transition": "none" 
    },
    "active": {
        "background-color": "transparent",
        "color": "#e6000f",
        "font-weight": "500",
        "transform": "none", 
    }
}

def main():
    """Main application entry point"""
    # Initialize app configuration
    st.set_page_config(
        initial_sidebar_state="collapsed",
        layout="wide",
        page_title="Business Process Optimizer",
        page_icon="⚙️"
    )
    
    # Apply theme configuration
    for key, value in THEME_CONFIG.items():
        st._config.set_option(f"theme.{key}", value)
    
    # Initialize database
    init_db()
    
    # Handle logo
    logo_path = os.path.join(current_dir, "vu_mc_logo_text.svg")
    if not os.path.exists(logo_path):
        st.error(f"⚠️ Missing logo at: {logo_path}")
        logo_path = None
    
    # Setup navigation
    page = st_navbar(
        ["Home", "Contact"],
        options={"show_menu": False, "show_sidebar": False},
        logo_path=logo_path,
        styles=NAV_STYLES
    )
    
    functions = {
        "Home": home.show_home,
        "Contact": contact.show_contact
    }
    go_to = functions.get(page)
    if go_to:
        go_to()

if __name__ == "__main__":
    # Add development reloading
    main()
