import streamlit as st


def show_contact():
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