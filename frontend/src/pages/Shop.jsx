// Shop.jsx — Product browsing with category filter, search, and pagination
import { useState, useEffect, useCallback } from 'react';
import { Search, Filter, X, ChevronLeft, ChevronRight } from 'lucide-react';
import ProductCard from '../components/ProductCard';
import { getProducts, searchProducts, getCategories } from '../api';
import './Shop.css';

export default function Shop() {
  const [products, setProducts]       = useState([]);
  const [categories, setCategories]   = useState([]);
  const [loading, setLoading]         = useState(true);
  const [searchQ, setSearchQ]         = useState('');
  const [selectedCat, setSelectedCat] = useState(null);
  const [page, setPage]               = useState(1);
  const [totalPages, setTotalPages]   = useState(1);
  const [total, setTotal]             = useState(0);

  const PER_PAGE = 24;

  // Load categories once
  useEffect(() => {
    getCategories().then(d => setCategories(d.categories || []));
  }, []);

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    try {
      let data;
      if (searchQ.trim()) {
        data = await searchProducts(searchQ);
        setProducts(data.items || []);
        setTotalPages(1);
        setTotal(data.items?.length || 0);
      } else {
        data = await getProducts(page, PER_PAGE, selectedCat);
        setProducts(data.items || []);
        setTotalPages(data.pages || 1);
        setTotal(data.total || 0);
      }
    } catch (e) {
      setProducts([]);
    } finally {
      setLoading(false);
    }
  }, [page, selectedCat, searchQ]);

  useEffect(() => { fetchProducts(); }, [fetchProducts]);

  const handleCatChange = (catId) => {
    setSelectedCat(catId === selectedCat ? null : catId);
    setPage(1);
    setSearchQ('');
  };

  const handleSearch = (e) => {
    setSearchQ(e.target.value);
    setPage(1);
  };

  return (
    <div className="shop page">
      <div className="container">
        {/* ── Header ─────────────────────────────────────────────── */}
        <div className="shop-header">
          <div>
            <h1 className="heading-lg">Shop</h1>
            <p className="text-muted mt-1">
              {total.toLocaleString()} products found
              {selectedCat && categories.find(c => c.id === selectedCat)
                ? ` in "${categories.find(c => c.id === selectedCat).name}"`
                : ''}
            </p>
          </div>
          {/* Search */}
          <div className="shop-search-wrap">
            <Search size={18} className="shop-search-icon" />
            <input
              id="shop-search-input"
              className="input shop-search"
              placeholder="Search products…"
              value={searchQ}
              onChange={handleSearch}
            />
            {searchQ && (
              <button className="shop-search-clear" onClick={() => { setSearchQ(''); setPage(1); }}>
                <X size={16} />
              </button>
            )}
          </div>
        </div>

        {/* ── Category chips ─────────────────────────────────────── */}
        <div className="category-chips">
          <button
            className={`chip ${!selectedCat ? 'chip-active' : ''}`}
            onClick={() => { setSelectedCat(null); setPage(1); }}
            id="cat-all"
          >
            All
          </button>
          {categories.slice(0, 20).map(cat => (
            <button
              key={cat.id}
              id={`cat-${cat.id}`}
              className={`chip ${selectedCat === cat.id ? 'chip-active' : ''}`}
              onClick={() => handleCatChange(cat.id)}
            >
              {cat.name.length > 22 ? cat.name.slice(0, 22) + '…' : cat.name}
            </button>
          ))}
        </div>

        {/* ── Product grid ───────────────────────────────────────── */}
        {loading ? (
          <div className="grid-4">
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} className="skeleton" style={{ height: 290 }} />
            ))}
          </div>
        ) : products.length === 0 ? (
          <div className="empty-state">
            <span className="empty-emoji">🔍</span>
            <p>No products found. Try a different search or category.</p>
          </div>
        ) : (
          <div className="grid-4">
            {products.map(item => <ProductCard key={item.id} item={item} />)}
          </div>
        )}

        {/* ── Pagination ─────────────────────────────────────────── */}
        {!searchQ && totalPages > 1 && (
          <div className="pagination">
            <button
              className="btn btn-secondary btn-sm"
              disabled={page === 1}
              onClick={() => setPage(p => p - 1)}
              id="prev-page-btn"
            >
              <ChevronLeft size={16} /> Prev
            </button>
            <span className="page-info">Page {page} of {totalPages}</span>
            <button
              className="btn btn-secondary btn-sm"
              disabled={page === totalPages}
              onClick={() => setPage(p => p + 1)}
              id="next-page-btn"
            >
              Next <ChevronRight size={16} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
