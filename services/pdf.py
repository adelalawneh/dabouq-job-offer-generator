import io
import re
from pathlib import Path

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from config import COMPANY, LOGO_PATH
from services.helpers import ar_text, money

NAVY = (0.06, 0.13, 0.23)
FONT_EN = "Helvetica"
FONT_EN_BOLD = "Helvetica-Bold"
ROOT = Path(__file__).resolve().parent.parent
MARGIN_X = 2 * cm
CONTENT_W = A4[0] - 4 * cm


def register_font():
    font_path = ROOT / "IBMPlexSansArabic-Regular.ttf"
    try:
        pdfmetrics.registerFont(TTFont("DabouqFont", str(font_path)))
        return "DabouqFont"
    except Exception as e:
        print("Font error:", e)
        return FONT_EN


def _has_arabic(text) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", str(text or "")))


def draw_ar(c, x, y, text, font, size=10):
    c.setFont(font, size)
    c.drawRightString(x, y, ar_text(text))


def _trim_logo(img: Image.Image) -> Image.Image:
    rgb = img.convert("RGB")
    gray = rgb.convert("L")
    mask = gray.point(lambda p: 255 if p < 245 else 0)
    bbox = mask.getbbox()
    if not bbox:
        return rgb
    return rgb.crop(bbox)


def _logo_bytes(logo_path: Path) -> tuple[io.BytesIO, float]:
    with Image.open(logo_path) as img:
        trimmed = _trim_logo(img)
        iw, ih = trimmed.size
        aspect = iw / max(ih, 1)
        buf = io.BytesIO()
        trimmed.save(buf, format="PNG")
        buf.seek(0)
        return buf, aspect


def draw_logo(c, x, y, *, max_width=9 * cm, max_height=2.15 * cm):
    for logo_name in (LOGO_PATH, "assets/logo_group.png", "assets/logo_clean.png", "logo.jpeg"):
        logo_path = ROOT / logo_name
        if not logo_path.exists():
            continue
        try:
            buf, aspect = _logo_bytes(logo_path)
            draw_h = min(max_height, max_width / aspect)
            draw_w = draw_h * aspect
            c.drawImage(
                ImageReader(buf),
                x,
                y,
                width=draw_w,
                height=draw_h,
                preserveAspectRatio=True,
                anchor="sw",
                mask=None,
            )
            return draw_h
        except Exception:
            continue
    return 0


def _wrap_en(c, text, max_width, font_name=FONT_EN, font_size=8.7):
    words = str(text or "").split()
    if not words:
        return []
    lines = []
    current = []
    for word in words:
        trial = " ".join([*current, word]).strip()
        if c.stringWidth(trial, font_name, font_size) <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def draw_wrapped_en(c, text, x, y, max_width, *, font_size=8.7, line_gap=0.48 * cm):
    c.setFont(FONT_EN, font_size)
    for line in _wrap_en(c, text, max_width, FONT_EN, font_size):
        c.drawString(x, y, line)
        y -= line_gap
    return y


def draw_wrapped_ar(c, text, x, y, max_width, font, *, font_size=8.7, line_gap=0.48 * cm):
    # Simple wrap by words using measured Arabic-shaped strings.
    words = str(text or "").split()
    if not words:
        return y
    lines = []
    current = []
    for word in words:
        trial = " ".join([*current, word]).strip()
        shaped = ar_text(trial)
        if c.stringWidth(shaped, font, font_size) <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    for line in lines:
        draw_ar(c, x, y, line, font, font_size)
        y -= line_gap
    return y


def draw_company_header_en(c, width, height):
    draw_logo(c, MARGIN_X, height - 3.35 * cm, max_height=2.15 * cm, max_width=9 * cm)
    c.setFont(FONT_EN, 9.2)
    c.setFillColorRGB(*NAVY)
    lines = [
        COMPANY["name_en"],
        f"Establishment No: {COMPANY['establishment_no']}",
        f"C.R: {COMPANY['cr']}",
        f"Phone: {COMPANY['phone']}",
        f"Tax ID: {COMPANY['tax_id']}",
    ]
    y = height - 1.55 * cm
    for line in lines:
        c.drawRightString(width - MARGIN_X, y, line)
        y -= 0.42 * cm
    c.setFillColor(colors.black)


def draw_company_header_ar(c, width, height, font):
    draw_logo(c, MARGIN_X, height - 3.35 * cm, max_height=2.15 * cm, max_width=9 * cm)
    company_lines = [
        COMPANY["name_ar_full"],
        f"رقم المنشأة: {COMPANY['establishment_no']}",
        f"س.ت: {COMPANY['cr']}",
        f"هاتف: {COMPANY['phone']}",
        f"الرقم الضريبي: {COMPANY['tax_id']}",
    ]
    y = height - 1.55 * cm
    c.setFillColorRGB(*NAVY)
    for line in company_lines:
        draw_ar(c, width - MARGIN_X, y, line, font, 9.2)
        y -= 0.42 * cm
    c.setFillColor(colors.black)


def draw_section_title_ar(c, x, y, title, font, page_width):
    c.setFillColorRGB(*NAVY)
    c.roundRect(x, y - 0.25 * cm, page_width - 4 * cm, 0.65 * cm, 0.12 * cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    draw_ar(c, page_width - 2.3 * cm, y - 0.03 * cm, title, font, 10.5)
    c.setFillColor(colors.black)


def draw_section_title_en(c, x, y, title, page_width):
    c.setFillColorRGB(*NAVY)
    c.roundRect(x, y - 0.25 * cm, page_width - 4 * cm, 0.65 * cm, 0.12 * cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(FONT_EN_BOLD, 10.5)
    c.drawString(x + 0.35 * cm, y - 0.03 * cm, title)
    c.setFillColor(colors.black)


def draw_label_value_ar(c, label, value, x, y, font):
    c.setFont(font, 10)
    draw_ar(c, x, y, f"{label}: {value}", font, 10)


def draw_label_value_en(c, label, value, y, font_ar, page_width=None):
    x = MARGIN_X + 0.3 * cm
    value = str(value or "—")
    prefix = f"{label}: "
    if _has_arabic(value):
        c.setFont(FONT_EN, 10)
        c.drawString(x, y, prefix)
        c.setFont(font_ar, 10)
        c.drawString(x + c.stringWidth(prefix, FONT_EN, 10), y, ar_text(value))
    else:
        c.setFont(FONT_EN, 10)
        c.drawString(x, y, f"{prefix}{value}")


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


def draw_salary_table_en(c, data, x, y, font_ar, width):
    rows = [
        ("Basic Salary", f"{money(data['basic'])} SAR"),
        ("Housing Allowance", f"{money(data['housing'])} SAR"),
        ("Transport Allowance", f"{money(data['transport'])} SAR"),
        ("Gross Salary", f"{money(data['total_salary'])} SAR"),
        ("GOSI Deduction", f"{money(data['insurance'])} SAR"),
        ("Net Salary", f"{money(data['net_salary'])} SAR"),
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
        row_text = f"{label}: {value}"
        c.setFont(FONT_EN, 9.5)
        c.drawString(x + 0.35 * cm, yy - 0.38 * cm, row_text)

    return y - len(rows) * row_h - 0.2 * cm


def _footer_lines(data, language):
    if language == "العربية":
        return [
            data.get("footer_salary_review") or "",
            data.get("footer_validity") or "",
            data.get("footer_acceptance") or "",
            data.get("footer_rejection") or "",
        ]
    return [
        data.get("footer_salary_review") or "",
        data.get("footer_validity") or "",
        data.get("footer_acceptance") or "",
        data.get("footer_rejection") or "",
    ]


def _draw_pdf_ar(c, data, width, height, font):
    draw_company_header_ar(c, width, height, font)

    c.setStrokeColorRGB(*NAVY)
    c.setLineWidth(1)
    c.roundRect(width / 2 - 2.7 * cm, height - 5.05 * cm, 5.4 * cm, 0.85 * cm, 0.18 * cm, fill=0, stroke=1)
    c.setFillColorRGB(*NAVY)
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

    draw_section_title_ar(c, 2 * cm, y, "تفاصيل الوظيفة", font, width)
    y -= 0.9 * cm
    draw_label_value_ar(c, "المسمى الوظيفي", data["job_title"], width - 2.3 * cm, y, font)
    y -= 0.5 * cm
    draw_label_value_ar(c, "القسم", data["department"], width - 2.3 * cm, y, font)
    y -= 0.5 * cm
    draw_label_value_ar(c, "موقع العمل", data["location"], width - 2.3 * cm, y, font)
    y -= 0.75 * cm

    draw_section_title_ar(c, 2 * cm, y, "تفاصيل العقد", font, width)
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

    draw_section_title_ar(c, 2 * cm, y, "تفاصيل الراتب الشهري", font, width)
    y -= 0.85 * cm
    y = draw_salary_table_ar(c, data, 2 * cm, y, font, width)
    draw_ar(c, width - 2.3 * cm, y, f"صافي الراتب كتابة: فقط {data['salary_words_ar']}", font, 9.4)
    y -= 0.75 * cm

    draw_section_title_ar(c, 2 * cm, y, "المزايا", font, width)
    y -= 0.9 * cm
    draw_label_value_ar(c, "التأمين الطبي", "يُوفر وفقًا لمتطلبات الوظيفة", width - 2.3 * cm, y, font)
    y -= 0.5 * cm
    draw_label_value_ar(c, "مزايا أخرى", "حسب السياسات الداخلية للشركة", width - 2.3 * cm, y, font)
    y -= 0.65 * cm

    for line in _footer_lines(data, "العربية"):
        if line:
            y = draw_wrapped_ar(c, line, width - MARGIN_X, y, CONTENT_W, font, font_size=8.7)
            y -= 0.12 * cm

    c.setStrokeColorRGB(*NAVY)
    c.setLineWidth(1)
    c.line(2 * cm, 2.35 * cm, width - 2 * cm, 2.35 * cm)
    draw_ar(c, width - 2.2 * cm, 1.35 * cm, "إدارة الموارد البشرية", font, 9.5)


def _draw_pdf_en(c, data, width, height, font_ar):
    draw_company_header_en(c, width, height)

    c.setStrokeColorRGB(*NAVY)
    c.setLineWidth(1)
    c.roundRect(width / 2 - 2.7 * cm, height - 5.05 * cm, 5.4 * cm, 0.85 * cm, 0.18 * cm, fill=0, stroke=1)
    c.setFillColorRGB(*NAVY)
    c.setFont(FONT_EN_BOLD, 15)
    c.drawCentredString(width / 2, height - 4.78 * cm, "JOB OFFER")
    c.setFillColor(colors.black)

    y = height - 5.9 * cm
    draw_label_value_en(c, "Date", data["date_en"], y, font_ar, width)
    y -= 0.58 * cm
    draw_label_value_en(c, "To", f"Mr. {data['name']}", y, font_ar, width)
    y -= 0.58 * cm
    draw_label_value_en(c, "Document No.", data["doc_number"], y, font_ar, width)
    y -= 0.75 * cm

    draw_section_title_en(c, 2 * cm, y, "Job Details", width)
    y -= 0.9 * cm
    draw_label_value_en(c, "Job Title", data["job_title"], y, font_ar, width)
    y -= 0.5 * cm
    draw_label_value_en(c, "Department", data["department"], y, font_ar, width)
    y -= 0.5 * cm
    draw_label_value_en(c, "Work Location", data["location"], y, font_ar, width)
    y -= 0.75 * cm

    draw_section_title_en(c, 2 * cm, y, "Contract Details", width)
    y -= 0.9 * cm
    draw_label_value_en(c, "Contract Type", data["contract_type"], y, font_ar, width)
    y -= 0.5 * cm
    draw_label_value_en(c, "Duration", data["contract_duration"], y, font_ar, width)
    y -= 0.5 * cm
    draw_label_value_en(c, "Working Days", data["work_days"], y, font_ar, width)
    y -= 0.5 * cm
    draw_label_value_en(c, "Probation Period", data["probation"], y, font_ar, width)
    y -= 0.5 * cm
    draw_label_value_en(c, "Annual Leave", data["annual_leave"], y, font_ar, width)
    y -= 0.75 * cm

    draw_section_title_en(c, 2 * cm, y, "Monthly Salary Details", width)
    y -= 0.85 * cm
    y = draw_salary_table_en(c, data, 2 * cm, y, font_ar, width)
    salary_words = f"Salary in Words: {data['salary_words_en']}"
    y = draw_wrapped_en(c, salary_words, MARGIN_X + 0.3 * cm, y, CONTENT_W, font_size=9.4, line_gap=0.42 * cm)
    y -= 0.35 * cm

    draw_section_title_en(c, 2 * cm, y, "Benefits", width)
    y -= 0.9 * cm
    draw_label_value_en(c, "Medical Insurance", "Provided as per job requirements", y, font_ar, width)
    y -= 0.5 * cm
    draw_label_value_en(c, "Other Benefits", "As per company internal policies", y, font_ar, width)
    y -= 0.65 * cm

    for line in _footer_lines(data, "English"):
        if not line:
            continue
        if _has_arabic(line):
            y = draw_wrapped_ar(c, line, width - MARGIN_X, y, CONTENT_W, font_ar, font_size=8.7)
        else:
            y = draw_wrapped_en(c, line, MARGIN_X + 0.3 * cm, y, CONTENT_W, font_size=8.7)
        y -= 0.12 * cm

    c.setStrokeColorRGB(*NAVY)
    c.setLineWidth(1)
    c.line(2 * cm, 2.35 * cm, width - 2 * cm, 2.35 * cm)
    c.setFont(FONT_EN, 9.5)
    c.drawString(2.3 * cm, 1.35 * cm, "Human Resources Department")


def generate_pdf(data, language):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    font_ar = register_font()

    c.setTitle("DABOUQ Job Offer")
    c.setStrokeColorRGB(*NAVY)
    c.setLineWidth(2)
    c.line(MARGIN_X, height - 4.15 * cm, width - MARGIN_X, height - 4.15 * cm)

    if language == "العربية":
        _draw_pdf_ar(c, data, width, height, font_ar)
    else:
        _draw_pdf_en(c, data, width, height, font_ar)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
