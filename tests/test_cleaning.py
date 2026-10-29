
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "raw" / "online_retail_II.xlsx"
OUT = ROOT / "data" / "processed"


def test_source_row_count():
    raw = pd.concat(
        [
            pd.read_excel(RAW_FILE, sheet_name=sheet)
            for sheet in pd.ExcelFile(RAW_FILE).sheet_names
        ],
        ignore_index=True,
    )
    assert len(raw) == 1_067_371


def test_output_row_counts_reconcile():
    files = [
        "sales.parquet",
        "returns_and_cancellations.parquet",
        "financial_adjustments.parquet",
        "rejected_records.parquet",
    ]
    total = sum(
        len(pd.read_parquet(OUT / filename))
        for filename in files
    )
    assert total == 1_067_371


def test_sales_have_positive_quantities():
    sales = pd.read_parquet(OUT / "sales.parquet")
    assert (sales["quantity"] > 0).all()
    assert (~sales["is_cancellation"]).all()
    assert (sales["unit_price"] >= 0).all()


def test_returns_or_cancellations_are_flagged():
    returns = pd.read_parquet(
        OUT / "returns_and_cancellations.parquet"
    )
    assert (
        returns["is_cancellation"]
        | returns["is_negative_quantity"]
    ).all()
    assert (returns["unit_price"] >= 0).all()


def test_adjustments_have_negative_prices():
    adjustments = pd.read_parquet(
        OUT / "financial_adjustments.parquet"
    )
    assert (adjustments["unit_price"] < 0).all()


def test_no_rejected_rows_remain():
    rejected = pd.read_parquet(OUT / "rejected_records.parquet")
    assert rejected.empty


if __name__ == "__main__":
    tests = [
        test_source_row_count,
        test_output_row_counts_reconcile,
        test_sales_have_positive_quantities,
        test_returns_or_cancellations_are_flagged,
        test_adjustments_have_negative_prices,
        test_no_rejected_rows_remain,
    ]

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")

    print(f"\nAll {len(tests)} tests passed.")
