import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from config import COMPANY
from services.helpers import ar_text, money


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


def generate_pdf(data, language):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    font = register_font()

    c.setTitle("DABOUQ Job Offer")

    navy = (0.06, 0.13, 0.23)

    c.setStrokeColorRGB(*navy)
    c.setLineWidth(2)
    c.line(2 * cm, height - 4.15 * cm, width - 2 * cm, height - 4.15 * cm)

    try:
        logo = ImageReader("logo.jpeg")
        c.drawImage(
            logo,
            2 * cm,
            height - 3.65 * cm,
            width=3.2 * cm,
            height=2.8 * cm,
            preserveAspectRatio=True,
            mask="auto",
        )
    except Exception:
        pass

    if language == "العربية":
        company_lines = [
            COMPANY["name_ar"],
            f"رقم المنشأة: {COMPANY['establishment_no']}",
            f"س.ت: {COMPANY['cr']}",
            f"هاتف: {COMPANY['phone']}",
            f"الرقم الضريبي: {COMPANY['tax_id']}",
        ]

        y = height - 1.55 * cm
        c.setFillColorRGB(*navy)
        for line in company_lines:
            draw_ar(c, width - 2 * cm, y, line, font, 9.2)
            y -= 0.42 * cm

        c.setFillColor(colors.black)

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

        draw_section_title(c, 2 * cm, y, "تفاصيل الوظيفة", font, width)
        y -= 0.9 * cm
        draw_label_value_ar(c, "المسمى الوظيفي", data["job_title"], width - 2.3 * cm, y, font)
        y -= 0.5 * cm
        draw_label_value_ar(c, "القسم", data["department"], width - 2.3 * cm, y, font)
        y -= 0.5 * cm
        draw_label_value_ar(c, "موقع العمل", data["location"], width - 2.3 * cm, y, font)

        y -= 0.75 * cm

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

        draw_section_title(c, 2 * cm, y, "تفاصيل الراتب الشهري", font, width)
        y -= 0.85 * cm
        y = draw_salary_table_ar(c, data, 2 * cm, y, font, width)

        draw_ar(c, width - 2.3 * cm, y, f"صافي الراتب كتابة: فقط {data['salary_words_ar']}", font, 9.4)
        y -= 0.75 * cm

        draw_section_title(c, 2 * cm, y, "المزايا", font, width)
        y -= 0.9 * cm
        draw_label_value_ar(c, "التأمين الطبي", "يُوفر وفقًا لمتطلبات الوظيفة", width - 2.3 * cm, y, font)
        y -= 0.5 * cm
        draw_label_value_ar(c, "مزايا أخرى", "حسب السياسات الداخلية للشركة", width - 2.3 * cm, y, font)

        y -= 0.65 * cm

        draw_ar(c, width - 2.3 * cm, y, "سيتم مراجعة الراتب بعد مرور ثلاثة (3) أشهر من تاريخ مباشرة العمل، وذلك لغرض النظر في إمكانية زيادة الراتب وتثبيت الموظف بناءً على تقييم الأداء.", font, 8.7)
        y -= 0.55 * cm
        draw_ar(c, width - 2.3 * cm, y, "ويُعتبر هذا العرض ساري المفعول لمدة عشرة (10) أيام فقط من تاريخ صدوره.", font, 8.7)

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
            COMPANY["name_en"],
            f"Establishment No: {COMPANY['establishment_no']}",
            f"C.R: {COMPANY['cr']}",
            f"Phone: {COMPANY['phone']}",
            f"Tax ID: {COMPANY['tax_id']}",
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
            ("Contract Type", data["contract_type"]),
            ("Duration", data["contract_duration"]),
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
