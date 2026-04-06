# 🛒 E-Commerce Analytics Platform

A full-stack data analytics platform built for the **Online Retail** dataset, featuring real-time machine learning–powered insights including association rule mining, sequential pattern discovery, and time-series sales forecasting.

---

## 📦 Dataset

**Source:** Online Retail II (UCI Machine Learning Repository)  
**Size:** ~525,000 transactions | 4,000+ products | 4,000+ customers  
**Period:** December 2009 – December 2011  

| Attribute | Description |
|---|---|
| `Invoice` | Unique transaction ID (prefix `C` = cancellation) |
| `StockCode` | Alphanumeric product ID |
| `Description` | Product name |
| `Quantity` | Units purchased per transaction |
| `InvoiceDate` | Date and time of transaction |
| `Price` | Unit price in GBP (£) |
| `Customer ID` | Unique customer identifier |
| `Country` | Country of the customer |

---

## 🧠 Machine Learning Algorithms

### 1. Apriori
Mines frequent itemsets and generates association rules by iteratively pruning infrequent combinations.
- **Min Support:** 0.02 (2%)
- **Min Confidence:** 0.2 (20%)
- **Min Lift:** 1.0
- **Output:** Support, Confidence, Lift per rule

### 2. FP-Growth (Frequent Pattern Growth)
A faster alternative to Apriori that uses a compressed FP-Tree structure to avoid repeated database scans.
- **Same thresholds as Apriori** — used for direct performance comparison
- **Output:** Same association rules, in significantly less time

### 3. ARIMA (AutoRegressive Integrated Moving Average)
Forecasts future monthly sales based on historical time-series data.
- **Order:** (1, 1, 1) — one AR term, one differencing pass, one MA term
- **Forecast Horizon:** 3 months ahead
- **Metrics:** AIC, BIC, Fitted vs Actual

### 4. Moving Average (MA)
A smoothing technique that averages the last N months of sales to predict the next month.
- **Window:** Rolling 3-month window
- **Output:** Smoothed historical trend + short-term forecast

### 5. PrefixSpan (Sequential Pattern Mining)
Discovers ordered purchase patterns — what customers tend to buy across successive months.
- **Min Support:** 0.001 (0.1%)
- **Max Pattern Length:** 3 steps
- **Output:** Sequences like `[StockCode A] → [StockCode B]`

---

## 🗂️ Project Structure

```
da_project/
├── backend/
│   ├── app.py                  # Flask application entry point
│   ├── config.py               # ML thresholds & app configuration
│   ├── models.py               # SQLAlchemy database models
│   ├── seed_db.py              # Populates SQLite DB from CSV
│   ├── data/
│   │   └── online_retail.csv   # Cleaned dataset (converted from .xlsx)
│   ├── db/
│   │   ├── ecommerce.db        # SQLite database
│   │   └── ml_cache.json       # Cached ML results (auto-generated)
│   ├── ml/
│   │   ├── preprocessing.py    # Data cleaning & feature engineering
│   │   ├── apriori_module.py   # Apriori algorithm implementation
│   │   ├── fpgrowth_module.py  # FP-Growth algorithm implementation
│   │   ├── timeseries_module.py# ARIMA + Moving Average
│   │   └── sequential_module.py# PrefixSpan implementation
│   ├── routes/
│   │   ├── products.py         # GET /api/products
│   │   ├── patterns.py         # GET /api/patterns/sequential
│   │   ├── predictions.py      # GET /api/predictions
│   │   ├── recommendations.py  # GET /api/recommendations
│   │   └── cart.py             # Cart API
│   └── venv/                   # Python virtual environment
│
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── Home.jsx        # Landing page with dataset stats
    │   │   ├── Dashboard.jsx   # Analytics dashboard
    │   │   └── Products.jsx    # Product listing & detail
    │   └── api.js              # Axios API client
    └── package.json
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm / npx

### Backend Setup

```powershell
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install flask flask-sqlalchemy flask-cors pandas numpy mlxtend statsmodels openpyxl scikit-learn

# Seed the database (run ONCE)
python seed_db.py

# Start the backend server
python app.py
```

The Flask API will be available at `http://localhost:5000`.

### Frontend Setup

```powershell
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/products` | List all products (paginated) |
| `GET` | `/api/products/top` | Top 8 best-selling products |
| `GET` | `/api/products/<id>` | Single product details |
| `GET` | `/api/predictions/summary` | ARIMA/MA model KPIs |
| `GET` | `/api/predictions/all` | Full historical + forecast data |
| `GET` | `/api/rules?algo=apriori` | Association rules (Apriori or FP-Growth) |
| `GET` | `/api/rules/compare` | Apriori vs FP-Growth benchmark |
| `GET` | `/api/patterns/sequential` | Sequential purchase patterns (PrefixSpan) |
| `GET` | `/api/recommendations/<id>` | Frequently bought together |

---

## 📊 Dashboard Features

- **KPI Cards** — Total items sold, Total revenue, Avg monthly sales, Growth rate
- **ARIMA Chart** — Fitted vs actual monthly sales (area chart)
- **Moving Average Chart** — Smoothed trend overlay
- **Top Selling Products** — Horizontal bar chart by StockCode
- **Apriori vs FP-Growth** — Side-by-side runtime & rule comparison
- **Top Association Rules** — Table with Support, Confidence, Lift
- **Sequential Patterns** — PrefixSpan pattern cards with step-by-step arrows

---

## 👥 Team

**Institution:** Data Analytics Project — Semester 6  
**Repository:** [N-Kalyan-Vasanth/data_analytics_project](https://github.com/N-Kalyan-Vasanth/data_analytics_project)
