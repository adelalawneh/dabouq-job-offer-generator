from datetime import timedelta

COMPANY = {
    "name_ar": "شركة دابوق التجارية شركة شخص واحد",
    "name_en": "Dabouq Commercial Company One Person Co.",
    "establishment_no": "7013895862",
    "cr": "3550102093",
    "phone": "0556018251",
    "tax_id": "311280392800003",
}

OFFER_VALIDITY_DAYS = 10

STATUS_LABELS = {
    "draft": "📝 مسودة",
    "sent": "📤 مُرسل",
    "accepted": "✅ مقبول",
    "rejected": "❌ مرفوض",
    "expired": "⏰ منتهي",
}

JOB_TEMPLATES = {
    "مندوب مبيعات": {
        "job_title": "مندوب مبيعات",
        "department": "المبيعات",
        "location": "منطقة الرياض",
        "total_salary": 3500.0,
    },
    "محاسب": {
        "job_title": "محاسب",
        "department": "المالية",
        "location": "منطقة الرياض",
        "total_salary": 5000.0,
    },
    "سائق": {
        "job_title": "سائق",
        "department": "العمليات",
        "location": "منطقة الرياض",
        "total_salary": 3000.0,
    },
    "مشرف مستودع": {
        "job_title": "مشرف مستودع",
        "department": "المستودعات",
        "location": "منطقة الرياض",
        "total_salary": 4500.0,
    },
}

DEFAULT_CONTRACT = {
    "contract_type": "محدد المدة (فردي)",
    "contract_duration": "سنة",
    "work_days": "٦ أيام في الأسبوع - 9 ساعات يوميًا تتضمن ساعة راحة",
    "probation": "٩٠ يومًا",
    "annual_leave": "٢١ يومًا في السنة",
}

DB_PATH = "data/offers.db"
