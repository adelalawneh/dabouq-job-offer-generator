import streamlit as st
import pandas as pd
from datetime import datetime

from components.auth import init_session, login_form, logout_button
from components.candidate_response import render_candidate_response
from config import STATUS_LABELS
from services.database import delete_offer, get_stats, init_db, list_offers, offer_to_pdf_data
from services.email import respond_url, send_offer_email
from services.helpers import clean_filename, money
from services.pdf import generate_pdf

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

st.title("📄 العروض الوظيفية")
st.caption("متابعة وإرسال العروض الوظيفية")

if st.button("➕ عرض وظيفي جديد", type="primary"):
    st.switch_page("pages/1_➕_New_Offer.py")

stats = get_stats()

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("الإجمالي", stats.get("total", 0))
c2.metric("مُرسل", stats.get("sent", 0))
c3.metric("مقبول", stats.get("accepted", 0))
c4.metric("مرفوض", stats.get("rejected", 0))
c5.metric("مسودة", stats.get("draft", 0))
c6.metric("منتهي", stats.get("expired", 0))

st.markdown("---")

col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
with col_f1:
    status_filter = st.selectbox(
        "الحالة",
        ["all", "draft", "sent", "accepted", "rejected", "expired"],
        format_func=lambda x: "الكل" if x == "all" else STATUS_LABELS.get(x, x),
    )
with col_f2:
    search = st.text_input("بحث", placeholder="اسم، إيميل، وظيفة...")

offers = list_offers(status_filter, search.strip() or None)

if not offers:
    st.info("لا توجد عروض مطابقة.")
    st.stop()

export_rows = []
for o in offers:
    export_rows.append({
        "الاسم": o["candidate_name"],
        "الإيميل": o.get("candidate_email") or "",
        "الوظيفة": o["job_title"],
        "الراتب": money(o["net_salary"]),
        "الحالة": STATUS_LABELS.get(o["status"], o["status"]),
        "تاريخ الإنشاء": o["created_at"][:10],
        "تاريخ الإرسال": (o.get("sent_at") or "")[:10],
        "تاريخ الرد": (o.get("responded_at") or "")[:10],
    })

st.download_button(
    "📥 تصدير Excel/CSV",
    data=pd.DataFrame(export_rows).to_csv(index=False).encode("utf-8-sig"),
    file_name=f"dabouq_offers_{datetime.today().strftime('%Y%m%d')}.csv",
    mime="text/csv",
)

st.markdown("---")

for offer in offers:
    status_label = STATUS_LABELS.get(offer["status"], offer["status"])
    header = f"{status_label}  ·  {offer['candidate_name']}  ·  {offer['job_title']}"

    with st.expander(header, expanded=False):
        d1, d2, d3 = st.columns(3)
        d1.write(f"**الإيميل:** {offer.get('candidate_email') or '—'}")
        d1.write(f"**الجنسية:** {offer.get('candidate_nationality') or '—'}")
        d1.write(f"**رقم الوثيقة:** {offer.get('document_number') or '—'}")
        d2.write(f"**صافي الراتب:** {money(offer['net_salary'])} SAR")
        d2.write(f"**القسم:** {offer['department']}")
        d2.write(f"**الموقع:** {offer['location']}")
        d3.write(f"**أُنشئ:** {offer['created_at'][:16]}")
        d3.write(f"**أُرسل:** {(offer.get('sent_at') or '—')[:16]}")
        d3.write(f"**الرد:** {(offer.get('responded_at') or '—')[:16]}")

        if offer["status"] == "accepted" and offer.get("start_date"):
            st.success(f"تاريخ البدء: {offer['start_date']}")
        if offer["status"] == "rejected" and offer.get("rejection_reason"):
            st.warning(f"سبب الرفض: {offer['rejection_reason']}")

        pdf_data = offer_to_pdf_data(offer)
        pdf_bytes = generate_pdf(pdf_data, offer.get("language", "العربية"))
        lang_suffix = "AR" if offer.get("language") == "العربية" else "EN"
        pdf_name = f"DABOUQ_JOB_OFFER_{clean_filename(offer['candidate_name'])}_{lang_suffix}.pdf"

        btn1, btn2, btn3, btn4 = st.columns(4)

        with btn1:
            st.download_button(
                "📄 تحميل PDF",
                data=pdf_bytes,
                file_name=pdf_name,
                mime="application/pdf",
                key=f"dl_{offer['id']}",
                use_container_width=True,
            )

        with btn2:
            if offer["status"] in ("sent", "accepted", "rejected") and offer.get("candidate_email"):
                if st.button("📧 إعادة إرسال", key=f"resend_{offer['id']}", use_container_width=True):
                    try:
                        send_offer_email(offer, pdf_bytes.getvalue())
                        st.success("تم إعادة الإرسال!")
                    except Exception as e:
                        st.error(str(e))
            else:
                st.caption("—")

        with btn3:
            if offer["status"] == "sent":
                st.code(respond_url(offer["token"]), language=None)
            else:
                st.caption("—")

        with btn4:
            if offer["status"] == "draft":
                confirm_key = f"confirm_delete_{offer['id']}"
                if st.session_state.get(confirm_key):
                    if st.button("✓ تأكيد الحذف", key=f"yes_{offer['id']}", type="primary", use_container_width=True):
                        if delete_offer(offer["id"]):
                            st.session_state.pop(confirm_key, None)
                            st.toast("تم حذف المسودة.")
                            st.rerun()
                        else:
                            st.error("تعذر الحذف.")
                    if st.button("إلغاء", key=f"no_{offer['id']}", use_container_width=True):
                        st.session_state.pop(confirm_key, None)
                        st.rerun()
                elif st.button("🗑️ حذف", key=f"del_{offer['id']}", use_container_width=True):
                    st.session_state[confirm_key] = True
                    st.rerun()
