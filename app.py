import streamlit as st

from components.auth import init_session, login_form, logout_button, require_login
from components.candidate_response import render_candidate_response
from services.database import get_stats, init_db

st.set_page_config(
    page_title="DABOUQ HR Portal",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

token = st.query_params.get("token")
if token:
    render_candidate_response(token)
    st.stop()

init_session()

if not st.session_state.logged_in:
    login_form()
    st.stop()

logout_button()

st.title("🏠 DABOUQ HR Portal")
st.caption("نظام متكامل لإدارة العروض الوظيفية")

stats = get_stats()

st.markdown("### نظرة سريعة")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("📋 إجمالي العروض", stats.get("total", 0))
c2.metric("📤 بانتظار الرد", stats.get("sent", 0))
c3.metric("✅ مقبولة", stats.get("accepted", 0))
c4.metric("❌ مرفوضة", stats.get("rejected", 0))
c5.metric("📝 مسودات", stats.get("draft", 0))

st.markdown("---")

st.markdown("""
### كيف يعمل النظام؟

1. **عرض جديد** — ارفع وثيقة المرشّح، راجع البيانات، وأرسل العرض بالإيميل
2. **المرشّح** — يستلم إيميلاً مع PDF ورابط قبول/رفض
3. **لوحة التحكم** — تتابع كل العروض، تحمّل PDF، وتصدّر التقارير

> استخدم القائمة الجانبية للتنقل بين الصفحات.
""")

if stats.get("sent", 0) > 0:
    st.warning(f"⚠️ لديك {stats['sent']} عرض/عروض بانتظار رد المرشّح.")
