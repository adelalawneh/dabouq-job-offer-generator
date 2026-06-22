from pathlib import Path

import streamlit as st

from config import COMPANY

LOGO_MAIN = "assets/logo_group.png"
LOGO_SOURCE = "assets/logo_clean.png"


def inject_css(hide_sidebar=False):
    hide = ""
    if hide_sidebar:
        hide = """
        section[data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        .block-container { max-width: 420px !important; padding-top: 2rem !important; }
        """

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] {{
            font-family: 'IBM Plex Sans Arabic', 'Segoe UI', sans-serif;
        }}
        {hide}
        .block-container {{ padding-top: 1rem; max-width: 980px; }}
        .main {{ background: #f3f4f6; }}
        section[data-testid="stSidebar"] {{
            background: #f3f4f6;
            border-right: 1px solid #e5e7eb;
        }}
        .login-logo [data-testid="stImage"] {{
            display: flex;
            justify-content: center;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 0.35rem;
        }}
        .login-logo [data-testid="stImage"] img {{
            width: 100% !important;
            max-width: 100% !important;
            height: auto !important;
            max-height: 88px;
            object-fit: contain;
            margin: 0 auto;
            border-radius: 10px;
        }}
        div[data-testid="stForm"] {{
            background: #fff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 1.25rem 1.25rem 0.75rem;
            box-shadow: 0 8px 30px rgba(15,33,58,0.06);
        }}
        div[data-testid="stFormSubmitButton"] > button,
        .stButton > button[kind="primary"] {{
            background: #0f213a !important;
            color: #fff !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
        }}
        .remember-wrap {{
            background: #fff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 0.65rem 1rem;
            margin: 0 0 0.85rem;
            box-shadow: 0 4px 18px rgba(15,33,58,0.04);
        }}
        .remember-wrap label {{
            font-size: 0.88rem !important;
            font-weight: 600 !important;
            color: #0f213a !important;
        }}
        .remember-hint {{
            text-align: center;
            color: #64748b;
            font-size: 0.74rem;
            margin: -0.35rem 0 0.9rem;
        }}
        #MainMenu, footer {{ visibility: hidden; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _logo_path():
    if Path(LOGO_MAIN).exists():
        return LOGO_MAIN
    if Path(LOGO_SOURCE).exists():
        return LOGO_SOURCE
    return None


def render_sidebar():
    path = _logo_path()
    if path:
        st.sidebar.image(path, use_container_width=True)
    st.sidebar.caption("DABOUQ GROUP · HR Portal")
    st.sidebar.divider()
    st.sidebar.markdown(f"**{st.session_state.username}**")
    st.sidebar.caption("مسجّل الدخول")


def render_login_page():
    st.markdown('<div class="login-logo">', unsafe_allow_html=True)
    path = _logo_path()
    if path:
        st.image(path, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;color:#64748b;font-size:0.85rem;margin:0.75rem 0 1.25rem;'>"
        f"{COMPANY['name_ar']} — نظام العروض الوظيفية</p>",
        unsafe_allow_html=True,
    )
