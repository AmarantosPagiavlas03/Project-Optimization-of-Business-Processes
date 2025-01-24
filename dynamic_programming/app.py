import sys
import os
import streamlit as st
from streamlit_navigation_bar import st_navbar
from database import init_db
import importlib

# --- Path Configuration ---
try:
    # Get the absolute path of the current file's directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add parent directory to Python path (project root)
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Import pages after path configuration
    from dynamic_programming.pages import home, contact
    
    # Configure logo path
    logo_path = os.path.join(current_dir, "vu_mc_logo_text.svg")

except (ImportError, ModuleNotFoundError) as e:
    st.error(f"Critical import error: {str(e)}")
    st.stop()

if os.environ.get("ENVIRONMENT") == "development":
    importlib.reload(home)
    importlib.reload(contact)

# --- App Initialization ---
st.set_page_config(
    initial_sidebar_state="collapsed",
    layout="wide",
    page_title="Business Process Optimizer",
    page_icon="⚙️"
)

# --- Theme Configuration ---
THEME_CONFIG = {
    "primaryColor": "#f07814",
    "backgroundColor": "#FFFFFF",
    "secondaryBackgroundColor": "#F5F5F5",
    "textColor": "#000000",
    "font": "sans serif"
}

for key, value in THEME_CONFIG.items():
    st._config.set_option(f"theme.{key}", value)

# --- Database Initialization ---
init_db()

# --- Logo Validation ---
if not os.path.exists(logo_path):
    st.error(f"⚠️ Missing logo at: {logo_path}")
    logo_path = None

# --- Navigation Styles ---
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
        "margin-left": "-1rem",
        "transition": "opacity 0.3s ease"  # Smooth logo transitions
    },
    "span": {
        "color": "white",
        "font-size": "1.1rem",
        "font-weight": "500",
        "transition": "all 0.2s ease-out"  # Smooth menu transitions
    },
    "active": {
        "color": "#e6000f",
        "font-weight": "600",
        "transform": "translateY(-1px)",  # Subtle lift effect
    }
}

# --- Navigation Setup ---
try:
    page = st_navbar(
        ["Home", "Contact"],
        options={"show_menu": False, "show_sidebar": False},
        logo_path=logo_path,
        styles=NAV_STYLES
    )
except Exception as nav_error:
    st.error(f"Navigation initialization failed: {str(nav_error)}")
    st.stop()

# --- Page Routing ---
PAGE_HANDLERS = {
    "Home": home.show_home,
    "Contact": contact.show_contact
}

try:
    PAGE_HANDLERS.get(page)()
except Exception as page_error:
    st.error(f"Page loading error: {str(page_error)}")
    st.write("Please try refreshing the page or contact support.")