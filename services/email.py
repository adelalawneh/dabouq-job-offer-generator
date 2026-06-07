import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from config import COMPANY, OFFER_VALIDITY_DAYS
from services.helpers import clean_filename, money


def _get_secret(key, default=""):
    import streamlit as st
    return st.secrets.get(key, default)


def _load_template(name, **kwargs):
    path = Path("templates") / name
    html = path.read_text(encoding="utf-8")
    for key, value in kwargs.items():
        html = html.replace(f"{{{{{key}}}}}", str(value))
    return html


def _smtp_configured():
    return bool(_get_secret("SMTP_HOST") and _get_secret("SMTP_USER"))


def send_email(to, subject, html_body, pdf_bytes=None, pdf_filename=None, cc=None):
    if not _smtp_configured():
        raise RuntimeError("SMTP is not configured. Add SMTP settings to .streamlit/secrets.toml")

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = _get_secret("SMTP_FROM", _get_secret("SMTP_USER"))
    msg["To"] = to
    if cc:
        msg["Cc"] = cc

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    if pdf_bytes and pdf_filename:
        attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
        attachment.add_header("Content-Disposition", "attachment", filename=pdf_filename)
        msg.attach(attachment)

    recipients = [to]
    if cc:
        recipients.append(cc)

    with smtplib.SMTP(_get_secret("SMTP_HOST"), int(_get_secret("SMTP_PORT", 587))) as server:
        server.starttls()
        server.login(_get_secret("SMTP_USER"), _get_secret("SMTP_PASSWORD"))
        server.sendmail(msg["From"], recipients, msg.as_string())


def respond_url(token):
    base = _get_secret("APP_BASE_URL", "http://localhost:8501")
    return f"{base}?token={token}"


def send_offer_email(offer, pdf_bytes):
    lang = offer.get("language", "العربية")
    is_ar = lang == "العربية"
    url = respond_url(offer["token"])
    name = offer["candidate_name"]
    pdf_name = f"DABOUQ_JOB_OFFER_{clean_filename(name)}_{'AR' if is_ar else 'EN'}.pdf"

    if is_ar:
        subject = f"عرض وظيفي — {COMPANY['name_ar']}"
        html = _load_template(
            "email_offer_ar.html",
            candidate_name=name,
            job_title=offer["job_title"],
            net_salary=money(offer["net_salary"]),
            respond_url=url,
            validity_days=OFFER_VALIDITY_DAYS,
            company_phone=COMPANY["phone"],
        )
    else:
        subject = f"Job Offer — {COMPANY['name_en']}"
        html = _load_template(
            "email_offer_en.html",
            candidate_name=name,
            job_title=offer["job_title"],
            net_salary=money(offer["net_salary"]),
            respond_url=url,
            validity_days=OFFER_VALIDITY_DAYS,
            company_phone=COMPANY["phone"],
        )

    hr_email = _get_secret("HR_EMAIL", "")
    send_email(
        to=offer["candidate_email"],
        subject=subject,
        html_body=html,
        pdf_bytes=pdf_bytes,
        pdf_filename=pdf_name,
        cc=hr_email or None,
    )


def send_hr_notification(offer, event):
    hr_email = _get_secret("HR_EMAIL")
    if not hr_email:
        return

    name = offer["candidate_name"]
    job = offer["job_title"]

    if event == "accepted":
        subject = f"✅ تم قبول العرض — {name}"
        body = f"""
        <div style="font-family:Arial,sans-serif;direction:rtl;text-align:right;">
            <h2>تم قبول عرض وظيفي</h2>
            <p><strong>المرشّح:</strong> {name}</p>
            <p><strong>الوظيفة:</strong> {job}</p>
            <p><strong>تاريخ البدء:</strong> {offer.get('start_date', '—')}</p>
            <p><strong>البريد:</strong> {offer.get('candidate_email', '—')}</p>
        </div>
        """
    elif event == "rejected":
        subject = f"❌ تم رفض العرض — {name}"
        body = f"""
        <div style="font-family:Arial,sans-serif;direction:rtl;text-align:right;">
            <h2>تم رفض عرض وظيفي</h2>
            <p><strong>المرشّح:</strong> {name}</p>
            <p><strong>الوظيفة:</strong> {job}</p>
            <p><strong>سبب الرفض:</strong> {offer.get('rejection_reason') or '—'}</p>
        </div>
        """
    else:
        subject = f"📤 تم إرسال عرض — {name}"
        body = f"""
        <div style="font-family:Arial,sans-serif;direction:rtl;text-align:right;">
            <h2>تم إرسال عرض وظيفي</h2>
            <p><strong>المرشّح:</strong> {name}</p>
            <p><strong>الوظيفة:</strong> {job}</p>
            <p><strong>البريد:</strong> {offer.get('candidate_email', '—')}</p>
        </div>
        """

    send_email(to=hr_email, subject=subject, html_body=body)


def send_candidate_confirmation(offer, accepted):
    email = offer.get("candidate_email")
    if not email:
        return

    name = offer["candidate_name"]
    is_ar = offer.get("language") == "العربية"

    if accepted:
        if is_ar:
            subject = "تأكيد قبول العرض الوظيفي — دابوق"
            body = f"""
            <div style="font-family:Arial,sans-serif;direction:rtl;text-align:right;">
                <p>السيد/ {name} المحترم،</p>
                <p>تم تسجيل قبولكم للعرض الوظيفي بنجاح.</p>
                <p>تاريخ البدء المتوقع: <strong>{offer.get('start_date', '—')}</strong></p>
                <p>سيتواصل معكم فريق الموارد البشرية قريبًا.</p>
                <p>مع تحيات،<br>إدارة الموارد البشرية — دابوق</p>
            </div>
            """
        else:
            subject = "Job Offer Acceptance Confirmation — DABOUQ"
            body = f"""
            <div style="font-family:Arial,sans-serif;">
                <p>Dear {name},</p>
                <p>Your acceptance of the job offer has been recorded successfully.</p>
                <p>Expected start date: <strong>{offer.get('start_date', '—')}</strong></p>
                <p>Our HR team will contact you shortly.</p>
                <p>Best regards,<br>DABOUQ Human Resources</p>
            </div>
            """
    else:
        if is_ar:
            subject = "تأكيد رفض العرض الوظيفي — دابوق"
            body = f"""
            <div style="font-family:Arial,sans-serif;direction:rtl;text-align:right;">
                <p>السيد/ {name} المحترم،</p>
                <p>تم تسجيل رفضكم للعرض الوظيفي.</p>
                <p>نشكركم على اهتمامكم ونتمنى لكم التوفيق.</p>
                <p>مع تحيات،<br>إدارة الموارد البشرية — دابوق</p>
            </div>
            """
        else:
            subject = "Job Offer Decline Confirmation — DABOUQ"
            body = f"""
            <div style="font-family:Arial,sans-serif;">
                <p>Dear {name},</p>
                <p>Your decline of the job offer has been recorded.</p>
                <p>Thank you for your interest. We wish you all the best.</p>
                <p>Best regards,<br>DABOUQ Human Resources</p>
            </div>
            """

    send_email(to=email, subject=subject, html_body=body)
