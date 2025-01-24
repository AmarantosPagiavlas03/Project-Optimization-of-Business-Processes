import streamlit as st
from streamlit_navigation_bar import st_navbar


page = st_navbar(
    pages=["Home", "Library", "Tutorials", "Development", "Download"],
    options={"use_padding": False, "show_sidebar": True},
)
st.write(page)