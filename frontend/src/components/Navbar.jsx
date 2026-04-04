// Navbar.jsx — Navigation bar with cart count badge
import { Link, useLocation } from 'react-router-dom';
import { ShoppingCart, BarChart3, Package, Home, Layers } from 'lucide-react';
import { useCart } from '../context/CartContext';
import './Navbar.css';

const NAV_LINKS = [
  { to: '/',          label: 'Home',      icon: Home },
  { to: '/shop',      label: 'Shop',      icon: Package },
  { to: '/dashboard', label: 'Analytics', icon: BarChart3 },
];

export default function Navbar() {
  const { count } = useCart();
  const location = useLocation();

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        {/* Logo */}
        <Link to="/" className="navbar-logo">
          <div className="navbar-logo-icon">
            <Layers size={18} color="white" />
          </div>
          DataMine
        </Link>

        {/* Nav links */}
        <div className="navbar-links">
          {NAV_LINKS.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className={`nav-link ${location.pathname === to ? 'active' : ''}`}
            >
              <Icon size={16} />
              {label}
            </Link>
          ))}
        </div>

        {/* Cart button */}
        <div className="navbar-actions">
          <Link to="/cart" className="cart-btn">
            <ShoppingCart size={18} />
            Cart
            {count > 0 && <span className="cart-count">{count}</span>}
          </Link>
        </div>
      </div>
    </nav>
  );
}
