const charts = {};
const ids = ['search', 'category', 'min-price', 'max-price', 'min-rating', 'availability'];
const $ = (id) => document.getElementById(id);

function money(value) { return value == null ? '—' : `$${Number(value).toFixed(2)}`; }
function escapeHtml(value) { return String(value ?? '').replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char])); }

function renderMetrics(data) {
  const summary = data.summary || {};
  const metrics = [['TOTAL PRODUCTS', summary.total_products || 0], ['AVERAGE PRICE', money(summary.average_price)], ['PRICE RANGE', `${money(summary.minimum_price)} - ${money(summary.maximum_price)}`], ['AVERAGE RATING', summary.average_rating ? `${summary.average_rating} / 5` : '—'], ['AVAILABLE', summary.available_products || 0], ['UNAVAILABLE', summary.unavailable_products || 0], ['PAGES SCRAPED', data.pages_scraped || 0], ['DUPLICATES REMOVED', data.duplicates_removed || 0], ['FAILED PAGES', data.failed_pages || 0], ['FINAL VALID RECORDS', data.final_valid_records || 0]];
  $('metrics').innerHTML = metrics.map(([label, value]) => `<div class="metric"><span>${label}</span><strong>${value}</strong></div>`).join('');
}

function renderProducts(products, categories) {
  const current = $('category').value;
  $('category').innerHTML = '<option value="">All categories</option>' + categories.map((item) => `<option>${escapeHtml(item)}</option>`).join('');
  $('category').value = categories.includes(current) ? current : '';
  $('products').innerHTML = products.length ? products.map((product, index) => `<tr data-index="${index}"><td class="product-name">${escapeHtml(product.product_name)}</td><td>${escapeHtml(product.category)}</td><td>${money(product.price)}</td><td>${product.rating ? '★'.repeat(product.rating) : '—'}</td><td class="pill">${escapeHtml(product.availability)}</td></tr>`).join('') : '<tr><td colspan="5" class="empty">No products match these filters.</td></tr>';
  [...document.querySelectorAll('#products tr[data-index]')].forEach((row) => row.addEventListener('click', () => showDetail(products[row.dataset.index])));
}

async function loadProducts() {
  const params = new URLSearchParams();
  ids.forEach((id) => { if ($(id).value) params.set(id === 'min-price' ? 'min_price' : id === 'max-price' ? 'max_price' : id === 'min-rating' ? 'min_rating' : id, $(id).value); });
  const response = await fetch(`/api/products?${params}`);
  const data = await response.json();
  renderProducts(data.products, data.categories);
}

function showDetail(product) {
  $('product-detail').innerHTML = `<div class="eyebrow">PRODUCT DETAIL</div><h2 class="detail-title">${escapeHtml(product.product_name)}</h2><div class="detail-grid"><div><div class="detail-label">Price</div><div class="detail-value">${money(product.price)}</div></div><div><div class="detail-label">Rating</div><div class="detail-value">${product.rating ? `${product.rating} / 5` : 'Not rated'}</div></div><div><div class="detail-label">Availability</div><div class="detail-value">${escapeHtml(product.availability)}</div></div><div><div class="detail-label">Category</div><div class="detail-value">${escapeHtml(product.category)}</div></div></div><div class="detail-label">Description</div><p>${escapeHtml(product.description || 'Description unavailable for this product.')}</p><div class="detail-label">Product URL</div><p><a href="${escapeHtml(product.product_url)}" target="_blank" rel="noreferrer">Open product page</a></p>`;
  $('product-dialog').showModal();
}

function renderCharts(products) {
  const chartIds = ['price-chart', 'rating-chart', 'scatter-chart', 'category-chart'];
  if (!products.length) {
    chartIds.forEach((id) => {
      if (charts[id]) charts[id].destroy();
      const canvas = $(id);
      const context = canvas.getContext('2d');
      context.clearRect(0, 0, canvas.width, canvas.height);
      context.font = '500 13px DM Sans';
      context.fillStyle = '#788589';
      context.textAlign = 'center';
      context.fillText('Run a scrape to see this analysis', canvas.clientWidth / 2, canvas.clientHeight / 2);
    });
    return;
  }
  const ratings = [1, 2, 3, 4, 5].map((rating) => products.filter((product) => product.rating === rating).length);
  const prices = products.map((product) => Number(product.price)).filter(Number.isFinite);
  const priceBins = [0, 20, 40, 60, 80, 100, Infinity];
  const priceLabels = ['$0-20', '$20-40', '$40-60', '$60-80', '$80-100', '$100+'];
  const priceCounts = priceBins.slice(0, -1).map((start, index) => prices.filter((price) => price >= start && price < priceBins[index + 1]).length);
  const categoryCounts = {};
  products.forEach((product) => { categoryCounts[product.category] = (categoryCounts[product.category] || 0) + 1; });
  const categories = Object.entries(categoryCounts).sort(([, first], [, second]) => second - first).slice(0, 12);
  const palette = { coral: '#e86f51', teal: '#176b67', gold: '#e5b94f', ink: '#26343a', grid: '#e2e5e1', muted: '#788589' };
  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 650, easing: 'easeOutQuart' },
    interaction: { intersect: false, mode: 'index' },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: palette.ink,
        titleFont: { family: 'DM Sans', weight: '700' },
        bodyFont: { family: 'DM Sans' },
        padding: 12,
        cornerRadius: 4,
        displayColors: false,
      },
    },
    scales: {
      x: { grid: { display: false }, ticks: { color: palette.muted, font: { family: 'DM Sans', size: 11 } } },
      y: { beginAtZero: true, grid: { color: palette.grid }, border: { display: false }, ticks: { color: palette.muted, precision: 0, font: { family: 'DM Sans', size: 11 } } },
    },
  };
  const configs = {
    'price-chart': { type: 'bar', data: { labels: priceLabels, datasets: [{ data: priceCounts, backgroundColor: palette.coral, borderRadius: 5, borderSkipped: false, barPercentage: .68, categoryPercentage: .72 }] } },
    'rating-chart': { type: 'bar', data: { labels: ['1 star', '2 stars', '3 stars', '4 stars', '5 stars'], datasets: [{ data: ratings, backgroundColor: [palette.gold, palette.gold, palette.teal, palette.teal, palette.coral], borderRadius: 5, borderSkipped: false, barPercentage: .62 }] } },
    'scatter-chart': { type: 'scatter', data: { datasets: [{ data: products.filter((p) => p.rating && p.price != null).map((p) => ({x: p.rating, y: p.price})), backgroundColor: palette.coral, borderColor: '#fff', borderWidth: 2, pointRadius: 6, pointHoverRadius: 8 }] }, options: { scales: { x: { min: 0.5, max: 5.5, ticks: { stepSize: 1 }, title: {display: true, text: 'RATING', color: palette.muted, font: { family: 'DM Sans', size: 10, weight: '700' } } }, y: { title: {display: true, text: 'PRICE', color: palette.muted, font: { family: 'DM Sans', size: 10, weight: '700' } } } } } },
    'category-chart': { type: 'bar', data: { labels: categories.map(([name]) => name), datasets: [{ data: categories.map(([, count]) => count), backgroundColor: palette.teal, borderRadius: 5, borderSkipped: false, barPercentage: .62 }] }, options: { indexAxis: 'y', scales: { x: { ticks: { precision: 0 } }, y: { grid: { display: false } } } } },
  };
  Object.entries(configs).forEach(([id, config]) => { if (charts[id]) charts[id].destroy(); charts[id] = new Chart($(id), { ...config, options: { ...baseOptions, ...config.options, plugins: { ...baseOptions.plugins, ...config.options?.plugins } } }); });
}

async function poll() {
  const response = await fetch('/api/status');
  const data = await response.json();
  $('connection').textContent = data.running ? 'SCRAPING' : (data.message || 'READY').toUpperCase();
  $('connection').classList.toggle('running', data.running);
  $('form-message').textContent = data.message || '';
  $('logs').textContent = data.logs?.join('\n') || 'No activity yet.';
  renderMetrics(data);
  if (data.running) setTimeout(poll, 700); else { await loadProducts(); renderCharts(data.products || []); }
}

$('scrape-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {url: $('url').value, max_pages: $('max-pages').value, delay: $('delay').value};
  ['card-selector', 'name-selector', 'price-selector', 'rating-selector', 'availability-selector', 'next-selector'].forEach((id) => { payload[id] = $(id).value; });
  const response = await fetch('/api/scrape', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
  const data = await response.json();
  $('form-message').textContent = data.error || data.message;
  if (response.ok) poll();
});
ids.forEach((id) => $(id).addEventListener('input', loadProducts));
poll();
