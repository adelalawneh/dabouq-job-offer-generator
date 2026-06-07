import streamlit as st


def init_session():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""


def login_form():
    st.title("🔐 DABOUQ HR Portal")
    st.caption("نظام إدارة العروض الوظيفية")

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True, type="primary"):
            if username == st.secrets["APP_USERNAME"] and password == st.secrets["APP_PASSWORD"]:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid username or password")


def require_login():
    init_session()
    if not st.session_state.logged_in:
        login_form()
        st.stop()


def logout_button():
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
