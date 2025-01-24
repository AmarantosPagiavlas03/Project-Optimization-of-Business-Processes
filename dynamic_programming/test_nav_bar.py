import os

import streamlit as st
from streamlit_navigation_bar import st_navbar

import pages as pg


st.set_page_config(initial_sidebar_state="collapsed")

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