// Cart.jsx — Shopping cart page
import { Trash2, Plus, Minus, ShoppingBag, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import './Cart.css';

export default function Cart() {
  const { items, total, count, removeItem, updateItem, clearAll, loading } = useCart();
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className="page container">
        <h1 className="heading-lg" style={{ paddingTop: 40, paddingBottom: 32 }}>Your Cart</h1>
        <div className="skeleton" style={{ height: 300, borderRadius: 20 }} />
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="page container cart-empty">
        <ShoppingBag size={64} style={{ color: 'var(--text-muted)', marginBottom: 16 }} />
        <h2 className="heading-md">Your cart is empty</h2>
        <p className="text-muted">Add some products to get started.</p>
        <button className="btn btn-primary mt-4" onClick={() => navigate('/shop')} id="go-shop-btn">
          Browse Products <ArrowRight size={18} />
        </button>
      </div>
    );
  }

  return (
    <div className="cart-page page">
      <div className="container">
        <div className="cart-header">
          <h1 className="heading-lg">Your Cart <span className="cart-count-label">({count} items)</span></h1>
          <button className="btn btn-danger btn-sm" onClick={clearAll} id="clear-cart-btn">
            <Trash2 size={16} /> Clear All
          </button>
        </div>

        <div className="cart-layout">
          {/* Cart items */}
          <div className="cart-items-list">
            {items.map(ci => (
              <div key={ci.cart_item_id} className="cart-item card" id={`cart-item-${ci.cart_item_id}`}>
                <div className="cart-item-emoji">📦</div>
                <div className="cart-item-info">
                  <p
                    className="cart-item-name"
                    onClick={() => navigate(`/product/${ci.item_id}`)}
                    style={{ cursor: 'pointer' }}
                  >
                    {ci.item_name}
                  </p>
                  <p className="text-sm">Unit price: ₽{ci.unit_price}</p>
                </div>
                <div className="cart-item-qty">
                  <button
                    className="qty-btn"
                    onClick={() => updateItem(ci.cart_item_id, ci.quantity - 1)}
                    disabled={ci.quantity <= 1}
                    id={`dec-qty-${ci.cart_item_id}`}
                  >
                    <Minus size={14} />
                  </button>
                  <span className="qty-val">{ci.quantity}</span>
                  <button
                    className="qty-btn"
                    onClick={() => updateItem(ci.cart_item_id, ci.quantity + 1)}
                    id={`inc-qty-${ci.cart_item_id}`}
                  >
                    <Plus size={14} />
                  </button>
                </div>
                <div className="cart-item-subtotal">₽{ci.subtotal}</div>
                <button
                  className="cart-remove-btn"
                  onClick={() => removeItem(ci.cart_item_id)}
                  id={`remove-${ci.cart_item_id}`}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>

          {/* Order summary */}
          <div className="cart-summary card">
            <h2 className="heading-md mb-4">Order Summary</h2>
            <div className="summary-row"><span>Subtotal</span><span>₽{total.toFixed(2)}</span></div>
            <div className="summary-row"><span>Shipping</span><span className="text-muted">Free</span></div>
            <div className="summary-row summary-total"><span>Total</span><span>₽{total.toFixed(2)}</span></div>
            <button className="btn btn-primary w-full mt-4" id="checkout-btn">
              Proceed to Checkout <ArrowRight size={18} />
            </button>
            <button className="btn btn-ghost w-full mt-2" onClick={() => navigate('/shop')} id="continue-shopping-btn">
              Continue Shopping
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
