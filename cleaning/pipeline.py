"""
The cleaning pipeline: load -> standardize -> validate -> deduplicate -> build outputs.

Each step returns new DataFrames and adds to a `stats` dict, so the data quality
report can explain exactly what happened to every row.
"""

import logging
from pathlib import Path

import pandas as pd

from cleaning import normalize as nz

log = logging.getLogger(__name__)

REQUIRED = ["order_id", "order_date", "product", "quantity", "unit_price", "status"]
CLEAN_COLUMNS = ["order_id", "order_date", "customer_name", "phone", "email", "city", "product",
                 "quantity", "unit_price", "line_total", "payment_method", "status", "source_file"]

# column -> function that cleans one value
CLEANERS = {
    "order_id": nz.order_id, "order_date": nz.order_date, "customer_name": nz.person_name,
    "phone": nz.phone, "email": nz.email, "city": nz.city, "product": nz._text,
    "quantity": nz.quantity, "unit_price": nz.price, "payment_method": nz.payment_method,
    "status": nz.status,
}


def load_exports(input_dir: Path) -> tuple[pd.DataFrame, list[dict]]:
    """Read every CSV/XLSX export as text (so phone numbers keep their leading 0)."""
    files = sorted(p for p in input_dir.iterdir() if p.suffix.lower() in {".csv", ".xlsx"})
    if not files:
        raise FileNotFoundError(f"No .csv or .xlsx files found in {input_dir}")

    frames, file_info = [], []
    for order, path in enumerate(files):
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path, dtype=str, keep_default_na=False)
        else:
            df = pd.read_excel(path, dtype=str, keep_default_na=False)

        unknown = [c for c in df.columns if nz.column_name(c) is None]
        if unknown:
            raise ValueError(f"{path.name}: unknown columns {unknown}. Add them to COLUMN_MAP.")

        df = df.rename(columns={c: nz.column_name(c) for c in df.columns})
        df["source_file"] = path.name
        df["file_order"] = order
        df["source_row"] = range(2, len(df) + 2)  # row number as seen in Excel (header = row 1)
        frames.append(df)
        file_info.append({"file": path.name, "rows": len(df), "columns": len(df.columns) - 3})
        log.info("loaded %s: %d rows", path.name, len(df))

    return pd.concat(frames, ignore_index=True), file_info


def drop_empty_rows(raw: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    data_cols = [c for c in raw.columns if c not in {"source_file", "file_order", "source_row"}]
    is_empty = raw[data_cols].apply(lambda col: col.map(lambda v: nz._text(v) is None)).all(axis=1)
    return raw[~is_empty].copy(), int(is_empty.sum())


NUMERIC = {"quantity", "unit_price"}


def _is_plain_number(s) -> bool:
    try:
        float(s)
        return True
    except (TypeError, ValueError):
        return False


def standardize(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Apply every cleaner and count how many values each one changed or blanked."""
    clean = raw[["source_file", "file_order", "source_row"]].copy()
    changes = {}
    for col, fn in CLEANERS.items():
        before = raw[col].map(nz._text)
        after = raw[col].map(fn).astype(object)
        had_value = before.notna()
        is_clean = after.notna()
        if col in NUMERIC:
            # '2 pcs' or '1,450.00 EGP' needed fixing; '2' or '1450.0' did not
            changed = ~before.map(_is_plain_number)
        else:
            changed = before != after.map(lambda v: None if pd.isna(v) else str(v))
        changes[col] = {
            "standardized": int((had_value & is_clean & changed).sum()),
            "unusable": int((had_value & ~is_clean).sum()),
            "missing": int((~had_value).sum()),
        }
        clean[col] = after
    clean["quantity"] = clean["quantity"].astype("Int64")
    clean["unit_price"] = clean["unit_price"].astype("Float64")
    clean["raw_city"] = raw["city"].map(nz._text)
    return clean, changes


def split_valid(clean: pd.DataFrame, raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Rows missing any required field go to the rejected log with the reason."""
    reasons = pd.Series("", index=clean.index)
    for col in REQUIRED:
        bad = clean[col].isna()
        reasons[bad] = reasons[bad] + f"invalid or missing {col}; "
    rejected_mask = reasons != ""
    rejected = raw.loc[rejected_mask].copy()
    rejected["reject_reason"] = reasons[rejected_mask].str.rstrip("; ")
    rejected["order_id_clean"] = clean.loc[rejected_mask, "order_id"]
    return clean.loc[~rejected_mask].copy(), rejected


def deduplicate(valid: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    One row per order. When the same order appears in several exports, keep the
    copy from the most recent file, because it carries the latest status.
    """
    key_cols = ["order_date", "product", "quantity", "unit_price", "status"]
    same_file = valid.duplicated(["order_id", "source_file"], keep="first")
    within_file = int(same_file.sum())
    deduped_files = valid[~same_file]

    across = int(deduped_files.duplicated("order_id", keep="last").sum())
    conflicts = int(deduped_files.groupby("order_id")[key_cols].nunique().gt(1).any(axis=1).sum())

    final = (deduped_files.sort_values(["file_order", "source_row"])
             .drop_duplicates("order_id", keep="last")
             .sort_values(["order_date", "order_id"]))
    return final, {"within_file": within_file, "across_files": across, "conflicting_orders": conflicts}


def build_orders(final: pd.DataFrame) -> pd.DataFrame:
    orders = final.copy()
    orders["line_total"] = (orders["quantity"] * orders["unit_price"]).round(2)
    return orders[CLEAN_COLUMNS].reset_index(drop=True)


def build_customers(orders: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """One row per customer, matched by phone number (names are spelled too many ways)."""
    with_phone = orders[orders["phone"].notna()].copy()
    with_phone["delivered_value"] = with_phone["line_total"].where(with_phone["status"] == "delivered", 0)

    def most_common(s: pd.Series):
        s = s.dropna()
        return s.mode().iloc[0] if not s.empty else None

    customers = with_phone.groupby("phone").agg(
        customer_name=("customer_name", most_common),
        name_spellings=("customer_name", "nunique"),
        email=("email", most_common),
        city=("city", most_common),
        orders=("order_id", "count"),
        delivered_revenue_egp=("delivered_value", "sum"),
        first_order=("order_date", "min"),
        last_order=("order_date", "max"),
    ).reset_index()
    customers = customers.sort_values("delivered_revenue_egp", ascending=False).reset_index(drop=True)
    merged_spellings = int((customers["name_spellings"] > 1).sum())
    return customers, merged_spellings


def run(input_dir: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    raw, file_info = load_exports(input_dir)
    total_rows = len(raw)
    raw, empty_rows = drop_empty_rows(raw)
    clean, changes = standardize(raw)
    valid, rejected = split_valid(clean, raw)
    final, dupes = deduplicate(valid)
    orders = build_orders(final)
    customers, merged_spellings = build_customers(orders)

    kept_ids = set(orders["order_id"])
    rejected["order_kept_from_other_copy"] = rejected["order_id_clean"].isin(kept_ids)

    orders.to_csv(output_dir / "orders_clean.csv", index=False)
    customers.to_csv(output_dir / "customers.csv", index=False)
    rejected.drop(columns=["file_order"]).to_csv(output_dir / "rejected_rows.csv", index=False)

    unmapped_cities = sorted(clean.loc[clean["city"].isna() & clean["raw_city"].notna(), "raw_city"].unique())

    return {
        "files": file_info,
        "rows_in": total_rows,
        "empty_rows": empty_rows,
        "rejected_rows": len(rejected),
        "rejected_recovered": int(rejected["order_kept_from_other_copy"].sum()),
        "reject_reasons": rejected["reject_reason"].value_counts().to_dict(),
        "duplicates": dupes,
        "orders_out": len(orders),
        "customers_out": len(customers),
        "merged_name_spellings": merged_spellings,
        "orders_without_valid_phone": int(orders["phone"].isna().sum()),
        "orders_without_valid_email": int(orders["email"].isna().sum()),
        "unmapped_cities": unmapped_cities,
        "changes": changes,
        "date_range": [str(orders["order_date"].min()), str(orders["order_date"].max())],
        "delivered_revenue_egp": float(orders.loc[orders["status"] == "delivered", "line_total"].sum()),
        "status_counts": orders["status"].value_counts().to_dict(),
    }
