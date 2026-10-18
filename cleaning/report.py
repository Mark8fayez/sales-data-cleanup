"""Write the data quality report as Markdown (for people) and JSON (for machines)."""

import json
from datetime import datetime
from pathlib import Path

LABELS = {
    "order_id": "Order ID", "order_date": "Order date", "customer_name": "Customer name",
    "phone": "Phone", "email": "Email", "city": "City", "product": "Product",
    "quantity": "Quantity", "unit_price": "Unit price", "payment_method": "Payment method",
    "status": "Status", "discount": "Discount",
}


def write(stats: dict, report_dir: Path) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "summary.json").write_text(json.dumps(stats, indent=2, default=str))

    d = stats["duplicates"]
    removed_dupes = d["within_file"] + d["across_files"]
    lines = [
        "# Data Quality Report",
        "",
        f"Generated {datetime.now():%Y-%m-%d %H:%M} by `clean.py`.",
        "",
        "## Summary",
        "",
        f"- **{stats['rows_in']:,}** raw rows from **{len(stats['files'])}** files became "
        f"**{stats['orders_out']:,}** clean, unique orders and **{stats['customers_out']:,}** customers.",
        f"- **{removed_dupes:,}** duplicate rows removed "
        f"({d['within_file']:,} repeated inside a file, {d['across_files']:,} re-exported in a later file).",
        f"- **{stats['rejected_rows']:,}** rows rejected and logged in `rejected_rows.csv`; "
        f"{stats['rejected_recovered']:,} of those orders were still kept from a valid copy in another file.",
        f"- **{stats['merged_name_spellings']:,}** customers had their name spelled more than one way "
        "and were merged by phone number.",
        f"- Orders cover {stats['date_range'][0]} to {stats['date_range'][1]}; delivered revenue "
        f"**EGP {stats['delivered_revenue_egp']:,.0f}**.",
        "",
        "## Row flow",
        "",
        "| Step | Rows |",
        "| --- | ---: |",
        f"| Raw rows in all files | {stats['rows_in']:,} |",
        f"| Fully empty rows dropped | -{stats['empty_rows']:,} |",
        f"| Rows rejected (missing or invalid required field) | -{stats['rejected_rows']:,} |",
        f"| Duplicates inside the same file | -{d['within_file']:,} |",
        f"| Same order re-exported in a later file | -{d['across_files']:,} |",
        f"| **Clean unique orders** | **{stats['orders_out']:,}** |",
        "",
        "## Input files",
        "",
        "| File | Rows | Columns |",
        "| --- | ---: | ---: |",
        *[f"| `{f['file']}` | {f['rows']:,} | {f['columns']} |" for f in stats["files"]],
        "",
        "## What was fixed, per column",
        "",
        "*Standardized* = value was usable but written in a non-standard way (case, spacing, "
        "format, synonym). *Unusable* = value present but invalid, set to empty.",
        "",
        "| Column | Standardized | Unusable | Missing |",
        "| --- | ---: | ---: | ---: |",
        *[f"| {LABELS[c]} | {v['standardized']:,} | {v['unusable']:,} | {v['missing']:,} |"
          for c, v in stats["changes"].items()],
        "",
        "## Rejection reasons",
        "",
        "| Reason | Rows |",
        "| --- | ---: |",
        *[f"| {r} | {n:,} |" for r, n in stats["reject_reasons"].items()],
        "",
        "## Still needs a human",
        "",
        f"- {stats['orders_without_valid_phone']:,} kept orders have no valid phone number.",
        f"- {stats['orders_without_valid_email']:,} kept orders have no valid email.",
        f"- {d['conflicting_orders']:,} orders had copies that disagreed on a key field; "
        "the copy from the most recent file was kept.",
        f"- Unmapped city spellings: {', '.join(stats['unmapped_cities']) or 'none'}.",
        "",
    ]
    path = report_dir / "data_quality_report.md"
    path.write_text("\n".join(lines))
    return path
