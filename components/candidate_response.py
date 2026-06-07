from datetime import datetime

import streamlit as st

from config import OFFER_VALIDITY_DAYS, STATUS_LABELS
from services.database import get_offer_by_token, respond_to_offer
from services.email import send_candidate_confirmation, send_hr_notification
from services.helpers import money


def render_candidate_response(token):
    offer = get_offer_by_token(token)

    if not offer:
        st.error("الرابط غير صالح أو منتهي الصلاحية.")
        st.stop()

    if offer["status"] == "expired":
        st.warning("⏰ انتهت صلاحية هذا العرض.")
        st.stop()

    if offer["status"] in ("accepted", "rejected"):
        status_msg = "✅ تم قبول العرض" if offer["status"] == "accepted" else "❌ تم رفض العرض"
        st.success(status_msg)
        if offer["status"] == "accepted" and offer.get("start_date"):
            st.info(f"تاريخ البدء: {offer['start_date']}")
        st.stop()

    if offer["status"] != "sent":
        st.info("هذا العرض غير متاح للرد حالياً.")
        st.stop()

    st.image("logo.jpeg", width=120)
    st.title("عرض وظيفي — DABOUQ")
    st.caption(f"السيد/ {offer['candidate_name']} المحترم")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("المسمى الوظيفي", offer["job_title"])
        st.metric("القسم", offer["department"])
    with col2:
        st.metric("صافي الراتب", f"{money(offer['net_salary'])} SAR")
        st.metric("موقع العمل", offer["location"])

    if offer.get("expires_at"):
        exp = datetime.fromisoformat(offer["expires_at"]).strftime("%d/%m/%Y")
        st.info(f"⏳ العرض ساري حتى {exp} ({OFFER_VALIDITY_DAYS} أيام من الإرسال)")

    st.markdown("---")

    tab_accept, tab_reject = st.tabs(["✅ قبول العرض", "❌ رفض العرض"])

    with tab_accept:
        start_date = st.date_input("تاريخ بدء العمل المتوقع", min_value=datetime.today())
        if st.button("تأكيد القبول", type="primary", use_container_width=True):
            date_str = start_date.strftime("%d/%m/%Y")
            respond_to_offer(offer["id"], accepted=True, start_date=date_str)
            offer["start_date"] = date_str
            offer["status"] = "accepted"
            try:
                send_candidate_confirmation(offer, accepted=True)
                send_hr_notification(offer, "accepted")
            except Exception as e:
                st.warning(f"تم تسجيل القبول لكن فشل إرسال الإيميل: {e}")
            st.success("✅ تم قبول العرض بنجاح! سيتواصل معكم فريق HR قريباً.")
            st.balloons()
            st.stop()

    with tab_reject:
        reason = st.text_area("سبب الرفض (اختياري)", placeholder="...")
        if st.button("تأكيد الرفض", use_container_width=True):
            respond_to_offer(offer["id"], accepted=False, rejection_reason=reason or None)
            offer["rejection_reason"] = reason
            offer["status"] = "rejected"
            try:
                send_candidate_confirmation(offer, accepted=False)
                send_hr_notification(offer, "rejected")
            except Exception as e:
                st.warning(f"تم تسجيل الرفض لكن فشل إرسال الإيميل: {e}")
            st.info("تم تسجيل رفض العرض. نشكركم على اهتمامكم.")
