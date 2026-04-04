// ProductCard.jsx — E-commerce product card with cart integration
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShoppingCart, Check, TrendingUp } from 'lucide-react';
import { useCart } from '../context/CartContext';
import './ProductCard.css';

// Deterministic emoji picker based on item id / category
const CATEGORY_EMOJIS = {
  'PC': '💻', 'Game': '🎮', 'Book': '📚', 'Music': '🎵',
  'Movie': '🎬', 'Phone': '📱', 'Toy': '🧸', 'Software': '💾',
  'Clean': '🧹', 'Food': '🍕', 'Gift': '🎁', 'Sport': '⚽',
};

function getEmoji(categoryName = '', itemId = 0) {
  for (const [key, emoji] of Object.entries(CATEGORY_EMOJIS)) {
    if (categoryName.toLowerCase().includes(key.toLowerCase())) return emoji;
  }
  const defaults = ['📦', '🛍️', '⭐', '🔮', '🎯', '🏆', '💎', '🚀'];
  return defaults[itemId % defaults.length];
}

export default function ProductCard({ item }) {
  const { addItem } = useCart();
  const navigate = useNavigate();
  const [adding, setAdding] = useState(false);

  const handleAdd = async (e) => {
    e.stopPropagation(); // don't navigate to product detail
    if (adding) return;
    setAdding(true);
    try {
      await addItem(item.id, 1);
    } catch (err) {
      console.error('Failed to add item:', err);
    }
    setTimeout(() => setAdding(false), 1200);
  };

  const emoji = getEmoji(item.category_name, item.id);

  return (
    <div
      className="product-card animate-fade"
      onClick={() => navigate(`/product/${item.id}`)}
      role="button"
      aria-label={`View ${item.name}`}
      id={`product-card-${item.id}`}
    >
      {/* Image area */}
      <div className="product-card-image">
        <span className="product-card-emoji">{emoji}</span>
        {item.total_sold > 1000 && (
          <div className="product-sold-badge">
            <TrendingUp size={10} style={{ display: 'inline', marginRight: 3 }} />
            {item.total_sold.toLocaleString()} sold
          </div>
        )}
      </div>

      {/* Body */}
      <div className="product-card-body">
        {item.category_name && (
          <span className="product-card-category">{item.category_name}</span>
        )}
        <p className="product-card-name">{item.name}</p>

        <div className="product-card-footer">
          <span className="product-price">
            ₽{item.avg_price > 0 ? item.avg_price.toFixed(0) : 'N/A'}
          </span>

          <button
            className={`add-to-cart-btn ${adding ? 'adding' : ''}`}
            onClick={handleAdd}
            aria-label="Add to cart"
            id={`add-to-cart-${item.id}`}
          >
            {adding ? <Check size={16} /> : <ShoppingCart size={16} />}
          </button>
        </div>
      </div>
    </div>
  );
}
