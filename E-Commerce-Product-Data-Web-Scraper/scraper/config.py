"""Configuration for the Books to Scrape data pipeline."""

from pathlib import Path
import os

BASE_URL = os.getenv("SCRAPER_DEFAULT_URL", "https://books.toscrape.com/").strip()
REQUEST_TIMEOUT = 20
REQUEST_DELAY_SECONDS = 1.0
USER_AGENT = "ECommerceProductScraper/1.0 (educational project)"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

PRODUCT_COLUMNS = [
    "product_name",
    "price",
    "rating",
    "availability",
    "product_url",
    "category",
    "description",
]
