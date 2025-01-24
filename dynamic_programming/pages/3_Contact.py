import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_extras.switch_page_button import switch_page

st.set_page_config(page_title="Contact", layout="wide")
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
            switch_page("Home")
        if selected == "Analytics":
            switch_page("Analytics")
        if selected == "Contact":
            switch_page("Contact")
navigation_bar()
st.title("Contact Us")

# Add a description or introductory text
st.write("We'd love to hear from you! Please use the form below to get in touch with us.")

# Contact form
with st.form("contact_form"):
    # Name input
    name = st.text_input("Name", placeholder="Enter your name")
    # Email input
    email = st.text_input("Email", placeholder="Enter your email address")
    # Message input
    message = st.text_area("Message", placeholder="Write your message here", height=150)
    # Submit button
    submitted = st.form_submit_button("Submit")

    # Handle form submission
    if submitted:
        if name and email and message:
            st.success("Thank you for your message! We'll get back to you shortly.")
            # You can add email sending functionality here, e.g., using an API like SendGrid
        else:
            st.error("Please fill in all fields before submitting.")

# Additional contact information
st.write("### Other Ways to Reach Us")
st.write("📧 Email: support@vuamsterdamscheduling.com")
st.write("📍 Address: De Boelelaan 1105, 1081 HV Amsterdam, North Holland, Netherlands")
