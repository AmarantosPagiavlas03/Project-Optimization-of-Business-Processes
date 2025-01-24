import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_extras.switch_page_button import switch_page

st.set_page_config(page_title="Analytics", layout="wide")
def navigation_bar():
    with st.container():
        st.markdown(
            """
            <style>
                .nav-logo {
                    display: flex;
                    align-items: center;
                    margin-bottom: 10px;
                }
                .nav-logo img {
                    width: 200px;
                    height: 33px;
                    margin-right: 20px;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="nav-logo">
                <img src="https://raw.githubusercontent.com/AmarantosPagiavlas03/Project-Optimization-of-Business-Processes/main/dynamic_programming/vu_mc_logo.png" alt="Logo">
            </div>
            """,
            unsafe_allow_html=True,
        )
        selected = option_menu(
            menu_title=None,
            options=["Home", "Upload", "Analytics", 'Settings', 'Contact'],
            icons=['house', 'cloud-upload', "graph-up-arrow", 'gear', 'phone'],
            menu_icon="cast",
            orientation="horizontal",
            styles={
                "nav-link": {
                    "text-align": "left",
                    "--hover-color": "#eee",
                }
            }
        )
        if selected == "Home":
            switch_page("Hospital Scheduler")
        if selected == "Analytics":
            switch_page("Analytics")
        if selected == "Contact":
            switch_page("Contact")
navigation_bar()
st.title("Analytics")
