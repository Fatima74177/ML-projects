from scraper.processing import clean_products, validate_products
from scraper.scraper import Scraper


HTML = """
<html><body><ul class='breadcrumb'><li><a>Home</a></li><li><a>Travel</a></li></ul>
<article class='product_pod'><h3><a title='  A   Book '>A Book</a></h3><p class='price_color'>£12.99</p><p class='star-rating Four'></p><p class='availability'> In stock </p></article>
<li class='next'><a href='page-2.html'>next</a></li></body></html>
"""


def test_parse_page_extracts_product_and_next_url():
    products, next_url = Scraper(delay_seconds=0).parse_page(HTML, "https://books.toscrape.com/catalogue/page-1.html")
    assert products[0]["product_name"] == "A Book"
    assert products[0]["rating"] == 4
    assert products[0]["category"] == "Travel"
    assert next_url.endswith("/catalogue/page-2.html")


def test_clean_products_deduplicates_and_converts_price():
    records = [{"product_name": " A  Book ", "price": "£12.99", "rating": 4, "availability": "In stock", "product_url": "https://example.test/book", "category": "Travel", "description": None}] * 2
    frame = clean_products(records)
    assert len(frame) == 1
    assert frame.loc[0, "price"] == 12.99
    assert validate_products(frame) == (True, [])


AMAZON_HTML = """
<div data-component-type="s-search-result">
    <h2><a href="/dp/B001"><span>Demo Product</span></a></h2>
    <span class="a-price"><span class="a-offscreen">$19.99</span></span>
    <i class="a-icon-star-small"><span class="a-icon-alt">4.5 out of 5 stars</span></i>
</div>
<a class="s-pagination-next" href="?page=2">Next</a>
"""


def test_amazon_profile_extracts_products_and_next_page():
    scraper = Scraper(base_url="https://www.amazon.com/s?k=shoes", delay_seconds=0)
    products, next_url = scraper.parse_page(AMAZON_HTML, scraper.base_url)
    assert products[0]["product_name"] == "Demo Product"
    assert products[0]["price"] == "$19.99"
    assert next_url == "https://www.amazon.com/s?page=2"


def test_vercel_entrypoint_exports_flask_app():
    from api.index import app

    assert app.name == "app"
