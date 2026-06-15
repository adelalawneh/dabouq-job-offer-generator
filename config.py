COMPANY = {
    "name_ar": "شركة دابوق التجارية شركة شخص واحد",
    "name_ar_full": "شركة دابوق التجارية شركة شخص واحد",
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

DEFAULT_OFFER_FOOTER = {
    "ar": {
        "salary_review": "سيتم مراجعة الراتب بعد مرور ثلاثة (3) أشهر من تاريخ مباشرة العمل، وذلك لغرض النظر في إمكانية زيادة الراتب وتثبيت الموظف بناءً على تقييم الأداء.",
        "validity": "ويُعتبر هذا العرض ساري المفعول لمدة عشرة (10) أيام فقط من تاريخ صدوره.",
        "acceptance": "أوافق على ما ورد أعلاه، وأقر بأن تاريخ بدء عملي سيكون اعتبارًا من:      /      / ٢٠٢٦",
        "rejection": "لا أوافق على العرض المذكور أعلاه للأسباب التالية: ........................................................",
    },
    "en": {
        "salary_review": "Salary will be reviewed after three (3) months from the date of joining, for the purpose of considering a salary increase and confirmation based on performance evaluation.",
        "validity": "This offer is valid for ten (10) days only from the date of issuance.",
        "acceptance": "I agree to the terms above. My start date will be: ____ / ____ / 2026",
        "rejection": "I do not agree to the above offer for the following reasons: ........................................................",
    },
}

LOGO_PATH = "assets/logo_group.png"
DB_PATH = "data/offers.db"
