// Home.jsx — Landing page with hero, top products, and feature highlights
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, BarChart3, Zap, TrendingUp, ShoppingBag, GitBranch } from 'lucide-react';
import ProductCard from '../components/ProductCard';
import { getTopProducts } from '../api';
import './Home.css';

const FEATURES = [
  {
    icon: Zap,
    color: 'purple',
    title: 'Association Rules',
    description: 'Apriori & FP-Growth algorithms mine frequent itemsets to power "Frequently Bought Together" recommendations.',
  },
  {
    icon: TrendingUp,
    color: 'cyan',
    title: 'Time Series Forecasting',
    description: 'ARIMA and Moving Average models predict future sales trends with historical monthly data.',
  },
  {
    icon: GitBranch,
    color: 'amber',
    title: 'Sequential Patterns',
    description: 'PrefixSpan discovers ordered buying sequences, enabling "Customers Buy Next" recommendations.',
  },
  {
    icon: BarChart3,
    color: 'green',
    title: 'Analytics Dashboard',
    description: 'Real-time KPIs, charts, and algorithm performance comparisons in an interactive admin panel.',
  },
];

export default function Home() {
  const [topProducts, setTopProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    getTopProducts(8)
      .then(data => setTopProducts(data.items || []))
      .catch(() => setTopProducts([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="home page">
      {/* ── Hero ───────────────────────────────────────────────── */}
      <section className="hero">
        <div className="hero-bg-orbs">
          <div className="orb orb-1" />
          <div className="orb orb-2" />
          <div className="orb orb-3" />
        </div>
        <div className="container hero-content">
          <div className="hero-badge">
            <span className="badge badge-purple">🧪 Data Mining Powered</span>
          </div>
          <h1 className="heading-xl hero-title">
            Shop Smarter with<br />AI-Powered Insights
          </h1>
          <p className="hero-desc">
            An e-commerce platform powered by Apriori, FP-Growth, ARIMA, and
            PrefixSpan algorithms — delivering intelligent product recommendations
            and sales forecasts in real time.
          </p>
          <div className="hero-actions">
            <button
              className="btn btn-primary btn-lg"
              onClick={() => navigate('/shop')}
              id="hero-shop-btn"
            >
              <ShoppingBag size={20} />
              Browse Products
              <ArrowRight size={18} />
            </button>
            <button
              className="btn btn-secondary btn-lg"
              onClick={() => navigate('/dashboard')}
              id="hero-dashboard-btn"
            >
              <BarChart3 size={20} />
              View Analytics
            </button>
          </div>
          {/* Floating stats */}
          <div className="hero-stats">
            {[
              { label: 'Products', value: '4K+' },
              { label: 'Customers', value: '4K+' },
              { label: 'Sales Records', value: '525K+' },
              { label: 'ML Algorithms', value: '4' },
            ].map(stat => (
              <div key={stat.label} className="hero-stat">
                <span className="hero-stat-value">{stat.value}</span>
                <span className="hero-stat-label">{stat.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Feature Cards ─────────────────────────────────────── */}
      <section className="section-features container">
        <div className="section-header">
          <h2 className="section-title">Powered by Data Mining</h2>
        </div>
        <div className="grid-4">
          {FEATURES.map(({ icon: Icon, color, title, description }) => (
            <div key={title} className={`feature-card feature-${color}`}>
              <div className={`feature-icon feature-icon-${color}`}>
                <Icon size={22} />
              </div>
              <h3 className="feature-title">{title}</h3>
              <p className="feature-desc">{description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Top Products ──────────────────────────────────────── */}
      <section className="section-products container">
        <div className="section-header">
          <h2 className="section-title">Best Sellers</h2>
          <button
            className="btn btn-ghost"
            onClick={() => navigate('/shop')}
            id="view-all-products-btn"
          >
            View all <ArrowRight size={16} />
          </button>
        </div>
        {loading ? (
          <div className="grid-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="skeleton" style={{ height: 280 }} />
            ))}
          </div>
        ) : (
          <div className="grid-4">
            {topProducts.map(item => <ProductCard key={item.id} item={item} />)}
          </div>
        )}
      </section>
    </div>
  );
}
