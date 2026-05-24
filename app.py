import streamlit as st
import google.generativeai as genai
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from bidi.algorithm import get_display
import arabic_reshaper
from num2words import num2words
import json
import io
import re
from datetime import datetime


st.set_page_config(
    page_title="DABOUQ Job Offer Generator",
    layout="wide"
)

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])


# =========================
# LOGIN
# =========================
def login():
    st.title("🔐 DABOUQ HR Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login", use_container_width=True):
        if username == st.secrets["APP_USERNAME"] and password == st.secrets["APP_PASSWORD"]:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid username or password")


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
    st.stop()


# =========================
# HELPERS
# =========================
def ar_text(text):
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)


def clean_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "", name.strip())
    name = name.replace(" ", "_")
    return name if name else "candidate"


def money(value):
    return f"{int(round(value)):,}"


def salary_split(total):
    basic = round(total * 0.645)
    housing = round(total * 0.226)
    transport = round(total - basic - housing)
    return basic, housing, transport


def salary_ar_words(amount):
    try:
        return f"{num2words(int(round(amount)), lang='ar')} ريال سعودي لا غير"
    except Exception:
        return ""


def salary_en_words(amount):
    try:
        return f"{num2words(int(round(amount)), lang='en').title()} Saudi Riyals Only"
    except Exception:
        return ""


def extract_json(text):
    text = text.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return {}


def register_font():
    try:
        pdfmetrics.registerFont(TTFont("DabouqFont", "IBMPlexSansArabic-Regular.ttf"))
        return "DabouqFont"
    except Exception as e:
        print("Font error:", e)
        return "Helvetica"


def draw_ar(c, x, y, text, font, size=10):
    c.setFont(font, size)
    c.drawRightString(x, y, ar_text(text))


def draw_section_title(c, x, y, title, font, page_width):
    c.setFillColorRGB(0.06, 0.13, 0.23)
    c.roundRect(x, y - 0.25 * cm, page_width - 4 * cm, 0.65 * cm, 0.12 * cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    draw_ar(c, page_width - 2.3 * cm, y - 0.03 * cm, title, font, 10.5)
    c.setFillColor(colors.black)


def draw_label_value_ar(c, label, value, x, y, font):
    c.setFont(font, 10)
    draw_ar(c, x, y, f"{label}: {value}", font, 10)


def draw_salary_table_ar(c, data, x, y, font, width):
    rows = [
        ("الراتب الأساسي", f"{money(data['basic'])} ريال سعودي"),
        ("بدل السكن", f"{money(data['housing'])} ريال سعودي"),
        ("بدل النقل", f"{money(data['transport'])} ريال سعودي"),
        ("إجمالي الراتب", f"{money(data['total_salary'])} ريال سعودي"),
        ("خصم التأمينات الاجتماعية", f"{money(data['insurance'])} ريال سعودي"),
        ("صافي الراتب", f"{money(data['net_salary'])} ريال سعودي"),
    ]

    row_h = 0.72 * cm
    table_w = width - 4 * cm

    c.setStrokeColorRGB(0.80, 0.83, 0.88)
    c.setLineWidth(0.7)

    for i, (label, value) in enumerate(rows):
        yy = y - i * row_h
        if i == len(rows) - 1:
            c.setFillColorRGB(0.94, 0.96, 0.98)
            c.rect(x, yy - row_h + 0.12 * cm, table_w, row_h, fill=1, stroke=0)
            c.setFillColor(colors.black)

        c.rect(x, yy - row_h + 0.12 * cm, table_w, row_h, fill=0, stroke=1)
        draw_ar(c, width - 2.4 * cm, yy - 0.38 * cm, label, font, 9.5)
        draw_ar(c, width - 10.2 * cm, yy - 0.38 * cm, value, font, 9.5)

    return y - len(rows) * row_h - 0.2 * cm


# =========================
# OCR
# =========================
def extract_document_data(uploaded_file):
    image = Image.open(uploaded_file)
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = """
    Analyze this Passport / ID / IQAMA.

    Extract:
    - full_name
    - nationality
    - document_number

    Return STRICT JSON ONLY.

    {
      "full_name": "",
      "nationality": "",
      "document_number": ""
    }
    """

    response = model.generate_content([prompt, image])
    return extract_json(response.text)


# =========================
# PDF
# =========================
def generate_pdf(data, language):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    font = register_font()

    c.setTitle("DABOUQ Job Offer")

    navy = (0.06, 0.13, 0.23)

    # Background header line
    c.setStrokeColorRGB(*navy)
    c.setLineWidth(2)
    c.line(2 * cm, height - 4.15 * cm, width - 2 * cm, height - 4.15 * cm)

    # Logo
    try:
        logo = ImageReader("logo.jpeg")
        c.drawImage(
            logo,
            2 * cm,
            height - 3.65 * cm,
            width=3.2 * cm,
            height=2.8 * cm,
            preserveAspectRatio=True,
            mask="auto"
        )
    except Exception:
        pass

    if language == "العربية":
        # Company Info
        company_lines = [
            "شركة دابوق التجارية شركة شخص واحد",
            "رقم المنشأة: 7013895862",
            "س.ت: 3550102093",
            "هاتف: 0556018251",
            "الرقم الضريبي: 311280392800003"
        ]

        y = height - 1.55 * cm
        c.setFillColorRGB(*navy)
        for line in company_lines:
            draw_ar(c, width - 2 * cm, y, line, font, 9.2)
            y -= 0.42 * cm

        c.setFillColor(colors.black)

        # Title box
        c.setStrokeColorRGB(*navy)
        c.setLineWidth(1)
        c.roundRect(width / 2 - 2.7 * cm, height - 5.05 * cm, 5.4 * cm, 0.85 * cm, 0.18 * cm, fill=0, stroke=1)
        c.setFillColorRGB(*navy)
        c.setFont(font, 15)
        c.drawCentredString(width / 2, height - 4.78 * cm, ar_text("عرض وظيفي"))
        c.setFillColor(colors.black)

        y = height - 5.9 * cm

        draw_ar(c, width - 2 * cm, y, f"التاريخ: {data['date']}", font, 10)
        y -= 0.62 * cm
        draw_ar(c, width - 2 * cm, y, f"إلى السيد: {data['name']} المحترم،،،", font, 10)
        y -= 0.62 * cm
        draw_ar(c, width - 2 * cm, y, f"رقم الإقامة / الوثيقة: {data['doc_number']}", font, 10)

        y -= 0.75 * cm

        # Job Section
        draw_section_title(c, 2 * cm, y, "تفاصيل الوظيفة", font, width)
        y -= 0.9 * cm
        draw_label_value_ar(c, "المسمى الوظيفي", data["job_title"], width - 2.3 * cm, y, font)
        y -= 0.5 * cm
        draw_label_value_ar(c, "القسم", data["department"], width - 2.3 * cm, y, font)
        y -= 0.5 * cm
        draw_label_value_ar(c, "موقع العمل", data["location"], width - 2.3 * cm, y, font)

        y -= 0.75 * cm

        # Contract Section
        draw_section_title(c, 2 * cm, y, "تفاصيل العقد", font, width)
        y -= 0.9 * cm
        draw_label_value_ar(c, "نوع العقد", data["contract_type"], width - 2.3 * cm, y, font)
        y -= 0.5 * cm
        draw_label_value_ar(c, "مدة العقد", data["contract_duration"], width - 2.3 * cm, y, font)
        y -= 0.5 * cm
        draw_label_value_ar(c, "أيام العمل", data["work_days"], width - 2.3 * cm, y, font)
        y -= 0.5 * cm
        draw_label_value_ar(c, "فترة التجربة", data["probation"], width - 2.3 * cm, y, font)
        y -= 0.5 * cm
        draw_label_value_ar(c, "الإجازة السنوية", data["annual_leave"], width - 2.3 * cm, y, font)

        y -= 0.75 * cm

        # Salary Section
        draw_section_title(c, 2 * cm, y, "تفاصيل الراتب الشهري", font, width)
        y -= 0.85 * cm
        y = draw_salary_table_ar(c, data, 2 * cm, y, font, width)

        draw_ar(c, width - 2.3 * cm, y, f"صافي الراتب كتابة: فقط {data['salary_words_ar']}", font, 9.4)
        y -= 0.75 * cm

        # Benefits
        draw_section_title(c, 2 * cm, y, "المزايا", font, width)
        y -= 0.9 * cm
        draw_label_value_ar(c, "التأمين الطبي", "يُوفر وفقًا لمتطلبات الوظيفة", width - 2.3 * cm, y, font)
        y -= 0.5 * cm
        draw_label_value_ar(c, "مزايا أخرى", "حسب السياسات الداخلية للشركة", width - 2.3 * cm, y, font)

        y -= 0.65 * cm

        draw_ar(c, width - 2.3 * cm, y, "سيتم مراجعة الراتب بعد مرور ثلاثة (3) أشهر من تاريخ مباشرة العمل، وذلك لغرض النظر في إمكانية زيادة الراتب وتثبيت الموظف بناءً على تقييم الأداء.", font, 8.7)
        y -= 0.55 * cm
        draw_ar(c, width - 2.3 * cm, y, "ويُعتبر هذا العرض ساري المفعول لمدة عشرة (10) أيام فقط من تاريخ صدوره.", font, 8.7)

        # Footer acceptance
        c.setStrokeColorRGB(*navy)
        c.setLineWidth(1)
        c.line(2 * cm, 3.15 * cm, width - 2 * cm, 3.15 * cm)

        draw_ar(c, width - 2.2 * cm, 2.6 * cm, "أوافق على ما ورد أعلاه، وأقر بأن تاريخ بدء عملي سيكون اعتبارًا من:      /      / ٢٠٢٦", font, 8.7)
        draw_ar(c, width - 2.2 * cm, 2.1 * cm, "لا أوافق على العرض المذكور أعلاه للأسباب التالية: ........................................................", font, 8.7)

        draw_ar(c, width - 2.2 * cm, 1.35 * cm, "إدارة الموارد البشرية", font, 9.5)

    else:
        c.setFont(font, 10)
        c.setFillColorRGB(*navy)
        lines = [
            "Dabouq Commercial Company One Person Co.",
            "Establishment No: 7013895862",
            "C.R: 3550102093",
            "Phone: 0556018251",
            "Tax ID: 311280392800003"
        ]
        y = height - 1.55 * cm
        for line in lines:
            c.drawString(2 * cm, y, line)
            y -= 0.42 * cm

        c.setFillColorRGB(*navy)
        c.roundRect(width / 2 - 2.7 * cm, height - 5.05 * cm, 5.4 * cm, 0.85 * cm, 0.18 * cm, fill=0, stroke=1)
        c.setFont(font, 15)
        c.drawCentredString(width / 2, height - 4.78 * cm, "JOB OFFER")
        c.setFillColor(colors.black)

        y = height - 5.9 * cm
        rows = [
            ("Date", data["date_en"]),
            ("To", data["name"]),
            ("Document No.", data["doc_number"]),
            ("Job Title", data["job_title"]),
            ("Department", data["department"]),
            ("Work Location", data["location"]),
            ("Contract Type", "Fixed Term"),
            ("Duration", "One Year"),
            ("Basic Salary", f"{money(data['basic'])} SAR"),
            ("Housing Allowance", f"{money(data['housing'])} SAR"),
            ("Transport Allowance", f"{money(data['transport'])} SAR"),
            ("Net Salary", f"{money(data['net_salary'])} SAR"),
            ("Salary in Words", data["salary_words_en"]),
        ]

        c.setFont(font, 10)
        for label, value in rows:
            c.drawString(2 * cm, y, f"{label}: {value}")
            y -= 0.58 * cm

        c.drawString(2 * cm, y - 0.3 * cm, "Human Resources Department")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


# =========================
# UI
# =========================
st.title("📄 DABOUQ Job Offer Generator")
st.caption("Internal HR tool for generating official job offers.")

if "ocr_data" not in st.session_state:
    st.session_state.ocr_data = {
        "full_name": "",
        "nationality": "",
        "document_number": ""
    }

left, right = st.columns(2)

with left:
    st.subheader("1. Candidate Document")

    uploaded_file = st.file_uploader("Upload Passport / IQAMA / ID", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        if st.button("Extract Data with AI", use_container_width=True):
            with st.spinner("Reading document..."):
                try:
                    result = extract_document_data(uploaded_file)
                    st.session_state.ocr_data = result
                    st.success("Data extracted successfully. Please review it.")
                except Exception as e:
                    st.error(e)

    st.markdown("---")

    st.subheader("2. Candidate Details")

    name = st.text_input("Full Name", value=st.session_state.ocr_data.get("full_name", ""))
    nationality = st.text_input("Nationality", value=st.session_state.ocr_data.get("nationality", ""))
    doc_number = st.text_input("Document Number", value=st.session_state.ocr_data.get("document_number", ""))

    st.markdown("---")

    st.subheader("3. Job Details")

    job_title = st.text_input("Job Title", value="مندوب مبيعات")
    department = st.text_input("Department", value="المبيعات")
    location = st.text_input("Work Location", value="منطقة الرياض")

with right:
    st.subheader("4. Contract Details")

    contract_type = st.text_input("Contract Type", value="محدد المدة (فردي)")
    contract_duration = st.text_input("Contract Duration", value="سنة")
    work_days = st.text_input("Work Days", value="٦ أيام في الأسبوع - 9 ساعات يوميًا تتضمن ساعة راحة")
    probation = st.text_input("Probation Period", value="٩٠ يومًا")
    annual_leave = st.text_input("Annual Leave", value="٢١ يومًا في السنة")

    st.markdown("---")

    st.subheader("5. Salary Details")

    total_salary = st.number_input("Total Salary", min_value=0.0, value=3500.0, step=100.0)
    insurance = st.number_input("Social Insurance Deduction", min_value=0.0, value=0.0, step=50.0)

    basic, housing, transport = salary_split(total_salary)
    net_salary = round(total_salary - insurance)

    st.info(
        f"""
        Basic Salary: {money(basic)} SAR  
        Housing Allowance: {money(housing)} SAR  
        Transport Allowance: {money(transport)} SAR  
        Net Salary: {money(net_salary)} SAR
        """
    )

    language = st.radio("PDF Language", ["العربية", "English"], horizontal=True)

    today = datetime.today()

    data = {
        "name": name,
        "nationality": nationality,
        "doc_number": doc_number,
        "job_title": job_title,
        "department": department,
        "location": location,
        "contract_type": contract_type,
        "contract_duration": contract_duration,
        "work_days": work_days,
        "probation": probation,
        "annual_leave": annual_leave,
        "total_salary": total_salary,
        "basic": basic,
        "housing": housing,
        "transport": transport,
        "insurance": insurance,
        "net_salary": net_salary,
        "salary_words_ar": salary_ar_words(net_salary),
        "salary_words_en": salary_en_words(net_salary),
        "date": today.strftime("%d/%m/%Y"),
        "date_en": today.strftime("%B %d, %Y")
    }

    if st.button("Generate PDF", use_container_width=True):
        if not name.strip():
            st.error("Candidate name is required.")
        else:
            pdf_file = generate_pdf(data, language)
            filename = f"DABOUQ_JOB_OFFER_{clean_filename(name)}_{'AR' if language == 'العربية' else 'EN'}.pdf"

            st.success("PDF generated successfully.")

            st.download_button(
                label="Download PDF",
                data=pdf_file,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True
            )