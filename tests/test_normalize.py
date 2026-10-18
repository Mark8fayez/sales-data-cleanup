from datetime import date

import pytest

from cleaning import normalize as nz


@pytest.mark.parametrize("raw, expected", [
    ("01012345678", "+201012345678"),
    ("+201012345678", "+201012345678"),
    ("00201012345678", "+201012345678"),
    ("010 1234 5678", "+201012345678"),
    ("1012345678", "+201012345678"),
    ("+20 101-234-5678", "+201012345678"),
    ("1012345678.0", "+201012345678"),
    ("12345", None),
    ("N/A", None),
    ("01312345678", None),  # 013 is not an Egyptian mobile prefix
])
def test_phone(raw, expected):
    assert nz.phone(raw) == expected


@pytest.mark.parametrize("raw, expected", [
    ("ORD-10001", "ORD-10001"), ("ord10001", "ORD-10001"), ("ORD 10001", "ORD-10001"),
    ("10001", "ORD-10001"), ("10001.0", "ORD-10001"), ("", None),
])
def test_order_id(raw, expected):
    assert nz.order_id(raw) == expected


@pytest.mark.parametrize("raw, expected", [
    ("2026-03-09", date(2026, 3, 9)),
    ("09/03/2026", date(2026, 3, 9)),  # day first, as Egyptian sheets write it
    ("Mar 09, 2026", date(2026, 3, 9)),
    ("2026-03-09 00:00:00", date(2026, 3, 9)),
    ("March 9th", None),
])
def test_order_date(raw, expected):
    assert nz.order_date(raw) == expected


@pytest.mark.parametrize("raw, expected", [
    ("2", 2), ("2 pcs", 2), ("1 pc", 1), ("3.0", 3), ("0", None), ("-2", None), ("two", None),
])
def test_quantity(raw, expected):
    assert nz.quantity(raw) == expected


@pytest.mark.parametrize("raw, expected", [
    ("1150.0", 1150.0), ("2,300.00 EGP", 2300.0), ("EGP 2,400", 2400.0), ("", None), ("-5", None),
])
def test_price(raw, expected):
    assert nz.price(raw) == expected


def test_text_fields():
    assert nz.person_name("  mostafa   ADEL ") == "Mostafa Adel"
    assert nz.email(" FADY.FAWZY55@GMAIL.COM") == "fady.fawzy55@gmail.com"
    assert nz.email("fady.fawzy55.gmail.com") is None
    assert nz.city(" CAIRO ") == "Cairo"
    assert nz.city("Al Qahirah") == "Cairo"
    assert nz.status("Completed") == "delivered"
    assert nz.payment_method("COD") == "cash_on_delivery"


def test_unknown_column_is_flagged():
    assert nz.column_name("Order ID") == "order_id"
    assert nz.column_name("Discount Code") is None
