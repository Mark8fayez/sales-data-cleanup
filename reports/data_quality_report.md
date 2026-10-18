# Data Quality Report

Generated 2026-10-18 00:59 by `clean.py`.

## Summary

- **4,698** raw rows from **6** files became **3,855** clean, unique orders and **350** customers.
- **664** duplicate rows removed (130 repeated inside a file, 534 re-exported in a later file).
- **136** rows rejected and logged in `rejected_rows.csv`; 36 of those orders were still kept from a valid copy in another file.
- **66** customers had their name spelled more than one way and were merged by phone number.
- Orders cover 2026-01-01 to 2026-06-30; delivered revenue **EGP 4,347,915**.

## Row flow

| Step | Rows |
| --- | ---: |
| Raw rows in all files | 4,698 |
| Fully empty rows dropped | -43 |
| Rows rejected (missing or invalid required field) | -136 |
| Duplicates inside the same file | -130 |
| Same order re-exported in a later file | -534 |
| **Clean unique orders** | **3,855** |

## Input files

| File | Rows | Columns |
| --- | ---: | ---: |
| `orders_2026_01.csv` | 713 | 11 |
| `orders_2026_02.csv` | 847 | 11 |
| `orders_2026_03.xlsx` | 777 | 11 |
| `orders_2026_04.xlsx` | 792 | 11 |
| `orders_2026_05.csv` | 754 | 11 |
| `orders_2026_06.csv` | 815 | 11 |

## What was fixed, per column

*Standardized* = value was usable but written in a non-standard way (case, spacing, format, synonym). *Unusable* = value present but invalid, set to empty.

| Column | Standardized | Unusable | Missing |
| --- | ---: | ---: | ---: |
| Order ID | 3,514 | 0 | 0 |
| Order date | 3,110 | 0 | 0 |
| Customer name | 1,893 | 0 | 0 |
| Phone | 3,771 | 34 | 75 |
| Email | 551 | 137 | 253 |
| City | 3,427 | 0 | 0 |
| Product | 0 | 0 | 0 |
| Quantity | 475 | 96 | 0 |
| Unit price | 1,998 | 0 | 43 |
| Payment method | 4,655 | 0 | 0 |
| Status | 3,471 | 0 | 0 |

## Rejection reasons

| Reason | Rows |
| --- | ---: |
| invalid or missing quantity | 93 |
| invalid or missing unit_price | 40 |
| invalid or missing quantity; invalid or missing unit_price | 3 |

## Still needs a human

- 91 kept orders have no valid phone number.
- 310 kept orders have no valid email.
- 28 orders had copies that disagreed on a key field; the copy from the most recent file was kept.
- Unmapped city spellings: none.
