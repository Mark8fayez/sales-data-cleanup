# Data Quality Report

Generated 2026-10-18 21:10 by `clean.py`.

## Summary

- **4,698** raw rows from **6** files became **3,855** clean, unique orders and **350** customers.
- **667** duplicate rows removed (131 repeated inside a file, 536 re-exported in a later file).
- **133** rows rejected and logged in `rejected_rows.csv`; 34 of those orders were still kept from a valid copy in another file.
- **70** customers had their name spelled more than one way and were merged by phone number.
- Orders cover 2026-01-01 to 2026-06-30; delivered revenue **EGP 4,331,820**.

## Row flow

| Step | Rows |
| --- | ---: |
| Raw rows in all files | 4,698 |
| Fully empty rows dropped | -43 |
| Rows rejected (missing or invalid required field) | -133 |
| Duplicates inside the same file | -131 |
| Same order re-exported in a later file | -536 |
| **Clean unique orders** | **3,855** |

## Input files

| File | Rows | Columns |
| --- | ---: | ---: |
| `orders_2026_01.csv` | 713 | 11 |
| `orders_2026_02.csv` | 847 | 11 |
| `orders_2026_03.xlsx` | 777 | 11 |
| `orders_2026_04.xlsx` | 792 | 11 |
| `orders_2026_05.csv` | 754 | 12 |
| `orders_2026_06.csv` | 815 | 12 |

## What was fixed, per column

*Standardized* = value was usable but written in a non-standard way (case, spacing, format, synonym). *Unusable* = value present but invalid, set to empty.

| Column | Standardized | Unusable | Missing |
| --- | ---: | ---: | ---: |
| Order ID | 3,513 | 0 | 0 |
| Order date | 3,110 | 0 | 0 |
| Customer name | 1,928 | 0 | 0 |
| Phone | 3,777 | 29 | 86 |
| Email | 575 | 129 | 249 |
| City | 3,436 | 0 | 0 |
| Product | 0 | 0 | 0 |
| Quantity | 464 | 89 | 0 |
| Unit price | 2,006 | 0 | 48 |
| Payment method | 4,655 | 0 | 0 |
| Status | 3,451 | 0 | 0 |
| Discount | 407 | 188 | 3,699 |

## Rejection reasons

| Reason | Rows |
| --- | ---: |
| invalid or missing quantity | 85 |
| invalid or missing unit_price | 44 |
| invalid or missing quantity; invalid or missing unit_price | 4 |

## Still needs a human

- 98 kept orders have no valid phone number.
- 302 kept orders have no valid email.
- 31 orders had copies that disagreed on a key field; the copy from the most recent file was kept.
- Unmapped city spellings: none.
