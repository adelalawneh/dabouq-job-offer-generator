import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from config import DB_PATH, OFFER_VALIDITY_DAYS

OFFER_FIELDS = [
    "candidate_name", "candidate_email", "candidate_nationality", "document_number",
    "job_title", "department", "location",
    "contract_type", "contract_duration", "work_days", "probation", "annual_leave",
    "total_salary", "insurance", "basic", "housing", "transport", "net_salary",
    "language", "created_by",
    "footer_salary_review", "footer_validity", "footer_acceptance", "footer_rejection",
]

FOOTER_DB_COLUMNS = [
    "footer_salary_review TEXT",
    "footer_validity TEXT",
    "footer_acceptance TEXT",
    "footer_rejection TEXT",
]


def _ensure_schema(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS offers (
            id TEXT PRIMARY KEY,
            token TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            sent_at TEXT,
            responded_at TEXT,
            expires_at TEXT,
            candidate_name TEXT NOT NULL,
            candidate_email TEXT,
            candidate_nationality TEXT,
            document_number TEXT,
            job_title TEXT,
            department TEXT,
            location TEXT,
            contract_type TEXT,
            contract_duration TEXT,
            work_days TEXT,
            probation TEXT,
            annual_leave TEXT,
            total_salary REAL,
            insurance REAL,
            basic REAL,
            housing REAL,
            transport REAL,
            net_salary REAL,
            language TEXT,
            start_date TEXT,
            rejection_reason TEXT,
            created_by TEXT
        )
    """)
    existing = {row[1] for row in conn.execute("PRAGMA table_info(offers)")}
    for column_def in FOOTER_DB_COLUMNS:
        column_name = column_def.split()[0]
        if column_name not in existing:
            conn.execute(f"ALTER TABLE offers ADD COLUMN {column_def}")
    conn.commit()


def _connect():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn


def init_db():
    with _connect():
        pass


def _now():
    return datetime.utcnow().isoformat()


def _row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def create_offer(data, status="draft"):
    offer_id = str(uuid.uuid4())
    now = _now()
    values = [offer_id, offer_id, status, now, now]
    values += [data.get(f) for f in OFFER_FIELDS]
    placeholders = ", ".join(["?"] * len(values))
    columns = "id, token, status, created_at, updated_at, " + ", ".join(OFFER_FIELDS)

    with _connect() as conn:
        conn.execute(f"INSERT INTO offers ({columns}) VALUES ({placeholders})", values)
        conn.commit()
    return offer_id


def update_offer(offer_id, data, status=None):
    now = _now()
    sets = ["updated_at = ?"]
    values = [now]

    for field in OFFER_FIELDS:
        if field in data:
            sets.append(f"{field} = ?")
            values.append(data[field])

    if status:
        sets.append("status = ?")
        values.append(status)

    values.append(offer_id)
    with _connect() as conn:
        conn.execute(f"UPDATE offers SET {', '.join(sets)} WHERE id = ?", values)
        conn.commit()


def mark_sent(offer_id):
    now = _now()
    expires = (datetime.utcnow() + timedelta(days=OFFER_VALIDITY_DAYS)).isoformat()
    with _connect() as conn:
        conn.execute(
            "UPDATE offers SET status = 'sent', sent_at = ?, expires_at = ?, updated_at = ? WHERE id = ?",
            (now, expires, now, offer_id),
        )
        conn.commit()


def respond_to_offer(offer_id, accepted, start_date=None, rejection_reason=None):
    now = _now()
    status = "accepted" if accepted else "rejected"
    with _connect() as conn:
        conn.execute(
            """UPDATE offers SET status = ?, responded_at = ?, updated_at = ?,
               start_date = ?, rejection_reason = ? WHERE id = ?""",
            (status, now, now, start_date, rejection_reason, offer_id),
        )
        conn.commit()


def delete_offer(offer_id: str, *, drafts_only: bool = True) -> bool:
    with _connect() as conn:
        if drafts_only:
            cur = conn.execute("DELETE FROM offers WHERE id = ? AND status = 'draft'", (offer_id,))
        else:
            cur = conn.execute("DELETE FROM offers WHERE id = ?", (offer_id,))
        conn.commit()
        return cur.rowcount > 0


def get_offer(offer_id):
    with _connect() as conn:
        row = conn.execute("SELECT * FROM offers WHERE id = ?", (offer_id,)).fetchone()
    return _row_to_dict(row)


def get_offer_by_token(token):
    with _connect() as conn:
        row = conn.execute("SELECT * FROM offers WHERE token = ?", (token,)).fetchone()
    return _row_to_dict(row)


def list_offers(status_filter=None, search=None):
    query = "SELECT * FROM offers WHERE 1=1"
    params = []

    if status_filter and status_filter != "all":
        query += " AND status = ?"
        params.append(status_filter)

    if search:
        query += " AND (candidate_name LIKE ? OR candidate_email LIKE ? OR job_title LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    query += " ORDER BY created_at DESC"

    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def expire_stale_offers():
    now = _now()
    with _connect() as conn:
        conn.execute(
            "UPDATE offers SET status = 'expired', updated_at = ? WHERE status = 'sent' AND expires_at < ?",
            (now, now),
        )
        conn.commit()


def get_stats():
    expire_stale_offers()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as count FROM offers GROUP BY status"
        ).fetchall()
    stats = {r["status"]: r["count"] for r in rows}
    stats["total"] = sum(stats.values())
    return stats


def offer_to_pdf_data(offer):
    from services.helpers import resolve_footer_fields, salary_ar_words, salary_en_words
    from datetime import datetime

    sent = offer.get("sent_at") or offer.get("created_at")
    if sent:
        dt = datetime.fromisoformat(sent)
        date_str = dt.strftime("%d/%m/%Y")
        date_en = dt.strftime("%B %d, %Y")
    else:
        date_str = datetime.today().strftime("%d/%m/%Y")
        date_en = datetime.today().strftime("%B %d, %Y")

    net = offer["net_salary"]
    footer = resolve_footer_fields(offer)
    return {
        "name": offer["candidate_name"],
        "nationality": offer.get("candidate_nationality") or "",
        "doc_number": offer.get("document_number") or "",
        "job_title": offer["job_title"],
        "department": offer["department"],
        "location": offer["location"],
        "contract_type": offer["contract_type"],
        "contract_duration": offer["contract_duration"],
        "work_days": offer["work_days"],
        "probation": offer["probation"],
        "annual_leave": offer["annual_leave"],
        "total_salary": offer["total_salary"],
        "basic": offer["basic"],
        "housing": offer["housing"],
        "transport": offer["transport"],
        "insurance": offer["insurance"],
        "net_salary": net,
        "salary_words_ar": salary_ar_words(net),
        "salary_words_en": salary_en_words(net),
        "date": date_str,
        "date_en": date_en,
        **footer,
    }
