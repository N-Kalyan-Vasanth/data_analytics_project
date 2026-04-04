// ProductDetail.jsx — Individual product page with recommendations
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ShoppingCart, ArrowLeft, Package, Users, Zap } from 'lucide-react';
import { getProduct, getRecommendations, getNextRecs } from '../api';
import { useCart } from '../context/CartContext';
import './ProductDetail.css';

export default function ProductDetail() {
  const { id }     = useParams();
  const navigate   = useNavigate();
  const { addItem } = useCart();

  const [product, setProduct]     = useState(null);
  const [assocRecs, setAssocRecs] = useState([]);
  const [seqRecs, setSeqRecs]     = useState([]);
  const [loading, setLoading]     = useState(true);
  const [added, setAdded]         = useState(false);

  useEffect(() => {
    const itemId = parseInt(id);
    setLoading(true);

    Promise.all([
      getProduct(itemId),
      getRecommendations(itemId, 'fpgrowth').catch(() => ({ recommendations: [] })),
      getNextRecs(itemId).catch(() => ({ next_recommendations: [] })),
    ]).then(([prod, recs, nxt]) => {
      setProduct(prod);
      setAssocRecs(recs.recommendations || []);
      setSeqRecs(nxt.next_recommendations || []);
    }).catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  const handleAdd = async () => {
    if (added) return;
    await addItem(parseInt(id), 1);
    setAdded(true);
    setTimeout(() => setAdded(false), 2000);
  };

  if (loading) {
    return (
      <div className="page container" style={{ paddingTop: 100 }}>
        <div className="skeleton" style={{ height: 400, borderRadius: 20 }} />
      </div>
    );
  }

  if (!product) {
    return (
      <div className="page container text-center py-12">
        <p className="heading-md">Product not found</p>
        <button className="btn btn-primary mt-4" onClick={() => navigate('/shop')}>
          Back to Shop
        </button>
      </div>
    );
  }

  return (
    <div className="product-detail page">
      <div className="container">
        {/* Back button */}
        <button className="btn btn-ghost back-btn" onClick={() => navigate(-1)} id="back-btn">
          <ArrowLeft size={18} /> Back
        </button>

        {/* Product hero */}
        <div className="detail-hero card">
          <div className="detail-image">
            <span className="detail-emoji">📦</span>
          </div>
          <div className="detail-info">
            <span className="badge badge-cyan">{product.category_name || 'Uncategorised'}</span>
            <h1 className="detail-name">{product.name}</h1>
            <div className="detail-price">₽{product.avg_price > 0 ? product.avg_price.toFixed(0) : 'N/A'}</div>
            <p className="text-muted">Item ID: #{product.id} · {product.total_sold?.toLocaleString()} units sold</p>
            <button
              className={`btn btn-primary btn-lg add-btn ${added ? 'added' : ''}`}
              onClick={handleAdd}
              id="detail-add-to-cart-btn"
            >
              <ShoppingCart size={20} />
              {added ? 'Added to Cart ✓' : 'Add to Cart'}
            </button>
          </div>
        </div>

        {/* Frequently Bought Together (Apriori / FP-Growth) */}
        {assocRecs.length > 0 && (
          <section className="recs-section">
            <div className="recs-header">
              <div className="recs-icon recs-icon-purple"><Zap size={18} /></div>
              <div>
                <h2 className="heading-md">Frequently Bought Together</h2>
                <p className="text-muted">Based on FP-Growth association rules</p>
              </div>
            </div>
            <div className="recs-grid">
              {assocRecs.map(rec => (
                <div
                  key={rec.item_id}
                  className="rec-card"
                  onClick={() => navigate(`/product/${rec.item_id}`)}
                  id={`fbt-${rec.item_id}`}
                >
                  <div className="rec-emoji">📦</div>
                  <p className="rec-name">{rec.name}</p>
                  <p className="rec-price">₽{rec.avg_price?.toFixed(0)}</p>
                  <div className="rec-meta">
                    <span className="badge badge-purple">Confidence: {(rec.confidence * 100).toFixed(0)}%</span>
                    <span className="badge badge-cyan">Lift: {rec.lift?.toFixed(2)}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Customers Also Buy Next (PrefixSpan) */}
        {seqRecs.length > 0 && (
          <section className="recs-section">
            <div className="recs-header">
              <div className="recs-icon recs-icon-amber"><Users size={18} /></div>
              <div>
                <h2 className="heading-md">Customers Also Buy Next</h2>
                <p className="text-muted">Sequential patterns mined via PrefixSpan</p>
              </div>
            </div>
            <div className="recs-grid">
              {seqRecs.map(rec => (
                <div
                  key={rec.item_id}
                  className="rec-card"
                  onClick={() => navigate(`/product/${rec.item_id}`)}
                  id={`seq-${rec.item_id}`}
                >
                  <div className="rec-emoji">🛒</div>
                  <p className="rec-name">{rec.name}</p>
                  <p className="rec-price">₽{rec.avg_price?.toFixed(0)}</p>
                  <div className="rec-meta">
                    <span className="badge badge-amber">Score: {(rec.score * 100).toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {assocRecs.length === 0 && seqRecs.length === 0 && (
          <div className="card text-center py-12 mt-6">
            <Package size={40} style={{ margin: '0 auto 12px', color: 'var(--text-muted)' }} />
            <p className="text-muted">No recommendations yet. Run the ML pipeline from the Analytics Dashboard.</p>
          </div>
        )}
      </div>
    </div>
  );
}
