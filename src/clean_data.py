
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "raw" / "online_retail_ii.xlsx"
OUTPUT_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"

ALIASES = {
    "Invoice": "invoice",
    "InvoiceNo": "invoice",
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "quantity",
    "InvoiceDate": "invoice_date",
    "Price": "unit_price",
    "Customer ID": "customer_id",
    "Country": "country",
}

REQUIRED = [
    "invoice", "stock_code", "description", "quantity",
    "invoice_date", "unit_price", "customer_id", "country",
]


def main():
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Missing source file: {RAW_FILE}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    frames = []

    for sheet in pd.ExcelFile(RAW_FILE).sheet_names:
        df = pd.read_excel(RAW_FILE, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]
        df = df.rename(columns=ALIASES)

        missing = set(REQUIRED) - set(df.columns)
        if missing:
            raise ValueError(f"{sheet}: missing columns {missing}")

        df["source_sheet"] = sheet
        frames.append(df)

    data = pd.concat(frames, ignore_index=True)
    source_rows = len(data)

    # Normalize identifiers and types.
    for col in ["invoice", "stock_code", "customer_id",
                "country", "description"]:
        data[col] = data[col].astype("string").str.strip()

    data["quantity"] = pd.to_numeric(
        data["quantity"], errors="coerce"
    )
    data["unit_price"] = pd.to_numeric(
        data["unit_price"], errors="coerce"
    )
    data["invoice_date"] = pd.to_datetime(
        data["invoice_date"], errors="coerce"
    )

    invoice_text = data["invoice"].str.upper()
    data["is_cancellation"] = invoice_text.str.startswith(
        "C", na=False
    )
    data["is_negative_quantity"] = data["quantity"] < 0
    data["is_zero_price"] = data["unit_price"] == 0
    data["is_exact_duplicate"] = data.duplicated(keep=False)

    # Required fields for the initial transaction classification.
    valid_base = (
        data["invoice"].notna()
        & data["stock_code"].notna()
        & data["invoice_date"].notna()
        & data["quantity"].notna()
        & data["unit_price"].notna()
        & data["country"].notna()
    )

    cancellation = data["is_cancellation"]
    negative_quantity = data["is_negative_quantity"]
    positive_quantity = data["quantity"] > 0
    nonnegative_price = data["unit_price"] >= 0
    negative_price = data["unit_price"] < 0

    # Mutually exclusive classifications.
    sales_mask = (
        valid_base
        & positive_quantity
        & ~cancellation
        & nonnegative_price
    )

    returns_mask = (
        valid_base
        & (cancellation | negative_quantity)
        & nonnegative_price
    )

    # Negative-price entries are isolated for review rather than
    # treated as product sales or silently discarded.
    adjustment_mask = valid_base & negative_price

    classified = sales_mask | returns_mask | adjustment_mask
    rejected_mask = ~classified

    sales = data.loc[sales_mask].copy()
    returns = data.loc[returns_mask].copy()
    adjustments = data.loc[adjustment_mask].copy()
    rejected = data.loc[rejected_mask].copy()

    sales["gross_line_value"] = (
        sales["quantity"] * sales["unit_price"]
    )
    returns["signed_line_value"] = (
        returns["quantity"] * returns["unit_price"]
    )
    adjustments["signed_adjustment_value"] = (
        adjustments["quantity"] * adjustments["unit_price"]
    )

    outputs = {
        "sales.parquet": sales,
        "returns_and_cancellations.parquet": returns,
        "financial_adjustments.parquet": adjustments,
        "rejected_records.parquet": rejected,
    }

    for filename, frame in outputs.items():
        frame.to_parquet(
            OUTPUT_DIR / filename,
            index=False,
            compression="snappy",
        )

    classified_rows = (
        len(sales) + len(returns)
        + len(adjustments) + len(rejected)
    )

    report = [
        "RETAIL DATA CLEANING SUMMARY",
        "=" * 55,
        f"Source rows: {source_rows:,}",
        f"Sales rows: {len(sales):,}",
        f"Returns/cancellation rows: {len(returns):,}",
        f"Financial adjustment rows: {len(adjustments):,}",
        f"Rejected rows: {len(rejected):,}",
        f"Classified rows total: {classified_rows:,}",
        f"Row counts reconcile: {classified_rows == source_rows}",
        "",
        f"Sales with missing customer IDs: "
        f"{sales['customer_id'].isna().sum():,}",
        f"Zero-price sales: {sales['is_zero_price'].sum():,}",
        f"Source rows participating in duplicate groups: "
        f"{data['is_exact_duplicate'].sum():,}",
        f"Extra duplicate occurrences: "
        f"{data.duplicated().sum():,}",
        f"Cancellations in return output: "
        f"{returns['is_cancellation'].sum():,}",
        f"Negative quantities in return output: "
        f"{returns['is_negative_quantity'].sum():,}",
        "",
        "Review duplicate rows before removing them.",
        "Returns and cancellations remain separate from sales.",
        "Financial adjustments are not ordinary product sales.",
        "Net sales requires a documented return/cancellation policy.",
    ]

    text = "\n".join(report)
    (REPORT_DIR / "cleaning_summary.txt").write_text(
        text, encoding="utf-8"
    )
    print(text)


if __name__ == "__main__":
    main()
