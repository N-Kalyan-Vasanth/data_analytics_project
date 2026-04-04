# DataMine E-Commerce Platform

A full-stack data-driven e-commerce platform featuring integrated ML data mining algorithms (Apriori, FP-Growth, ARIMA/Moving Average, and PrefixSpan) for recommendations and sales forecasting.

## Architecture

- **Backend**: Python / Flask, SQLAlchemy (SQLite)
- **Frontend**: React + Vite
- **Data Mining**: `mlxtend` (Apriori/FP-Growth), PrefixSpan (custom implementation)
- **Time Series**: `statsmodels` (ARIMA), Moving Average

## Setup Instructions

### 1. Backend Setup

First, open a terminal in the `backend` folder and install the Python dependencies. It's recommended to use a virtual environment.

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

### 2. Seed the Database

Before running the server, you must seed the SQLite database using the provided CSV files. The CSV data files have already been placed in `backend/data/`.

Run the seeder script (this will take a few moments as it batches the sales data):
```bash
python seed_db.py
```

### 3. Start the Backend Server

Start the Flask backend (it runs on port 5000):
```bash
python app.py
```

### 4. Frontend Setup

Open a **new** terminal in the `frontend` directory and install the Node.js packages:
```bash
cd frontend
npm install
```

### 5. Start the Frontend Server

Run the Vite development server:
```bash
npm run dev
```

The application will now be running at `http://localhost:5173/`, and all `/api` requests will proxy to the backend automatically!
