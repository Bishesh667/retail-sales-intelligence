
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "online_retail_II.xlsx"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"


def main():
    REPORTS.mkdir(exist_ok=True)

    # Load the original workbook to audit the classification.
    frames = []
    for sheet in pd.ExcelFile(RAW).sheet_names:
        df = pd.read_excel(RAW, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]
        df = df.rename(columns={
            "Invoice": "invoice",
            "InvoiceNo": "invoice",
            "StockCode": "stock_code",
            "Quantity": "quantity",
            "InvoiceDate": "invoice_date",
            "Price": "unit_price",
            "Customer ID": "customer_id",
        })
        df["source_sheet"] = sheet
        frames.append(df)

    raw = pd.concat(frames, ignore_index=True)

    raw["invoice"] = raw["invoice"].astype("string").str.strip()
    raw["quantity"] = pd.to_numeric(raw["quantity"], errors="coerce")
    raw["unit_price"] = pd.to_numeric(
        raw["unit_price"], errors="coerce"
    )
    raw["invoice_date"] = pd.to_datetime(
        raw["invoice_date"], errors="coerce"
    )

    cancellation = raw["invoice"].str.upper().str.startswith(
        "C", na=False
    )
    negative_quantity = raw["quantity"] < 0
    zero_quantity = raw["quantity"] == 0

    # Count extra occurrences separately from all duplicate occurrences.
    duplicate_all = raw.duplicated(keep=False)
    duplicate_extra = raw.duplicated(keep="first")

    rejected = pd.read_parquet(
        PROCESSED / "rejected_records.parquet"
    )
    sales = pd.read_parquet(PROCESSED / "sales.parquet")
    returns = pd.read_parquet(
        PROCESSED / "returns_and_cancellations.parquet"
    )

    print("\n--- SOURCE VALIDATION ---")
    print(f"Raw rows: {len(raw):,}")
    print(f"Rows with cancellation invoice: {cancellation.sum():,}")
    print(f"Rows with negative quantity: {negative_quantity.sum():,}")
    print(f"Rows with zero quantity: {zero_quantity.sum():,}")
    print(f"Cancellation AND negative quantity: "
          f"{(cancellation & negative_quantity).sum():,}")
    print(f"Rows participating in duplicate groups: "
          f"{duplicate_all.sum():,}")
    print(f"Extra duplicate occurrences: {duplicate_extra.sum():,}")

    print("\n--- REJECTED RECORDS ---")
    if rejected.empty:
        print("No rejected records.")
    else:
        print(rejected.to_string(index=False))

    print("\n--- OUTPUT VALIDATION ---")
    print(f"Sales rows: {len(sales):,}")
    print(f"Return/cancellation rows: {len(returns):,}")
    print(f"Rejected rows: {len(rejected):,}")
    print(f"Total classified rows: "
          f"{len(sales) + len(returns) + len(rejected):,}")
    print(f"Row counts reconcile: "
          f"{len(sales) + len(returns) + len(rejected) == len(raw)}")

    # Check whether sales and return outputs contain overlapping
    # source records. This key is diagnostic, not a guaranteed unique ID.
    print("\n--- OUTPUT CHECKS ---")
    print(f"Sales with missing invoice: "
          f"{sales['invoice'].isna().sum():,}")
    print(f"Sales with negative quantity: "
          f"{(sales['quantity'] < 0).sum():,}")
    print(f"Returns with negative quantity: "
          f"{(returns['quantity'] < 0).sum():,}")
    print(f"Returns with cancellation invoice: "
          f"{returns['invoice'].astype('string').str.upper().str.startswith('C', na=False).sum():,}")

    report = [
        f"Raw rows: {len(raw)}",
        f"Duplicate-group rows: {duplicate_all.sum()}",
        f"Extra duplicate occurrences: {duplicate_extra.sum()}",
        f"Cancellation AND negative quantity: "
        f"{(cancellation & negative_quantity).sum()}",
        f"Rejected rows: {len(rejected)}",
        f"Output row counts reconcile: "
        f"{len(sales) + len(returns) + len(rejected) == len(raw)}",
    ]
    (REPORTS / "validation_summary.txt").write_text(
        "\n".join(report), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
