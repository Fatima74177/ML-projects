# E-Commerce Product Data Web Scraper

A modular Python scraper that collects book products from [Books to Scrape](https://books.toscrape.com/), a public practice website intended for scraping exercises. It follows the site's `robots.txt`, uses a one-second delay by default, handles pagination, cleans and validates records, exports CSV and Excel files, and produces basic analysis charts.

## Project structure

```text
E-Commerce-Product-Data-Web-Scraper/
├── scraper/
│   ├── analysis.py
│   ├── config.py
│   ├── processing.py
│   ├── scraper.py
│   └── storage.py
├── data/
├── output/
├── notebooks/
├── tests/
├── main.py
├── app.py
├── api/
│   └── index.py
├── templates/
├── static/
├── vercel.json
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Run

Launch the web dashboard:

```bash
python app.py
```

Open `http://127.0.0.1:5000`. The dashboard supports configurable URLs, page limits and delays; live scrape status and logs; search and filters; product detail views; CSV and Excel downloads; summary metrics; and price, rating, category, and price-vs-rating charts.

The default website is `https://books.toscrape.com/`. To set another website as the pre-filled URL without changing code, define `SCRAPER_DEFAULT_URL` before starting the app:

```powershell
$env:SCRAPER_DEFAULT_URL = "https://example.com/products"
python app.py
```

## Deploy to Vercel

Push the project to GitHub, import that repository in Vercel, and keep the project settings at their defaults. Vercel detects `vercel.json`, uses `api/index.py` as the Flask entrypoint, and installs the packages from `requirements.txt`.

On Vercel, scraping runs inside the request because serverless functions do not keep background threads alive reliably. Start with a small page count and low delay. Scraped results and downloads are held in function memory; Vercel storage is not persistent, so use a database or object storage later if results must survive function restarts.

The scraper first looks for standard `Product` JSON-LD, which works with many e-commerce platforms automatically. For sites with custom HTML, expand **Custom site selectors** and enter CSS selectors for the product card, name, price, rating, availability, and next-page link. Sites that require JavaScript to render products, authentication, or anti-bot challenges need a browser-based adapter such as Playwright and must be scraped only with permission.

A complete run crawls all available pages:

```bash
python main.py
```

For a quick test run:

```bash
python main.py --max-pages 2 --delay 0
```

Results are written to `output/products.csv`, `output/products.xlsx`, `output/summary.json`, and four PNG charts. The notebook in `notebooks/product_analysis.ipynb` demonstrates the same workflow interactively.

## Data fields

`product_name`, `price`, `rating`, `availability`, `product_url`, `category`, and `description` are normalized into a consistent dataset. Books to Scrape exposes descriptions on detail pages, so the current list-page implementation leaves that optional field blank rather than issuing extra requests; the field is ready for a detail-page enrichment step.

## Quality checks

```bash
python -m pytest -q
python -m compileall scraper main.py tests
```
