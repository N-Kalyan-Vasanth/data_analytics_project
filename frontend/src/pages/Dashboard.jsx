// Dashboard.jsx — Admin Analytics Dashboard
// Shows: KPIs, Sales forecast charts, Apriori vs FP-Growth comparison,
//        Association rules table, Sequential patterns, and top products.

import { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, AreaChart, Area
} from 'recharts';
import {
  TrendingUp, Zap, BarChart3, GitBranch, Package,
  RefreshCw, Clock, Award, Activity
} from 'lucide-react';
import {
  getPredictionSummary, getAllPredictions,
  getAssocRules, compareAlgorithms,
  getSequentialPatterns, getTopProducts
} from '../api';
import './Dashboard.css';

// ── Custom tooltip for Recharts ────────────────────────────────────
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>
          {p.name}: {typeof p.value === 'number' ? p.value.toLocaleString() : p.value}
        </p>
      ))}
    </div>
  );
};

// ── KPI Card ───────────────────────────────────────────────────────
function StatCard({ label, value, sub, colorClass, icon: Icon }) {
  return (
    <div className={`stat-card ${colorClass}`}>
      <div className="stat-icon"><Icon size={20} /></div>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

// ── Section wrapper ────────────────────────────────────────────────
function DashSection({ title, subtitle, children, id }) {
  return (
    <section className="dash-section" id={id}>
      <div className="dash-section-header">
        <div>
          <h2 className="section-title">{title}</h2>
          {subtitle && <p className="text-muted" style={{ marginTop: 6 }}>{subtitle}</p>}
        </div>
      </div>
      {children}
    </section>
  );
}

export default function Dashboard() {
  const [summary, setSummary]           = useState(null);
  const [predictions, setPredictions]   = useState(null);
  const [rules, setRules]               = useState(null);
  const [comparison, setComparison]     = useState(null);
  const [patterns, setPatterns]         = useState(null);
  const [topItems, setTopItems]         = useState([]);
  const [loadingCompare, setLoadingCompare] = useState(false);
  const [activeTab, setActiveTab]       = useState('arima');

  useEffect(() => {
    // Load all dashboard data on mount
    getPredictionSummary().then(setSummary).catch(console.error);
    getAllPredictions().then(setPredictions).catch(console.error);
    getAssocRules('fpgrowth').then(setRules).catch(console.error);
    getSequentialPatterns(15).then(setPatterns).catch(console.error);
    getTopProducts(8).then(d => setTopItems(d.items || [])).catch(console.error);
  }, []);

  const handleCompare = async () => {
    setLoadingCompare(true);
    try {
      const d = await compareAlgorithms();
      setComparison(d);
    } catch (e) { console.error(e); }
    finally { setLoadingCompare(false); }
  };

  // ── Build chart data ─────────────────────────────────────────────
  const arimaData = predictions?.arima?.historical?.map(h => ({
    month: h.month?.slice(0, 7),
    Actual: Math.round(h.actual),
    Fitted: Math.round(h.fitted),
  })) || [];

  const forecastData = [
    ...(predictions?.arima?.historical?.slice(-6).map(h => ({
      month: h.month?.slice(0, 7),
      Actual: Math.round(h.actual),
    })) || []),
    ...(predictions?.arima?.forecast?.map(f => ({
      month: f.month?.slice(0, 7),
      ARIMA: Math.round(f.predicted),
      MA: 0,
    })) || []),
  ];

  // Merge MA into forecastData
  const maForecast = predictions?.moving_average?.forecast || [];
  maForecast.forEach((f, i) => {
    if (forecastData.length - maForecast.length + i >= 0) {
      const idx = forecastData.length - maForecast.length + i;
      if (forecastData[idx]) forecastData[idx].MA = Math.round(f.predicted);
    }
  });

  const topItemsChartData = topItems.slice(0, 8).map(item => ({
    name: String(item.id || item.item_id || ''),
    sold: item.total_sold,
  }));

  return (
    <div className="dashboard page">
      <div className="container">
        {/* Page header */}
        <div className="dash-page-header">
          <div>
            <h1 className="heading-xl" style={{ fontSize: '2rem' }}>Analytics Dashboard</h1>
            <p className="text-muted">Sales insights, ML-powered patterns & forecasts</p>
          </div>
          <div className="dash-header-badge">
            <Activity size={16} />
            Live Data
          </div>
        </div>

        {/* ── KPI Cards ─────────────────────────────────────────── */}
        <div className="kpi-grid">
          <StatCard
            label="Total Items Sold"
            value={summary ? summary.total_items_sold?.toLocaleString() : '—'}
            sub="All time"
            colorClass="purple"
            icon={Package}
          />
          <StatCard
            label="Total Revenue"
            value={summary ? `₽${(summary.total_revenue / 1e6).toFixed(1)}M` : '—'}
            sub="All time"
            colorClass="cyan"
            icon={TrendingUp}
          />
          <StatCard
            label="Avg Monthly Sales"
            value={summary ? summary.avg_monthly_items?.toLocaleString() : '—'}
            sub={`Peak: ${summary?.peak_month || '—'}`}
            colorClass="amber"
            icon={BarChart3}
          />
          <StatCard
            label="Growth Rate"
            value={summary ? `${summary.growth_rate_pct > 0 ? '+' : ''}${summary.growth_rate_pct}%` : '—'}
            sub="Last vs prev month"
            colorClass="green"
            icon={Activity}
          />
        </div>

        {/* ── Time Series Forecast ──────────────────────────────── */}
        <DashSection
          id="time-series"
          title="Sales Forecast"
          subtitle="ARIMA(1,1,1) fitted values vs actual monthly sales"
        >
          {/* Tab selector */}
          <div className="chart-tabs">
            {['arima', 'moving_avg'].map(tab => (
              <button
                key={tab}
                className={`chart-tab ${activeTab === tab ? 'active' : ''}`}
                onClick={() => setActiveTab(tab)}
                id={`tab-${tab}`}
              >
                {tab === 'arima' ? 'ARIMA Fit' : 'Moving Average'}
              </button>
            ))}
          </div>

          <div className="chart-card">
            {!predictions && <div className="skeleton" style={{ height: 340 }} />}

            {predictions && activeTab === 'arima' && (
              <ResponsiveContainer width="100%" height={340}>
                <AreaChart data={arimaData}>
                  <defs>
                    <linearGradient id="gradActual" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#7c3aed" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="gradFitted" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="month" stroke="#5c5b7a" tick={{ fontSize: 11 }} interval={5} />
                  <YAxis stroke="#5c5b7a" tick={{ fontSize: 11 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Area type="monotone" dataKey="Actual" stroke="#7c3aed" fill="url(#gradActual)" strokeWidth={2} dot={false} />
                  <Area type="monotone" dataKey="Fitted" stroke="#06b6d4" fill="url(#gradFitted)" strokeWidth={2} dot={false} strokeDasharray="4 2" />
                </AreaChart>
              </ResponsiveContainer>
            )}

            {predictions && activeTab === 'moving_avg' && (
              <ResponsiveContainer width="100%" height={340}>
                <AreaChart data={predictions.moving_average?.historical?.map(h => ({
                  month: h.month?.slice(0, 7),
                  Actual: Math.round(h.actual),
                  'Moving Avg': Math.round(h.smoothed),
                })) || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="month" stroke="#5c5b7a" tick={{ fontSize: 11 }} interval={5} />
                  <YAxis stroke="#5c5b7a" tick={{ fontSize: 11 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Area type="monotone" dataKey="Actual" stroke="#f59e0b" fill="rgba(245,158,11,0.1)" strokeWidth={2} dot={false} />
                  <Area type="monotone" dataKey="Moving Avg" stroke="#10b981" fill="rgba(16,185,129,0.1)" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            )}


          </div>

          {predictions?.arima?.metrics && (
            <div className="model-metrics">
              <span className="badge badge-purple">Model: ARIMA{JSON.stringify(predictions.arima.order)}</span>
              <span className="badge badge-cyan">AIC: {predictions.arima.metrics.aic}</span>
              <span className="badge badge-amber">BIC: {predictions.arima.metrics.bic}</span>
            </div>
          )}
        </DashSection>

        {/* ── Top Products Bar Chart ────────────────────────────── */}
        <DashSection id="top-products" title="Top Selling Products" subtitle="By total units sold">
          <div className="chart-card">
            {topItemsChartData.length === 0 ? (
              <div className="skeleton" style={{ height: 280 }} />
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={topItemsChartData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                  <XAxis type="number" stroke="#5c5b7a" tick={{ fontSize: 11 }} />
                  <YAxis dataKey="name" type="category" width={160} stroke="#5c5b7a" tick={{ fontSize: 11 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="sold" fill="url(#barGrad)" radius={[0,4,4,0]}>
                    <defs>
                      <linearGradient id="barGrad" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0%" stopColor="#7c3aed" />
                        <stop offset="100%" stopColor="#06b6d4" />
                      </linearGradient>
                    </defs>
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </DashSection>

        {/* ── Algorithm Comparison ──────────────────────────────── */}
        <DashSection
          id="algo-comparison"
          title="Apriori vs FP-Growth"
          subtitle="Performance comparison on the same transaction dataset"
        >
          {!comparison ? (
            <div className="text-center" style={{ padding: '32px 0' }}>
              <p className="text-muted mb-4">Click to run both algorithms and compare execution time.</p>
              <button
                className="btn btn-primary"
                onClick={handleCompare}
                disabled={loadingCompare}
                id="run-comparison-btn"
              >
                {loadingCompare
                  ? <><RefreshCw size={18} className="spin-icon" /> Running…</>
                  : <><Zap size={18} /> Run Comparison</>
                }
              </button>
            </div>
          ) : (
            <div className="comparison-layout">
              <div className="algo-card algo-apriori card">
                <h3 style={{ color: '#a78bfa', marginBottom: 16 }}>🔵 Apriori</h3>
                <div className="algo-stat">
                  <Clock size={16} />
                  <span>{comparison.comparison.apriori.execution_time_ms} ms</span>
                </div>
                <div className="algo-stat">
                  <Package size={16} />
                  <span>{comparison.comparison.apriori.n_itemsets} frequent itemsets</span>
                </div>
                <div className="algo-stat">
                  <Award size={16} />
                  <span>{comparison.comparison.apriori.n_rules} rules generated</span>
                </div>
              </div>
              <div className="compare-vs">
                <div className="speedup-badge">
                  {comparison.comparison.speedup}×
                  <span>FP-Growth speedup</span>
                </div>
              </div>
              <div className="algo-card algo-fpgrowth card">
                <h3 style={{ color: '#67e8f9', marginBottom: 16 }}>⚡ FP-Growth</h3>
                <div className="algo-stat">
                  <Clock size={16} />
                  <span>{comparison.comparison.fpgrowth.execution_time_ms} ms</span>
                </div>
                <div className="algo-stat">
                  <Package size={16} />
                  <span>{comparison.comparison.fpgrowth.n_itemsets} frequent itemsets</span>
                </div>
                <div className="algo-stat">
                  <Award size={16} />
                  <span>{comparison.comparison.fpgrowth.n_rules} rules generated</span>
                </div>
              </div>
            </div>
          )}
        </DashSection>

        {/* ── Association Rules ─────────────────────────────────── */}
        <DashSection
          id="assoc-rules"
          title="Top Association Rules"
          subtitle={rules ? `${rules.n_rules} rules found via ${rules.algorithm} in ${rules.execution_time_ms}ms` : 'Loading…'}
        >
          {!rules ? (
            <div className="skeleton" style={{ height: 300, borderRadius: 12 }} />
          ) : rules.rules?.length === 0 ? (
            <p className="text-muted">No rules found. Try lowering min_support in config.</p>
          ) : (
            <div className="table-wrapper">
              <table className="table" id="rules-table">
                <thead>
                  <tr>
                    <th>If bought (Antecedents)</th>
                    <th>Then likely (Consequents)</th>
                    <th>Support</th>
                    <th>Confidence</th>
                    <th>Lift</th>
                  </tr>
                </thead>
                <tbody>
                  {rules.rules.slice(0, 15).map((rule, i) => (
                    <tr key={i}>
                      <td>
                        <div className="rule-items">
                          {rule.antecedents.slice(0, 2).map((id, j) => (
                            <span key={j} className="rule-item rule-item-purple">{id}</span>
                          ))}
                        </div>
                      </td>
                      <td>
                        <div className="rule-items">
                          {rule.consequents.slice(0, 2).map((id, j) => (
                            <span key={j} className="rule-item rule-item-cyan">{id}</span>
                          ))}
                        </div>
                      </td>
                      <td><span className="badge badge-purple">{(rule.support * 100).toFixed(1)}%</span></td>
                      <td><span className="badge badge-cyan">{(rule.confidence * 100).toFixed(1)}%</span></td>
                      <td><span className="badge badge-amber">{rule.lift?.toFixed(2)}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </DashSection>

        {/* ── Sequential Patterns ───────────────────────────────── */}
        <DashSection
          id="seq-patterns"
          title="Sequential Purchase Patterns"
          subtitle={
            patterns 
              ? `${patterns.n_patterns} patterns found via PrefixSpan across ${patterns.n_sequences} sequences`
              : 'Mining sequential patterns (may take up to 60 seconds on first load)...'
          }
        >
          {!patterns ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px', padding: '40px', color: '#8894ab' }}>
              <div style={{ width: '20px', height: '20px', border: '2px solid #8894ab', borderTop: '2px solid #60a5fa', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
              <span>Mining sequential patterns from purchase history...</span>
            </div>
          ) : patterns.error ? (
            <p className="text-muted" style={{ color: '#ef4444' }}>Error: {patterns.error}</p>
          ) : patterns.patterns?.length === 0 ? (
            <p className="text-muted">No patterns found. Check SEQ_MIN_SUPPORT in config or ensure sufficient data.</p>
          ) : (
            <div className="patterns-grid">
              {patterns.patterns.slice(0, 12).map((p, i) => (
                <div key={i} className="pattern-card card" id={`pattern-${i}`}>
                  <div className="pattern-index">#{i + 1}</div>
                  <div className="pattern-sequence">
                    {p.pattern.map((itemset, j) => (
                      <div key={j} className="pattern-step">
                        <div className="pattern-itemset">
                          {itemset.map(iid => <span key={iid} className="item-chip">{iid}</span>)}
                        </div>
                        {j < p.pattern.length - 1 && <div className="pattern-arrow">→</div>}
                      </div>
                    ))}
                  </div>
                  <div className="pattern-meta">
                    <span className="badge badge-green">Support: {(p.support * 100).toFixed(1)}%</span>
                    <span className="text-sm">Count: {p.count}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </DashSection>
      </div>
    </div>
  );
}
