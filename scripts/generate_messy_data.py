"""
Generate realistic, messy monthly order exports for a fictional online store.

Story: "Nile Basket" sells home goods online in Egypt. Every month someone exports
orders from a different tool (the web shop, a sales rep's Excel sheet, a newer
POS system), so the files never match. This script recreates that mess on purpose,
so clean.py has something real to fix.

Run:
    python scripts/generate_messy_data.py --out data/raw --seed 42
"""

import argparse
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

MONTHS = [1, 2, 3, 4, 5, 6]  # January to June 2026
YEAR = 2026

PRODUCTS = {
    "Cotton Bed Sheet Set": ("Bedroom", 1450),
    "Memory Foam Pillow": ("Bedroom", 650),
    "Ceramic Dinner Set (24 pcs)": ("Kitchen", 2300),
    "Non-stick Frying Pan 28cm": ("Kitchen", 890),
    "Electric Kettle 1.7L": ("Kitchen", 1150),
    "Bath Towel Pack (4)": ("Bathroom", 780),
    "Shower Curtain": ("Bathroom", 320),
    "LED Desk Lamp": ("Living Room", 540),
    "Wall Clock": ("Living Room", 410),
    "Storage Basket Set": ("Living Room", 365),
}

# Clean value -> the messy ways it shows up in the exports
CITY_VARIANTS = {
    "Cairo": ["Cairo", "cairo", " CAIRO ", "Cairo City", "Al Qahirah"],
    "Giza": ["Giza", "GIZA", "El Giza", "giza "],
    "Alexandria": ["Alexandria", "Alex", "alexandria", "ALEXANDRIA"],
    "Mansoura": ["Mansoura", "El Mansoura", "mansoura"],
    "Tanta": ["Tanta", "tanta", "TANTA"],
}
STATUS_VARIANTS = {
    "delivered": ["Delivered", "delivered", "DELIVERED", "Completed"],
    "cancelled": ["Cancelled", "Canceled", "cancelled"],
    "returned": ["Returned", "returned", "Refunded"],
    "pending": ["Pending", "pending", "In Progress"],
}
PAYMENT_VARIANTS = {
    "cash_on_delivery": ["Cash on Delivery", "COD", "cash"],
    "card": ["Card", "Credit Card", "Visa"],
    "mobile_wallet": ["Wallet", "Vodafone Cash", "mobile wallet"],
}

# Each tool exports different column names and formats
SCHEMAS = {
    "webshop": {  # January, February
        "ext": "csv",
        "cols": ["Order ID", "Order Date", "Customer Name", "Phone", "Email", "City",
                 "Product", "Qty", "Unit Price (EGP)", "Payment", "Status"],
        "date_fmt": "%Y-%m-%d",
    },
    "rep_excel": {  # March, April
        "ext": "xlsx",
        "cols": ["order_no", "date", "customer", "mobile", "e-mail", "city",
                 "item", "quantity", "price", "payment_method", "order_status"],
        "date_fmt": "%d/%m/%Y",
    },
    "pos": {  # May, June
        "ext": "csv",
        "cols": ["OrderID", "Date", "Client", "Phone Number", "Email Address", "Governorate",
                 "Product Name", "Units", "Price", "Pay Method", "Status", "Discount"],
        "date_fmt": "%b %d, %Y",
    },
}
MONTH_SCHEMA = {1: "webshop", 2: "webshop", 3: "rep_excel", 4: "rep_excel", 5: "pos", 6: "pos"}


FIRST_NAMES = ["Mohamed", "Ahmed", "Mahmoud", "Omar", "Youssef", "Mostafa", "Karim", "Hassan",
               "Tarek", "Amr", "Mina", "Kirollos", "Fady", "Ibrahim", "Khaled", "Sherif",
               "Mariam", "Nour", "Salma", "Yasmin", "Aya", "Fatma", "Hana", "Dina", "Rana",
               "Mennatallah", "Marina", "Nada", "Habiba", "Sara", "Reem", "Laila"]
LAST_NAMES = ["Hassan", "Ali", "Ibrahim", "Mahmoud", "Abdelrahman", "Saeed", "Fawzy", "Nasr",
              "Gamal", "Soliman", "Farouk", "Mansour", "Adel", "Kamal", "Shehata", "Fayez",
              "Girgis", "Hanna", "Naguib", "Ezzat", "Zaki", "Ramadan", "Fathy", "Samir"]
# How the same first name gets typed differently by different people
SPELLINGS = {"Mohamed": ["Mohammed", "Muhammad"], "Ahmed": ["Ahmad"], "Youssef": ["Yousef", "Yusuf"],
             "Mostafa": ["Moustafa", "Mustafa"], "Mariam": ["Maryam"], "Yasmin": ["Yasmine"],
             "Kirollos": ["Kerollos"], "Amr": ["Amro"]}


def make_customers(n: int) -> list[dict]:
    customers = []
    for _ in range(n):
        first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
        local = f"{first}.{last}".lower().replace(" ", "")
        customers.append({
            "name": f"{first} {last}",
            "phone_digits": random.choice(["10", "11", "12", "15"]) + f"{random.randint(0, 99_999_999):08d}",
            "email": f"{local}{random.randint(1, 99)}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com'])}",
            "city": random.choice(list(CITY_VARIANTS)),
        })
    return customers


def messy_name(name: str) -> str:
    first, last = name.split(" ", 1)
    if first in SPELLINGS and random.random() < 0.25:
        name = f"{random.choice(SPELLINGS[first])} {last}"
    r = random.random()
    if r < 0.15:
        return name.upper()
    if r < 0.30:
        return name.lower()
    if r < 0.40:
        return "  " + name.replace(" ", "   ") + " "
    return name


def messy_phone(digits: str) -> str:
    """digits is the 10-digit local part without the leading 0, e.g. 1012345678."""
    if random.random() < 0.02:
        return random.choice(["12345", "N/A", ""])  # broken values a human typed
    return random.choice([
        "0" + digits,
        "+20" + digits,
        "0020" + digits,
        f"0{digits[:2]} {digits[2:6]} {digits[6:]}",
        digits,
        f"+20 {digits[:3]}-{digits[3:6]}-{digits[6:]}",
    ])


def messy_email(email: str) -> str:
    r = random.random()
    if r < 0.05:
        return ""
    if r < 0.08:
        return email.replace("@", ".")  # invalid
    if r < 0.20:
        return " " + email.upper()
    return email


def messy_order_id(n: int) -> str:
    return random.choice([f"ORD-{n}", f"ord{n}", str(n), f"ORD {n}"])


def messy_quantity(q: int) -> object:
    r = random.random()
    if r < 0.01:
        return 0
    if r < 0.02:
        return -q
    if r < 0.12:
        return f"{q} pcs"
    return q


def messy_price(price: float, schema: str) -> object:
    if random.random() < 0.01:
        return None
    if schema == "rep_excel":
        return f"{price:,.2f} EGP"
    if schema == "pos" and random.random() < 0.3:
        return f"EGP {price:,.0f}"
    return price


def build_orders(customers: list[dict], orders_per_month: int) -> list[dict]:
    orders, next_id = [], 10001
    for m in MONTHS:
        start = date(YEAR, m, 1)
        end = date(YEAR + (m == 12), (m % 12) + 1, 1) - timedelta(days=1)
        for _ in range(orders_per_month + random.randint(-40, 40)):
            product = random.choice(list(PRODUCTS))
            category, base = PRODUCTS[product]
            orders.append({
                "order_num": next_id,
                "date": start + timedelta(days=random.randint(0, (end - start).days)),
                "month": m,
                "customer": random.choice(customers),
                "product": product,
                "quantity": random.choices([1, 2, 3, 4], weights=[60, 25, 10, 5])[0],
                "unit_price": float(base + random.choice([-50, 0, 0, 0, 100])),
                "status": random.choices(list(STATUS_VARIANTS), weights=[78, 8, 5, 9])[0],
                "payment": random.choices(list(PAYMENT_VARIANTS), weights=[55, 30, 15])[0],
            })
            next_id += 1
    return orders

def messy_discount() -> object:
    """Most orders have no discount; the rest are written in different ways."""
    return random.choice(["", "", "", "0", "50", "EGP 100", "150 EGP", "-20"])

def to_row(o: dict, schema: str, reexport: bool = False) -> list:
    c = o["customer"]
    order_status = o["status"]
    if reexport and order_status == "pending" and random.random() < 0.6:
        order_status = "delivered"  # the later export carries the newer status
    row = [
        messy_order_id(o["order_num"]),
        o["date"].strftime(SCHEMAS[schema]["date_fmt"]),
        messy_name(c["name"]),
        messy_phone(c["phone_digits"]),
        messy_email(c["email"]),
        random.choice(CITY_VARIANTS[c["city"]]),
        o["product"],
        messy_quantity(o["quantity"]),
        messy_price(o["unit_price"], schema),
        random.choice(PAYMENT_VARIANTS[o["payment"]]),
        random.choice(STATUS_VARIANTS[order_status]),
    ]
    if schema == "pos":
        row.append(messy_discount())
    return row

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="data/raw", help="folder for the messy exports")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--customers", type=int, default=350)
    ap.add_argument("--orders-per-month", type=int, default=650)
    args = ap.parse_args()

    random.seed(args.seed)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    orders = build_orders(make_customers(args.customers), args.orders_per_month)

    for m in MONTHS:
        schema = MONTH_SCHEMA[m]
        rows = [to_row(o, schema) for o in orders if o["month"] == m]

        # Re-export problem: the last 3 days of the previous month show up again,
        # formatted the way THIS month's tool formats them.
        if m > 1:
            prev = [o for o in orders if o["month"] == m - 1 and o["date"].day >= 26]
            rows += [to_row(o, schema, reexport=True) for o in prev]

        # Exact duplicate rows (someone pasted a block twice)
        rows += random.sample(rows, k=max(1, len(rows) * 3 // 100))

        # Fully empty rows
        rows += [[None] * len(SCHEMAS[schema]["cols"]) for _ in range(len(rows) // 100)]

        random.shuffle(rows)
        df = pd.DataFrame(rows, columns=SCHEMAS[schema]["cols"])
        path = out / f"orders_{YEAR}_{m:02d}.{SCHEMAS[schema]['ext']}"
        if SCHEMAS[schema]["ext"] == "xlsx":
            df.to_excel(path, index=False)
        else:
            df.to_csv(path, index=False)
        print(f"wrote {path} ({len(df):,} rows, schema: {schema})")


if __name__ == "__main__":
    main()
