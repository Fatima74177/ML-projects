"""Summary statistics and plots for scraped products."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def summarize(frame: pd.DataFrame) -> dict:
    if frame.empty:
        return {"total_products": 0}
    rating_counts = frame["rating"].value_counts(dropna=True)
    return {
        "total_products": int(len(frame)),
        "average_price": round(float(frame["price"].mean()), 2),
        "minimum_price": round(float(frame["price"].min()), 2),
        "maximum_price": round(float(frame["price"].max()), 2),
        "average_rating": round(float(frame["rating"].dropna().mean()), 2) if frame["rating"].notna().any() else None,
        "most_common_rating": int(rating_counts.index[0]) if not rating_counts.empty else None,
        "available_products": int(frame["availability"].str.contains("in stock", case=False, na=False).sum()),
        "unavailable_products": int(frame["availability"].str.contains("in stock", case=False, na=False).eq(False).sum()),
        "highest_rated_products": frame.nlargest(5, "rating")["product_name"].tolist(),
        "lowest_price_products": frame.nsmallest(5, "price")["product_name"].tolist(),
    }


def create_visualizations(frame: pd.DataFrame, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    plots = [
        ("price_distribution.png", "Price Distribution", lambda: frame["price"].plot.hist(bins=20, color="#e76f51")),
        ("rating_distribution.png", "Rating Distribution", lambda: frame["rating"].value_counts().sort_index().plot.bar(color="#2a9d8f")),
        ("price_vs_rating.png", "Price vs. Rating", lambda: frame.plot.scatter(x="rating", y="price", alpha=0.6, color="#264653")),
        ("products_by_category.png", "Products by Category", lambda: frame["category"].value_counts().plot.barh(color="#f4a261")),
    ]
    for filename, title, plotter in plots:
        if frame.empty:
            continue
        plt.figure(figsize=(10, 6))
        plotter()
        plt.title(title)
        plt.tight_layout()
        path = output_dir / filename
        plt.savefig(path, dpi=150)
        plt.close()
        paths.append(path)
    return paths
