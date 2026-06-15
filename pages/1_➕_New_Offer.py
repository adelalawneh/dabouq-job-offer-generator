import streamlit as st

from components.auth import init_session, login_form, logout_button
from config import DEFAULT_CONTRACT, JOB_TEMPLATES
from services.database import create_offer, init_db, mark_sent, update_offer
from services.email import send_hr_notification, send_offer_email
from services.helpers import build_offer_payload, clean_filename, footer_defaults as get_footer_defaults, money, salary_split
from services.ocr import extract_document_data
from services.pdf import generate_pdf

init_session()

if not st.session_state.logged_in:
    login_form()
    st.stop()

init_db()
logout_button()

st.title("➕ عرض وظيفي جديد")
st.caption("إنشاء وإرسال عرض وظيفي للمرشّح")

if st.button("← العودة للعروض"):
    st.switch_page("app.py")

if "ocr_data" not in st.session_state:
    st.session_state.ocr_data = {"full_name": "", "nationality": "", "document_number": ""}

template_names = ["— اختر قالب —"] + list(JOB_TEMPLATES.keys())
selected_template = st.selectbox("📋 قالب وظيفة جاهز", template_names)

defaults = {}
if selected_template != "— اختر قالب —":
    defaults = {**DEFAULT_CONTRACT, **JOB_TEMPLATES[selected_template]}
else:
    defaults = {
        **DEFAULT_CONTRACT,
        "job_title": "مندوب مبيعات",
        "department": "المبيعات",
        "location": "منطقة الرياض",
        "total_salary": 3500.0,
    }

left, right = st.columns(2)

with left:
    st.subheader("1. وثيقة المرشّح")

    uploaded_file = st.file_uploader("رفع جواز / إقامة / هوية", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        if st.button("🤖 استخراج البيانات بالذكاء الاصطناعي", use_container_width=True):
            with st.spinner("جاري قراءة الوثيقة..."):
                try:
                    result = extract_document_data(uploaded_file, st.secrets["GEMINI_API_KEY"])
                    st.session_state.ocr_data = result
                    st.success("تم استخراج البيانات — راجعها قبل الإرسال")
                except Exception as e:
                    st.error(str(e))

    st.markdown("---")
    st.subheader("2. بيانات المرشّح")

    name = st.text_input("الاسم الكامل *", value=st.session_state.ocr_data.get("full_name", ""))
    email = st.text_input("البريد الإلكتروني *", placeholder="candidate@email.com")
    nationality = st.text_input("الجنسية", value=st.session_state.ocr_data.get("nationality", ""))
    doc_number = st.text_input("رقم الوثيقة", value=st.session_state.ocr_data.get("document_number", ""))

    st.markdown("---")
    st.subheader("3. تفاصيل الوظيفة")

    job_title = st.text_input("المسمى الوظيفي", value=defaults.get("job_title", ""))
    department = st.text_input("القسم", value=defaults.get("department", ""))
    location = st.text_input("موقع العمل", value=defaults.get("location", ""))

with right:
    st.subheader("4. تفاصيل العقد")

    contract_type = st.text_input("نوع العقد", value=defaults.get("contract_type", DEFAULT_CONTRACT["contract_type"]))
    contract_duration = st.text_input("مدة العقد", value=defaults.get("contract_duration", DEFAULT_CONTRACT["contract_duration"]))
    work_days = st.text_input("أيام العمل", value=defaults.get("work_days", DEFAULT_CONTRACT["work_days"]))
    probation = st.text_input("فترة التجربة", value=defaults.get("probation", DEFAULT_CONTRACT["probation"]))
    annual_leave = st.text_input("الإجازة السنوية", value=defaults.get("annual_leave", DEFAULT_CONTRACT["annual_leave"]))

    st.markdown("---")
    st.subheader("5. تفاصيل الراتب")

    total_salary = st.number_input("إجمالي الراتب", min_value=0.0, value=float(defaults.get("total_salary", 3500.0)), step=100.0)
    insurance = st.number_input("خصم التأمينات الاجتماعية", min_value=0.0, value=0.0, step=50.0)

    basic, housing, transport = salary_split(total_salary)
    net_salary = round(total_salary - insurance)

    st.info(
        f"أساسي: {money(basic)} SAR  \n"
        f"سكن: {money(housing)} SAR  \n"
        f"نقل: {money(transport)} SAR  \n"
        f"**صافي: {money(net_salary)} SAR**"
    )

    language = st.radio("لغة العرض", ["العربية", "English"], horizontal=True)

footer_defaults = get_footer_defaults(language)
with st.expander("📝 نصوص نهاية العرض (قابلة للتعديل)", expanded=False):
    footer_salary_review = st.text_area(
        "ملاحظة مراجعة الراتب",
        value=footer_defaults["salary_review"],
        height=68,
    )
    footer_validity = st.text_area(
        "صلاحية العرض",
        value=footer_defaults["validity"],
        height=56,
    )
    footer_acceptance = st.text_area(
        "سطر الموافقة",
        value=footer_defaults["acceptance"],
        height=56,
    )
    footer_rejection = st.text_area(
        "سطر الرفض",
        value=footer_defaults["rejection"],
        height=56,
    )


def collect_form():
    return {
        "candidate_name": name.strip(),
        "candidate_email": email.strip(),
        "candidate_nationality": nationality.strip(),
        "document_number": doc_number.strip(),
        "job_title": job_title.strip(),
        "department": department.strip(),
        "location": location.strip(),
        "contract_type": contract_type.strip(),
        "contract_duration": contract_duration.strip(),
        "work_days": work_days.strip(),
        "probation": probation.strip(),
        "annual_leave": annual_leave.strip(),
        "total_salary": total_salary,
        "insurance": insurance,
        "language": language,
        "created_by": st.session_state.get("username", "hr"),
        "footer_salary_review": footer_salary_review.strip(),
        "footer_validity": footer_validity.strip(),
        "footer_acceptance": footer_acceptance.strip(),
        "footer_rejection": footer_rejection.strip(),
    }


def validate(required_email=False):
    if not name.strip():
        st.error("اسم المرشّح مطلوب.")
        return False
    if required_email and not email.strip():
        st.error("البريد الإلكتروني مطلوب للإرسال.")
        return False
    if required_email and "@" not in email:
        st.error("البريد الإلكتروني غير صالح.")
        return False
    return True


def save_fields(form):
    payload = build_offer_payload(form)
    return {
        **form,
        "basic": payload["basic"],
        "housing": payload["housing"],
        "transport": payload["transport"],
        "net_salary": payload["net_salary"],
    }


st.markdown("---")

btn1, btn2, btn3 = st.columns(3)

with btn1:
    if st.button("💾 حفظ كمسودة", use_container_width=True):
        if validate():
            offer_id = create_offer(save_fields(collect_form()), status="draft")
            st.success(f"تم حفظ المسودة — رقم: {offer_id[:8]}...")

with btn2:
    if st.button("📄 معاينة PDF", use_container_width=True):
        if validate():
            form = collect_form()
            payload = build_offer_payload(form)
            pdf = generate_pdf(payload, language)
            filename = f"DABOUQ_JOB_OFFER_{clean_filename(name)}_{'AR' if language == 'العربية' else 'EN'}.pdf"
            st.download_button("⬇️ تحميل PDF", data=pdf, file_name=filename, mime="application/pdf", use_container_width=True)

with btn3:
    if st.button("📧 إرسال العرض", type="primary", use_container_width=True):
        if validate(required_email=True):
            form = collect_form()
            payload = build_offer_payload(form)
            db_fields = save_fields(form)

            offer_id = create_offer(db_fields, status="draft")
            pdf = generate_pdf(payload, language)

            try:
                offer = {**db_fields, "id": offer_id, "token": offer_id}
                send_offer_email(offer, pdf.getvalue())
                mark_sent(offer_id)
                send_hr_notification(offer, "sent")
                st.success("✅ تم إرسال العرض بنجاح!")
                st.info("يمكنك متابعة حالة العرض من صفحة العروض.")
            except Exception as e:
                update_offer(offer_id, {}, status="draft")
                st.error(f"فشل الإرسال: {e}")
                st.warning("تأكد من إعداد SMTP في secrets.toml")
