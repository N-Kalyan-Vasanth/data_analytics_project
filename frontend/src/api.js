// api.js — Centralised API client
// All API calls go through this module so base URL changes in one place.

const BASE = '/api';  // Proxied to http://localhost:5000 via vite.config.js

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    credentials: 'include',   // send session cookies for cart
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || 'API error');
  }
  return res.json();
}

// ── Products ──────────────────────────────────────────────────────
export const getProducts = (page = 1, perPage = 20, categoryId = null) => {
  let url = `/products?page=${page}&per_page=${perPage}`;
  if (categoryId) url += `&category_id=${categoryId}`;
  return request(url);
};

export const searchProducts = (q) => request(`/products/search?q=${encodeURIComponent(q)}`);
export const getProduct     = (id) => request(`/products/${id}`);
export const getTopProducts = (n = 10) => request(`/top-products?n=${n}`);
export const getCategories  = () => request('/categories');

// ── Cart ──────────────────────────────────────────────────────────
export const getCart        = () => request('/cart');
export const addToCart      = (itemId, qty = 1) => request('/cart', { method: 'POST', body: JSON.stringify({ item_id: itemId, quantity: qty }) });
export const updateCartItem = (cartItemId, qty) => request(`/cart/${cartItemId}`, { method: 'PUT', body: JSON.stringify({ quantity: qty }) });
export const removeCartItem = (cartItemId) => request(`/cart/${cartItemId}`, { method: 'DELETE' });
export const clearCart      = () => request('/cart', { method: 'DELETE' });

// ── Recommendations ───────────────────────────────────────────────
export const getRecommendations = (itemId, algo = 'fpgrowth') => request(`/recommendations/${itemId}?algorithm=${algo}`);
export const getAssocRules      = (algo = 'fpgrowth') => request(`/recommendations/rules?algorithm=${algo}`);
export const compareAlgorithms  = () => request('/recommendations/compare', { method: 'POST' });

// ── Predictions ───────────────────────────────────────────────────
export const getPredictionSummary = () => request('/predictions/summary');
export const getMonthlyPredictions = (p=1,d=1,q=1,months=3) => request(`/predictions/monthly?p=${p}&d=${d}&q=${q}&months=${months}`);
export const getMovingAvg  = (window=3, months=3) => request(`/predictions/moving-avg?window=${window}&months=${months}`);
export const getAllPredictions     = () => request('/predictions/all');

// ── Sequential Patterns ───────────────────────────────────────────
export const getSequentialPatterns = (limit = 20) => request(`/patterns/sequential?limit=${limit}`);
export const getNextRecs            = (itemId) => request(`/patterns/next/${itemId}`);
export const getPatternsSummary     = () => request('/patterns/summary');
