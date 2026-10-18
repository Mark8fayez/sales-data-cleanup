"""
Small, testable functions that turn one messy value into one clean value.

Rule for every function here: return the clean value, or None when the value
cannot be trusted. Never guess silently; the caller logs what was rejected.
"""

import re
from datetime import date, datetime

# Every column name we have seen in the exports -> the one name we use
COLUMN_MAP = {
    "order id": "order_id", "order_no": "order_id", "orderid": "order_id",
    "order date": "order_date", "date": "order_date",
    "customer name": "customer_name", "customer": "customer_name", "client": "customer_name",
    "phone": "phone", "mobile": "phone", "phone number": "phone",
    "email": "email", "e-mail": "email", "email address": "email",
    "city": "city", "governorate": "city",
    "product": "product", "item": "product", "product name": "product",
    "qty": "quantity", "quantity": "quantity", "units": "quantity",
    "unit price (egp)": "unit_price", "price": "unit_price",
    "payment": "payment_method", "payment_method": "payment_method", "pay method": "payment_method",
    "status": "status", "order_status": "status",
}

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%b %d, %Y"]

CITY_MAP = {
    "cairo": "Cairo", "cairo city": "Cairo", "al qahirah": "Cairo",
    "giza": "Giza", "el giza": "Giza",
    "alexandria": "Alexandria", "alex": "Alexandria",
    "mansoura": "Mansoura", "el mansoura": "Mansoura",
    "tanta": "Tanta",
}
STATUS_MAP = {
    "delivered": "delivered", "completed": "delivered",
    "cancelled": "cancelled", "canceled": "cancelled",
    "returned": "returned", "refunded": "returned",
    "pending": "pending", "in progress": "pending",
}
PAYMENT_MAP = {
    "cash on delivery": "cash_on_delivery", "cod": "cash_on_delivery", "cash": "cash_on_delivery",
    "card": "card", "credit card": "card", "visa": "card",
    "wallet": "mobile_wallet", "vodafone cash": "mobile_wallet", "mobile wallet": "mobile_wallet",
}

EMAIL_RE = re.compile(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$")
EG_MOBILE_RE = re.compile(r"^\+201[0125]\d{8}$")


def _text(value) -> str | None:
    """Turn any cell into a stripped string, or None if it is empty."""
    if value is None:
        return None
    s = str(value).strip()
    return None if s == "" or s.lower() in {"nan", "none", "n/a", "null"} else s


def column_name(raw: str) -> str | None:
    return COLUMN_MAP.get(str(raw).strip().lower())


def order_id(value) -> str | None:
    """'ord10001', 'ORD 10001', '10001', '10001.0' -> 'ORD-10001'."""
    s = _text(value)
    if s is None:
        return None
    s = re.sub(r"\.0$", "", s)  # Excel sometimes turns 10001 into 10001.0
    digits = re.sub(r"\D", "", s)
    return f"ORD-{digits}" if digits else None


def order_date(value) -> date | None:
    """Try each known export format. Ambiguous or unknown formats are rejected."""
    s = _text(value)
    if s is None:
        return None
    s = s.split(" 00:00:00")[0]  # Excel datetime leftovers
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def person_name(value) -> str | None:
    """'  mostafa   ADEL ' -> 'Mostafa Adel'."""
    s = _text(value)
    return " ".join(s.split()).title() if s else None


def phone(value) -> str | None:
    """Any Egyptian mobile format -> E.164 '+201012345678'. Invalid -> None."""
    s = _text(value)
    if s is None:
        return None
    digits = re.sub(r"\D", "", re.sub(r"\.0$", "", s))
    if digits.startswith("0020"):
        digits = digits[4:]
    elif digits.startswith("20") and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    candidate = "+20" + digits
    return candidate if EG_MOBILE_RE.match(candidate) else None


def email(value) -> str | None:
    s = _text(value)
    if s is None:
        return None
    s = s.lower()
    return s if EMAIL_RE.match(s) else None


def city(value) -> str | None:
    s = _text(value)
    return CITY_MAP.get(" ".join(s.lower().split())) if s else None


def status(value) -> str | None:
    s = _text(value)
    return STATUS_MAP.get(s.lower()) if s else None


def payment_method(value) -> str | None:
    s = _text(value)
    return PAYMENT_MAP.get(s.lower()) if s else None


def quantity(value) -> int | None:
    """'2 pcs' -> 2. Zero or negative quantities are rejected (returns live in status)."""
    s = _text(value)
    if s is None:
        return None
    m = re.match(r"^(-?\d+)(\.0+)?\s*(pcs?)?$", s.lower())
    if not m:
        return None
    q = int(m.group(1))
    return q if q > 0 else None


def price(value) -> float | None:
    """'2,300.00 EGP', 'EGP 2,400', '1150.0' -> float. Missing or non-positive -> None."""
    s = _text(value)
    if s is None:
        return None
    s = s.upper().replace("EGP", "").replace(",", "").strip()
    try:
        p = float(s)
    except ValueError:
        return None
    return p if p > 0 else None
