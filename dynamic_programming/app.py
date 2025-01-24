# Add this FIRST in app.py
import sys
import os

# Get the path to the project root (parent of dynamic_programming folder)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)  # Insert at start of path list

# Now import other modules
import streamlit as st
from streamlit_navigation_bar import st_navbar
from dynamic_programming.pages import home, contact  # Use absolute import
from database import init_db

# Add this at the top of app.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
st.set_page_config(initial_sidebar_state="collapsed")
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
    "Home": pg.show_home,
    "Contact": pg.show_contact,
}
go_to = functions.get(page)
if go_to:
    go_to()