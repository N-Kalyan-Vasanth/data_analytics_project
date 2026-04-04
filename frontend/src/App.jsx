// App.jsx — Root component with React Router and global providers
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { CartProvider } from './context/CartContext';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Shop from './pages/Shop';
import ProductDetail from './pages/ProductDetail';
import Cart from './pages/Cart';
import Dashboard from './pages/Dashboard';
import './index.css';

export default function App() {
  return (
    <BrowserRouter>
      <CartProvider>
        <Navbar />
        <Routes>
          <Route path="/"            element={<Home />} />
          <Route path="/shop"        element={<Shop />} />
          <Route path="/product/:id" element={<ProductDetail />} />
          <Route path="/cart"        element={<Cart />} />
          <Route path="/dashboard"   element={<Dashboard />} />
          {/* Fallback */}
          <Route path="*" element={
            <div className="page container text-center py-12">
              <h1 className="heading-xl" style={{ fontSize: '4rem' }}>404</h1>
              <p className="text-muted">Page not found.</p>
            </div>
          } />
        </Routes>
      </CartProvider>
    </BrowserRouter>
  );
}
