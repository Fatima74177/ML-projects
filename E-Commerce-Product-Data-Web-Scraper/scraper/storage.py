"""Persist cleaned product data."""

from pathlib import Path

import pandas as pd


def save_outputs(frame: pd.DataFrame, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "products.csv"
    excel_path = output_dir / "products.xlsx"
    frame.to_csv(csv_path, index=False)
    frame.to_excel(excel_path, index=False, engine="openpyxl")
    return csv_path, excel_path
