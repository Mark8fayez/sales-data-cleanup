"""
Draw docs/before_after.png: one order exported twice in different formats (before)
and the single clean row it became (after). Run after clean.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # so `cleaning` imports from the repo root

import matplotlib.pyplot as plt
import pandas as pd

from cleaning import normalize as nz
from cleaning.pipeline import load_exports, drop_empty_rows

COLS = ["order_id", "order_date", "customer_name", "phone", "city", "quantity", "unit_price", "status",
        "source_file"]
HEAD = ["Order ID", "Date", "Customer", "Phone", "City", "Qty", "Price", "Status", "File"]


def pick_examples(raw: pd.DataFrame, clean: pd.DataFrame, n: int = 3) -> list[str]:
    """Orders that appear in two different files and look different each time."""
    raw = raw.assign(oid=raw["order_id"].map(nz.order_id))
    multi = raw.groupby("oid")["source_file"].nunique()
    candidates = [o for o in multi[multi > 1].index if o in set(clean["order_id"])]
    scored = []
    for oid in candidates:
        rows = raw[raw["oid"] == oid]
        if rows["order_date"].nunique() < 2:  # want two different export formats
            continue
        messy = sum(rows[c].nunique() for c in ["order_id", "customer_name", "phone", "city", "status"])
        scored.append((messy, oid))
    return [oid for _, oid in sorted(scored, reverse=True)[:n]]


def draw_table(ax, rows, colors, title):
    ax.axis("off")
    ax.set_title(title, loc="left", fontsize=13, fontweight="bold", pad=8)
    t = ax.table(cellText=rows, colLabels=HEAD, cellLoc="left", loc="upper left",
                 cellColours=colors, colColours=["#e6eef8"] * len(HEAD))
    t.auto_set_font_size(False)
    t.set_fontsize(9)
    t.scale(1, 1.6)
    t.auto_set_column_width(list(range(len(HEAD))))


def main() -> None:
    raw, _ = load_exports(Path("data/raw"))
    raw, _ = drop_empty_rows(raw)
    clean = pd.read_csv("data/clean/orders_clean.csv", dtype=str)
    examples = pick_examples(raw, clean)

    shades = ["#ffffff", "#f5f6f8"]
    before, before_colors, after, after_colors = [], [], [], []
    for i, oid in enumerate(examples):
        for _, r in raw[raw["order_id"].map(nz.order_id) == oid].iterrows():
            before.append([str(r[c]) for c in COLS])
            before_colors.append([shades[i % 2]] * len(COLS))
        c = clean[clean["order_id"] == oid].iloc[0]
        cells = [str(c[k]) for k in COLS]
        cells[COLS.index("unit_price")] = f"{float(c['unit_price']):,.2f}"
        after.append(cells)
        after_colors.append([shades[i % 2]] * len(COLS))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.5, 0.3 * (len(before) + len(after) + 5)),
                                   gridspec_kw={"height_ratios": [len(before) + 2, len(after) + 2]})
    draw_table(ax1, before, before_colors, f"Before: {len(before)} raw rows from different monthly exports")
    draw_table(ax2, after, after_colors, f"After: {len(after)} clean orders")
    fig.tight_layout()
    Path("docs").mkdir(exist_ok=True)
    fig.savefig("docs/before_after.png", dpi=160, bbox_inches="tight", facecolor="white")
    print("wrote docs/before_after.png")


if __name__ == "__main__":
    main()
