import json
import re
from num2words import num2words
from bidi.algorithm import get_display
import arabic_reshaper

from config import DEFAULT_OFFER_FOOTER


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


def footer_defaults(language: str) -> dict:
    key = "ar" if language == "العربية" else "en"
    return dict(DEFAULT_OFFER_FOOTER[key])


def resolve_footer_fields(form_data: dict) -> dict:
    language = form_data.get("language", "العربية")
    defaults = footer_defaults(language)

    def pick(field: str, default_key: str) -> str:
        if field not in form_data or form_data[field] is None:
            return defaults[default_key].strip()
        return str(form_data[field]).strip()

    return {
        "footer_salary_review": pick("footer_salary_review", "salary_review"),
        "footer_validity": pick("footer_validity", "validity"),
        "footer_acceptance": pick("footer_acceptance", "acceptance"),
        "footer_rejection": pick("footer_rejection", "rejection"),
    }


def extract_json(text):
    text = text.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return {}


def build_offer_payload(form_data):
    basic, housing, transport = salary_split(form_data["total_salary"])
    net_salary = round(form_data["total_salary"] - form_data["insurance"])
    from datetime import datetime

    today = datetime.today()
    footer = resolve_footer_fields(form_data)
    return {
        **form_data,
        **footer,
        "name": form_data.get("candidate_name") or form_data.get("name", ""),
        "doc_number": form_data.get("document_number") or form_data.get("doc_number", ""),
        "basic": basic,
        "housing": housing,
        "transport": transport,
        "net_salary": net_salary,
        "salary_words_ar": salary_ar_words(net_salary),
        "salary_words_en": salary_en_words(net_salary),
        "date": today.strftime("%d/%m/%Y"),
        "date_en": today.strftime("%B %d, %Y"),
    }
