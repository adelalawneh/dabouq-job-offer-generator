import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta, timezone

import extra_streamlit_components as stx
import streamlit as st

from components.ui import render_login_page

REMEMBER_COOKIE = "dabouq_hr_remember"
REMEMBER_PREF_COOKIE = "dabouq_hr_remember_on"
REMEMBER_DAYS = 30
COOKIE_BOOT_RETRIES = 8


def _cookie_manager():
    if "dabouq_hr_cookie_mgr" not in st.session_state:
        st.session_state.dabouq_hr_cookie_mgr = stx.CookieManager(key="dabouq_hr_cookie_mgr")
    return st.session_state.dabouq_hr_cookie_mgr


def _read_cookies(manager) -> dict | None:
    """Compatible with old and new extra-streamlit-components CookieManager APIs."""
    cookies = getattr(manager, "cookies", None)
    if isinstance(cookies, dict):
        return cookies
    getter = getattr(manager, "get_all", None)
    if callable(getter):
        return getter()
    return None


def init_session():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "roles" not in st.session_state:
        st.session_state.roles = []
    _flush_pending_remember_cookie()
    _try_restore_from_cookie()


def _remember_secret() -> bytes:
    secret = (
        st.secrets.get("APP_REMEMBER_SECRET", "")
        or os.environ.get("APP_REMEMBER_SECRET", "")
    )
    if not secret and "users" not in st.secrets and not _users_from_env():
        secret = (
            st.secrets.get("APP_PASSWORD", "")
            or os.environ.get("APP_PASSWORD", "")
        )
    if not secret:
        secret = "dabouq-hr-remember"
    return str(secret).encode()


def _create_remember_token(username: str) -> str:
    payload = {"u": username, "exp": int(time.time()) + REMEMBER_DAYS * 86400}
    data = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()
    sig = hmac.new(_remember_secret(), data.encode(), hashlib.sha256).hexdigest()
    return f"{data}.{sig}"


def _verify_remember_token(token: str) -> str | None:
    try:
        data, sig = token.rsplit(".", 1)
        expected = hmac.new(_remember_secret(), data.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(base64.urlsafe_b64decode(data.encode()))
        if int(payload.get("exp", 0)) < time.time():
            return None
        username = (payload.get("u") or "").strip()
        return username or None
    except Exception:
        return None


def _users_from_env() -> dict:
    raw = os.environ.get("PORTAL_USERS_JSON", "").strip()
    if not raw:
        return {}

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}

    users = {}
    for username, entry in data.items():
        if not isinstance(entry, dict):
            continue
        password = entry.get("password", "")
        if not password:
            continue
        roles = entry.get("roles", ["hr"])
        if isinstance(roles, str):
            roles = [roles]
        users[str(username)] = {"password": str(password), "roles": list(roles)}
    return users


def _get_users():
    if "users" in st.secrets:
        users = {}
        for username, data in st.secrets["users"].items():
            roles = data.get("roles", ["hr"])
            if isinstance(roles, str):
                roles = [roles]
            users[username] = {
                "password": data["password"],
                "roles": list(roles),
            }
        return users

    env_users = _users_from_env()
    if env_users:
        return env_users

    username = os.environ.get("APP_USERNAME") or st.secrets.get("APP_USERNAME", "")
    password = os.environ.get("APP_PASSWORD") or st.secrets.get("APP_PASSWORD", "")
    if username and password:
        return {username: {"password": password, "roles": ["admin", "hr"]}}

    return {}


def _set_logged_in(username: str, roles: list[str]):
    st.session_state.logged_in = True
    st.session_state.username = username
    st.session_state.roles = roles


def _set_remember_cookie(username: str):
    token = _create_remember_token(username)
    expires = datetime.now(timezone.utc) + timedelta(days=REMEMBER_DAYS)
    manager = _cookie_manager()
    manager.set(
        REMEMBER_COOKIE,
        token,
        expires_at=expires,
        max_age=REMEMBER_DAYS * 86400,
        path="/",
        key="dabouq_hr_set_remember",
    )
    manager.set(
        REMEMBER_PREF_COOKIE,
        "1",
        expires_at=expires,
        max_age=REMEMBER_DAYS * 86400,
        path="/",
        key="dabouq_hr_set_remember_pref",
    )


def _flush_pending_remember_cookie():
    username = st.session_state.pop("pending_remember", None)
    if not username or not st.session_state.logged_in:
        return

    if not st.session_state.get("_remember_cookie_written"):
        _set_remember_cookie(username)
        st.session_state._remember_cookie_written = True
        st.rerun()

    st.session_state.pop("_remember_cookie_written", None)


def _clear_remember_cookie():
    manager = _cookie_manager()
    manager.delete(REMEMBER_COOKIE, key="dabouq_hr_del_remember")
    manager.delete(REMEMBER_PREF_COOKIE, key="dabouq_hr_del_remember_pref")


def _try_restore_from_cookie():
    if st.session_state.logged_in:
        return

    manager = _cookie_manager()
    cookies = _read_cookies(manager)

    if cookies is None:
        boots = int(st.session_state.get("_cookie_boot_count", 0))
        if boots < COOKIE_BOOT_RETRIES:
            st.session_state._cookie_boot_count = boots + 1
            st.rerun()
        return

    if not st.session_state.get("_remember_restore_done"):
        boots = int(st.session_state.get("_cookie_boot_count", 0))
        if not cookies.get(REMEMBER_COOKIE) and boots < COOKIE_BOOT_RETRIES:
            st.session_state._cookie_boot_count = boots + 1
            st.rerun()

    if "remember_me" not in st.session_state:
        st.session_state.remember_me = cookies.get(REMEMBER_PREF_COOKIE, "1") == "1"

    if st.session_state.get("_remember_restore_done"):
        return

    st.session_state._remember_restore_done = True
    token = cookies.get(REMEMBER_COOKIE)
    if not token:
        return

    username = _verify_remember_token(token)
    users = _get_users()
    if username and username in users:
        user = users[username]
        roles = user.get("roles", ["hr"])
        if isinstance(roles, str):
            roles = [roles]
        _set_logged_in(username, list(roles))
        st.session_state.remember_me = True
        _set_remember_cookie(username)
        st.rerun()

    _clear_remember_cookie()


def authenticate(username, password):
    users = _get_users()
    user = users.get(username)
    if not user:
        return False, []
    if user.get("password") != password:
        return False, []
    roles = user.get("roles", ["hr"])
    if isinstance(roles, str):
        roles = [roles]
    return True, list(roles)


def login_form():
    render_login_page()

    if "remember_me" not in st.session_state:
        st.session_state.remember_me = True

    st.markdown('<div class="remember-wrap">', unsafe_allow_html=True)
    st.toggle(
        "🔒 تذكرني على هذا الجهاز (30 يوم)",
        key="remember_me",
        help="لن تحتاج تسجيل الدخول في كل مرة على نفس المتصفح",
    )
    st.markdown("</div>", unsafe_allow_html=True)
    if st.session_state.get("remember_me", True):
        st.markdown(
            '<p class="remember-hint">✓ سيتم حفظ جلستك تلقائياً على هذا الجهاز</p>',
            unsafe_allow_html=True,
        )

    with st.form("login_form"):
        st.markdown("**تسجيل الدخول**")
        username = st.text_input("اسم المستخدم", label_visibility="collapsed", placeholder="اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password", label_visibility="collapsed", placeholder="كلمة المرور")
        submitted = st.form_submit_button("دخول →", use_container_width=True, type="primary")

    if submitted:
        if not _get_users():
            st.error("أضف Secrets في إعدادات Streamlit.")
        elif not username.strip() or not password:
            st.error("يرجى إدخال اسم المستخدم وكلمة المرور.")
        else:
            ok, roles = authenticate(username.strip(), password)
            if ok:
                _set_logged_in(username.strip(), roles)
                if st.session_state.get("remember_me", True):
                    st.session_state.pending_remember = username.strip()
                else:
                    _clear_remember_cookie()
                    st.session_state.pop("pending_remember", None)
                    st.session_state.pop("_remember_cookie_written", None)
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة")


def require_login():
    init_session()
    if not st.session_state.logged_in:
        login_form()
        st.stop()


def logout_button():
    if st.sidebar.button("تسجيل خروج", use_container_width=True):
        _clear_remember_cookie()
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.roles = []
        st.session_state.pop("_remember_restore_done", None)
        st.session_state.pop("_cookie_boot_count", None)
        st.session_state.pop("pending_remember", None)
        st.session_state.pop("_remember_cookie_written", None)
        st.rerun()
