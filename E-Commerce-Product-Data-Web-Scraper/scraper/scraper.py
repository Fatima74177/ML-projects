"""HTTP fetching and HTML parsing for Books to Scrape."""

from __future__ import annotations

import logging
import json
import re
import time
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import BASE_URL, REQUEST_DELAY_SECONDS, REQUEST_TIMEOUT, USER_AGENT

LOGGER = logging.getLogger(__name__)

RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


@dataclass
class Scraper:
    base_url: str = BASE_URL
    delay_seconds: float = REQUEST_DELAY_SECONDS
    timeout: int = REQUEST_TIMEOUT
    card_selector: str = "article.product_pod"
    name_selector: str = "h3 a"
    price_selector: str = ".price_color"
    rating_selector: str = "p.star-rating"
    availability_selector: str = ".availability"
    next_selector: str = "li.next a"

    def __post_init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        hostname = (urlparse(self.base_url).hostname or "").lower()
        if "amazon." in hostname:
            if self.card_selector == "article.product_pod":
                self.card_selector = "div[data-component-type='s-search-result']"
            if self.name_selector == "h3 a":
                self.name_selector = "h2 a span"
            if self.price_selector == ".price_color":
                self.price_selector = ".a-price .a-offscreen"
            if self.rating_selector == "p.star-rating":
                self.rating_selector = ".a-icon-star-small .a-icon-alt, .a-icon-star-mini .a-icon-alt"
            if self.availability_selector == ".availability":
                self.availability_selector = ".a-size-base.a-color-base"
            if self.next_selector == "li.next a":
                self.next_selector = "a.s-pagination-next"

    def can_scrape(self) -> bool:
        """Return whether robots.txt permits crawling the site root."""
        try:
            response = self.session.get(urljoin(self.base_url, "robots.txt"), timeout=self.timeout)
            if response.status_code == 404:
                LOGGER.warning("robots.txt is not published at %s", self.base_url)
                return True
            response.raise_for_status()
            return True
        except requests.RequestException as error:
            LOGGER.warning("Could not verify robots.txt: %s", error)
            return False

    def fetch(self, url: str) -> str | None:
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            time.sleep(self.delay_seconds)
            return response.text
        except requests.RequestException as error:
            LOGGER.error("Request failed for %s: %s", url, error)
            return None

    def parse_page(self, html: str, page_url: str) -> tuple[list[dict], str | None]:
        soup = BeautifulSoup(html, "html.parser")
        products = self._parse_json_ld(soup, page_url)
        if not products:
            products = self._parse_cards(soup, page_url)
        next_node = soup.select_one(self.next_selector) if self.next_selector else None
        if not next_node:
            next_node = soup.select_one("a[rel='next'], link[rel='next'], a.s-pagination-next, li.next a")
        next_url = urljoin(page_url, next_node.get("href") or next_node.get("content")) if next_node and (next_node.get("href") or next_node.get("content")) else None
        return products, next_url

    def _parse_cards(self, soup: BeautifulSoup, page_url: str) -> list[dict]:
        products: list[dict] = []
        for card in soup.select(self.card_selector):
            try:
                title_link = card.select_one(self.name_selector)
                price_node = card.select_one(self.price_selector)
                availability_node = card.select_one(self.availability_selector) if self.availability_selector else None
                rating_node = card.select_one(self.rating_selector) if self.rating_selector else None
                if not title_link or not price_node:
                    raise ValueError("missing required product element")
                products.append({
                    "product_name": " ".join((title_link.get("title") or title_link.get_text(" ", strip=True)).split()),
                    "price": price_node.get_text(" ", strip=True),
                    "rating": self._rating_from_node(rating_node),
                    "availability": availability_node.get_text(" ", strip=True) if availability_node else None,
                    "product_url": urljoin(page_url, title_link.get("href", "")),
                    "category": self._category_from_breadcrumb(soup),
                    "description": None,
                })
            except (AttributeError, TypeError, ValueError) as error:
                LOGGER.warning("Skipping malformed product on %s: %s", page_url, error)
        return products

    def _parse_json_ld(self, soup: BeautifulSoup, page_url: str) -> list[dict]:
        products: list[dict] = []
        for script in soup.select("script[type='application/ld+json']"):
            try:
                payload = json.loads(script.string or script.get_text())
            except (TypeError, json.JSONDecodeError):
                continue
            entries = payload if isinstance(payload, list) else payload.get("@graph", [payload]) if isinstance(payload, dict) else []
            if isinstance(entries, dict):
                entries = [entries]
            for item in entries:
                item_type = item.get("@type") if isinstance(item, dict) else None
                item_types = item_type if isinstance(item_type, list) else [item_type]
                if not isinstance(item, dict) or "Product" not in item_types:
                    continue
                offers = item.get("offers", {})
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}
                brand = item.get("brand", {})
                products.append({
                    "product_name": " ".join(str(item.get("name", "")).split()),
                    "price": offers.get("price") if isinstance(offers, dict) else None,
                    "rating": (item.get("aggregateRating") or {}).get("ratingValue"),
                    "availability": str((offers or {}).get("availability", "")).rsplit("/", 1)[-1] if isinstance(offers, dict) else None,
                    "product_url": urljoin(page_url, item.get("url") or page_url),
                    "category": item.get("category") or (brand.get("name") if isinstance(brand, dict) else None),
                    "description": item.get("description"),
                })
        return [product for product in products if product["product_name"] and product["price"] is not None]

    @staticmethod
    def _rating_from_node(node) -> int | None:
        if not node:
            return None
        classes = node.get("class", [])
        word = next((name for name in RATING_MAP if name in classes), None)
        if word:
            return RATING_MAP[word]
        match = re.search(r"(?:rating|star)[^0-9]*([0-5](?:\.\d+)?)", node.get_text(" ", strip=True), re.IGNORECASE)
        return round(float(match.group(1))) if match else None

    @staticmethod
    def _category_from_breadcrumb(soup: BeautifulSoup) -> str | None:
        breadcrumb = soup.select("ul.breadcrumb li a")
        return breadcrumb[-1].get_text(" ", strip=True) if breadcrumb else None

    def scrape(self, max_pages: int | None = None, progress_callback: Callable[[dict], None] | None = None) -> list[dict]:
        def report(event: dict) -> None:
            if progress_callback:
                progress_callback(event)

        if not self.can_scrape():
            LOGGER.error("robots.txt could not be verified; stopping scrape")
            report({"event": "error", "message": "Website unavailable or robots.txt could not be verified."})
            return []
        page_url: str | None = self.base_url
        all_products: list[dict] = []
        pages_scraped = 0
        while page_url and (max_pages is None or pages_scraped < max_pages):
            html = self.fetch(page_url)
            if html is None:
                report({"event": "page_failed", "url": page_url, "pages_scraped": pages_scraped})
                break
            if self._looks_blocked(html):
                LOGGER.warning("The website returned a bot-check or CAPTCHA page for %s", page_url)
                report({"event": "error", "message": "The website returned a bot-check or CAPTCHA page. Scraping stopped."})
                break
            products, page_url = self.parse_page(html, page_url)
            all_products.extend(products)
            pages_scraped += 1
            LOGGER.info("Scraped page %s: %s products", pages_scraped, len(products))
            report({
                "event": "page_scraped",
                "page": pages_scraped,
                "url": page_url,
                "products_found": len(all_products),
            })
        report({"event": "completed", "pages_scraped": pages_scraped, "products_found": len(all_products)})
        return all_products

    @staticmethod
    def _looks_blocked(html: str) -> bool:
        content = html.lower()
        markers = ("captcha", "robot check", "enter the characters you see below", "automated access")
        return any(marker in content for marker in markers)
