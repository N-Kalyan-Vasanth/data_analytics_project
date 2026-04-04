// CartContext.jsx — Global cart state using React Context + useReducer

import { createContext, useContext, useReducer, useEffect, useCallback } from 'react';
import { getCart, addToCart as apiAdd, removeCartItem as apiRemove, clearCart as apiClear, updateCartItem as apiUpdate } from '../api';

// ── State shape ────────────────────────────────────────────────────
const initialState = { items: [], total: 0, count: 0, loading: false };

// ── Reducer ────────────────────────────────────────────────────────
function cartReducer(state, action) {
  switch (action.type) {
    case 'SET_CART':
      return { ...state, ...action.payload, loading: false };
    case 'LOADING':
      return { ...state, loading: true };
    default:
      return state;
  }
}

// ── Context ────────────────────────────────────────────────────────
const CartContext = createContext(null);

export function CartProvider({ children }) {
  const [state, dispatch] = useReducer(cartReducer, initialState);

  const fetchCart = useCallback(async () => {
    try {
      dispatch({ type: 'LOADING' });
      const data = await getCart();
      dispatch({ type: 'SET_CART', payload: { items: data.cart, total: data.total, count: data.count } });
    } catch (e) {
      dispatch({ type: 'SET_CART', payload: { items: [], total: 0, count: 0 } });
    }
  }, []);

  useEffect(() => { fetchCart(); }, [fetchCart]);

  const addItem = async (itemId, qty = 1) => {
    await apiAdd(itemId, qty);
    fetchCart();
  };

  const removeItem = async (cartItemId) => {
    await apiRemove(cartItemId);
    fetchCart();
  };

  const updateItem = async (cartItemId, qty) => {
    await apiUpdate(cartItemId, qty);
    fetchCart();
  };

  const clearAll = async () => {
    await apiClear();
    fetchCart();
  };

  return (
    <CartContext.Provider value={{ ...state, addItem, removeItem, updateItem, clearAll, fetchCart }}>
      {children}
    </CartContext.Provider>
  );
}

export const useCart = () => useContext(CartContext);
