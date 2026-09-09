"""Cleaning and validation of scraped product records."""

from __future__ import annotations

import re

import pandas as pd

from .config import PRODUCT_COLUMNS


def clean_products(records: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(records, columns=PRODUCT_COLUMNS)
    if frame.empty:
        return frame
    frame["product_name"] = frame["product_name"].fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    frame["price"] = frame["price"].astype(str).str.replace(r"[^0-9.]", "", regex=True)
    frame["price"] = pd.to_numeric(frame["price"], errors="coerce")
    frame["rating"] = pd.to_numeric(frame["rating"], errors="coerce").clip(1, 5)
    frame["availability"] = frame["availability"].fillna("Unknown").astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    frame["category"] = frame["category"].fillna("Unknown").astype(str).str.strip()
    frame["description"] = frame["description"].fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    frame = frame.drop_duplicates(subset=["product_url"]).dropna(subset=["product_name", "price", "product_url"])
    frame["rating"] = frame["rating"].astype("Int64")
    return frame.reset_index(drop=True)


def validate_products(frame: pd.DataFrame) -> tuple[bool, list[str]]:
    errors: list[str] = []
    missing_columns = set(PRODUCT_COLUMNS) - set(frame.columns)
    if missing_columns:
        errors.append(f"Missing columns: {sorted(missing_columns)}")
    if frame.empty:
        errors.append("Dataset is empty")
    if "price" in frame and (frame["price"] < 0).any():
        errors.append("Price contains negative values")
    if "rating" in frame and not frame["rating"].dropna().between(1, 5).all():
        errors.append("Rating is outside the range 1-5")
    return not errors, errors
