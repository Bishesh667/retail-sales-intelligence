
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "raw" / "online_retail_ii.xlsx"
REPORT_DIR = PROJECT_ROOT / "reports"
REPORT_FILE = REPORT_DIR / "raw_profile.txt"


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_FILE}\n"
            "Download online_retail_II.xlsx into data/raw/ first."
        )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = []

    report.append("RETAIL SALES INTELLIGENCE")
    report.append("RAW DATA PROFILING REPORT")
    report.append("=" * 60)
    report.append(f"File: {DATA_FILE.name}")
    report.append(f"Size: {DATA_FILE.stat().st_size / (1024**2):.2f} MB")

    # Read workbook metadata without loading all rows.
    workbook = pd.ExcelFile(DATA_FILE)
    report.append(f"\nWorkbook sheets: {workbook.sheet_names}")

    total_rows = 0

    for sheet in workbook.sheet_names:
        report.append("\n" + "=" * 60)
        report.append(f"SHEET: {sheet}")
        report.append("=" * 60)

        df = pd.read_excel(workbook, sheet_name=sheet)
        total_rows += len(df)

        # Normalize column labels for consistent inspection.
        df.columns = [str(col).strip() for col in df.columns]

        report.append(f"Rows: {len(df):,}")
        report.append(f"Columns: {len(df.columns)}")
        report.append(f"Column names: {list(df.columns)}")
        report.append(f"Exact duplicate rows: {df.duplicated().sum():,}")

        report.append("\nMissing values:")
        missing = df.isna().sum()

        for column, count in missing.items():
            percentage = count / len(df) * 100 if len(df) else 0
            report.append(
                f"  {column}: {count:,} ({percentage:.2f}%)"
            )

        # Map the source's column names to standard names.
        aliases = {
            "Invoice": "invoice",
            "InvoiceNo": "invoice",
            "Invoice No": "invoice",
            "StockCode": "stock_code",
            "Description": "description",
            "Quantity": "quantity",
            "InvoiceDate": "invoice_date",
            "Price": "unit_price",
            "UnitPrice": "unit_price",
            "Customer ID": "customer_id",
            "CustomerID": "customer_id",
            "Country": "country",
        }

        normalized = {
            column: aliases.get(column, column)
            for column in df.columns
        }
        df = df.rename(columns=normalized)

        if "invoice" in df.columns:
            invoice = df["invoice"].astype("string").str.strip()
            cancellations = invoice.str.upper().str.startswith(
                "C", na=False
            )
            report.append(
                f"\nCancellation invoice rows: {cancellations.sum():,}"
            )

        if "quantity" in df.columns:
            quantity = pd.to_numeric(
                df["quantity"], errors="coerce"
            )
            report.append(
                f"Negative quantity rows: {(quantity < 0).sum():,}"
            )

        if "unit_price" in df.columns:
            price = pd.to_numeric(
                df["unit_price"], errors="coerce"
            )
            report.append(
                f"Zero price rows: {(price == 0).sum():,}"
            )
            report.append(
                f"Negative price rows: {(price < 0).sum():,}"
            )

        if "invoice_date" in df.columns:
            dates = pd.to_datetime(
                df["invoice_date"], errors="coerce"
            )
            report.append(f"Earliest date: {dates.min()}")
            report.append(f"Latest date: {dates.max()}")
            report.append(
                f"Invalid or missing dates: {dates.isna().sum():,}"
            )

        if "country" in df.columns:
            report.append(
                f"Unique countries: {df['country'].nunique(dropna=True):,}"
            )

        if "stock_code" in df.columns:
            report.append(
                f"Unique stock codes: {df['stock_code'].nunique(dropna=True):,}"
            )

        if "customer_id" in df.columns:
            report.append(
                f"Unique non-missing customers: "
                f"{df['customer_id'].nunique(dropna=True):,}"
            )

        # Release this sheet before processing the next one.
        del df

    report.append("\n" + "=" * 60)
    report.append(f"TOTAL ROWS ACROSS SHEETS: {total_rows:,}")
    report.append("=" * 60)

    REPORT_FILE.write_text("\n".join(report), encoding="utf-8")

    print("\n".join(report))
    print(f"\nReport saved to: {REPORT_FILE}")


if __name__ == "__main__":
    main()
