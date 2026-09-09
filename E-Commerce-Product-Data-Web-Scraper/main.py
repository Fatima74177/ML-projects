"""Run the complete e-commerce scraping and analysis pipeline."""

import argparse
import json
import logging

from scraper.analysis import create_visualizations, summarize
from scraper.config import OUTPUT_DIR
from scraper.processing import clean_products, validate_products
from scraper.scraper import Scraper
from scraper.storage import save_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Books to Scrape and build an analysis dataset.")
    parser.add_argument("--max-pages", type=int, default=None, help="Limit pages for a quick run.")
    parser.add_argument("--delay", type=float, default=None, help="Seconds between requests.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    scraper = Scraper(delay_seconds=args.delay if args.delay is not None else 1.0)
    frame = clean_products(scraper.scrape(max_pages=args.max_pages))
    valid, errors = validate_products(frame)
    if not valid:
        raise RuntimeError("Dataset validation failed: " + "; ".join(errors))
    csv_path, excel_path = save_outputs(frame, OUTPUT_DIR)
    visualization_paths = create_visualizations(frame, OUTPUT_DIR)
    summary = summarize(frame)
    (OUTPUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"summary": summary, "csv": str(csv_path), "excel": str(excel_path), "charts": [str(path) for path in visualization_paths]}, indent=2))


if __name__ == "__main__":
    main()
