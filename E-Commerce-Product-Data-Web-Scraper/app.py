"""Flask dashboard for the e-commerce scraping pipeline."""

from __future__ import annotations

import io
import logging
import os
import threading
from collections import deque
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from flask import Flask, jsonify, render_template, request, send_file

from scraper.analysis import summarize
from scraper.config import BASE_URL, OUTPUT_DIR
from scraper.processing import clean_products
from scraper.scraper import Scraper
from scraper.storage import save_outputs

app = Flask(__name__)
state_lock = threading.Lock()
state = {
    "running": False,
    "message": "Ready to scrape",
    "pages_scraped": 0,
    "products_found": 0,
    "duplicates_removed": 0,
    "failed_pages": 0,
    "final_valid_records": 0,
    "logs": deque(maxlen=100),
    "products": [],
    "summary": {"total_products": 0},
}


def log(message: str, level: int = logging.INFO) -> None:
    app.logger.log(level, message)
    with state_lock:
        state["logs"].append(message)


def snapshot() -> dict:
    with state_lock:
        result = dict(state)
        result["logs"] = list(state["logs"])
        return result


def run_scrape(url: str, max_pages: int, delay: float, selectors: dict[str, str]) -> None:
    try:
        raw_records: list[dict] = []

        def progress(event: dict) -> None:
            with state_lock:
                if event["event"] == "page_scraped":
                    state["pages_scraped"] = event["page"]
                    state["products_found"] = event["products_found"]
                    state["message"] = f"Scraped page {event['page']}"
                elif event["event"] == "page_failed":
                    state["failed_pages"] += 1
                    state["message"] = "A page failed to load"
                elif event["event"] == "error":
                    state["message"] = event["message"]
            if event["event"] == "page_scraped":
                log(f"Page {event['page']} complete: {event['products_found']} products found")
            elif event["event"] == "page_failed":
                log(f"Page failed: {event['url']}", logging.ERROR)

        log(f"Starting scrape from {url}")
        raw_records = Scraper(base_url=url, delay_seconds=delay, **selectors).scrape(max_pages=max_pages, progress_callback=progress)
        frame = clean_products(raw_records)
        duplicate_count = len(raw_records) - frame["product_url"].nunique() if raw_records else 0
        summary = summarize(frame)
        products = frame.where(frame.notna(), None).to_dict(orient="records")
        if not os.getenv("VERCEL"):
            save_outputs(frame, OUTPUT_DIR)
        with state_lock:
            state.update({
                "running": False,
                "message": "Scraping completed with warnings" if state["failed_pages"] else "Scraping completed",
                "duplicates_removed": max(0, duplicate_count),
                "final_valid_records": len(frame),
                "products": products,
                "summary": summary,
            })
        log(f"Completed: {len(frame)} valid records, {max(0, duplicate_count)} duplicates removed")
    except Exception as error:
        logging.exception("Scrape failed")
        with state_lock:
            state["running"] = False
            state["message"] = f"Scraping failed: {error}"
        log(f"Scraping failed: {error}", logging.ERROR)


@app.get("/")
def dashboard():
    return render_template("index.html", default_url=BASE_URL)


@app.get("/api/status")
def api_status():
    return jsonify(snapshot())


@app.get("/api/products")
def api_products():
    current = snapshot()["products"]
    query = request.args.get("search", "").lower().strip()
    category = request.args.get("category", "").strip()
    availability = request.args.get("availability", "").strip()
    min_price = float(request.args["min_price"]) if request.args.get("min_price") else None
    max_price = float(request.args["max_price"]) if request.args.get("max_price") else None
    min_rating = float(request.args["min_rating"]) if request.args.get("min_rating") else None
    filtered = [product for product in current if (
        (not query or query in str(product.get("product_name", "")).lower())
        and (not category or product.get("category") == category)
        and (not availability or (availability == "available") == ("in stock" in str(product.get("availability", "")).lower()))
        and (min_price is None or (product.get("price") is not None and product["price"] >= min_price))
        and (max_price is None or (product.get("price") is not None and product["price"] <= max_price))
        and (min_rating is None or (product.get("rating") is not None and product["rating"] >= min_rating))
    )]
    categories = sorted({product.get("category") for product in current if product.get("category")})
    return jsonify({"products": filtered, "categories": categories})


@app.post("/api/scrape")
def start_scrape():
    payload = request.get_json(silent=True) or {}
    url = str(payload.get("url", BASE_URL)).strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return jsonify({"error": "Invalid URL. Enter a complete http:// or https:// URL."}), 400
    try:
        max_pages = max(1, min(100, int(payload.get("max_pages", 5))))
        delay = max(0, min(60, float(payload.get("delay", 1))))
    except (TypeError, ValueError):
        return jsonify({"error": "Pages must be a number and delay must be a valid decimal."}), 400
    selectors = {
        "card_selector": str(payload.get("card_selector", "article.product_pod")).strip(),
        "name_selector": str(payload.get("name_selector", "h3 a")).strip(),
        "price_selector": str(payload.get("price_selector", ".price_color")).strip(),
        "rating_selector": str(payload.get("rating_selector", "p.star-rating")).strip(),
        "availability_selector": str(payload.get("availability_selector", ".availability")).strip(),
        "next_selector": str(payload.get("next_selector", "li.next a")).strip(),
    }
    with state_lock:
        if state["running"]:
            return jsonify({"error": "A scrape is already running."}), 409
        state.update({"running": True, "message": "Starting scrape", "pages_scraped": 0, "products_found": 0, "duplicates_removed": 0, "failed_pages": 0, "final_valid_records": 0, "products": [], "summary": {"total_products": 0}})
        state["logs"].clear()
    if os.getenv("VERCEL"):
        run_scrape(url, max_pages, delay, selectors)
        return jsonify({"message": snapshot()["message"]}), 200
    threading.Thread(target=run_scrape, args=(url, max_pages, delay, selectors), daemon=True).start()
    return jsonify({"message": "Scrape started"}), 202


@app.get("/download/<kind>")
def download(kind: str):
    frame = pd.DataFrame(snapshot()["products"])
    if kind == "csv":
        return send_file(io.BytesIO(frame.to_csv(index=False).encode("utf-8")), mimetype="text/csv", as_attachment=True, download_name="products.csv")
    if kind == "excel":
        output = io.BytesIO()
        frame.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)
        return send_file(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name="products.xlsx")
    return jsonify({"error": "Unknown export format"}), 404


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
