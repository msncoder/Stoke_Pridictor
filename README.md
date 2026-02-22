# Stock Market Analyzer & Predictor (SMAP) 📈

SMAP is a comprehensive end-to-end system designed to predict daily closing and hourly stock prices for various stocks on the Pakistan Stock Exchange (PSX). It leverages real-time data scraping, technical indicator analysis, and deep learning (LSTM) to provide timely guidance for investors.

---

## 🚀 Key Features
- **Live Data Pipeline:** Automated scraping from sources like Investing.com and Dawn.com.
- **Deep Learning Predictions:** Uses Univariate LSTM for hourly price movement forecasting.
- **Technical Analysis:** Calculates RSI, MA, and other custom indicators for daily trends.
- **Modern Web Dashboard:** A responsive FastAPI backend and React 19 frontend for visualizing predictions and historical data.
- **Automated Scheduling:** Background tasks via `apscheduler` to run the full pipeline daily.

---

## 🛠️ Tech Stack
- **Backend:** FastAPI (Python 3.10+), Uvicorn, APScheduler.
- **Frontend:** React 19, Vite, TailwindCSS, Lucide-React, Recharts.
- **Database:** MySQL.
- **Scraping:** Selenium (Chrome), BeautifulSoup4.
- **Analysis/ML:** TensorFlow (LSTM), NLTK, Pysentiment.

---

## ⚙️ Setup & Installation

### 1. Prerequisites
- Python 3.10+
- Node.js (v18+)
- MySQL Server
- Google Chrome (for Selenium)

### 2. Environment Configuration
Create a `.env` file in the root directory based on `.env_example`:
```bash
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=smap_db
```

### 3. Backend Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Frontend Setup
```bash
cd web/frontend
npm install
```

---

## 🏃 Running the Application

### Option A: Manual Data Refresh (Pipeline)
To import historical data or refresh technical indicators manually:
```bash
# Import historical data
python db/import_historical.py --all

# Run all scrapers and update predictions
python web/backend/pipeline.py
```

### Option B: Web Application (Production-like)
Run both backend and frontend to view the dashboard.

**Backend:**
```bash
uvicorn web.backend.main:app --reload
```

**Frontend:**
```bash
cd web/frontend
npm run dev
```

---

## 📂 Project Structure
- `web/backend/`: FastAPI application and pipeline logic.
- `web/frontend/`: React Vite application.
- `Scrapers/`: Selenium and BS4 scripts for data collection.
- `Technical_Analysis/`: Scripts for calculating stock indicators.
- `Prediction/`: LSTM model training and prediction logic.
- `config.py`: Centralized database and configuration management.

---

## 📊 Stock Coverage
Current predictions are active for:
- HBL (Habib Bank Ltd)
- UBL (United Bank Ltd)
- ENGRO FERTILIZER
- PSO (Pakistan State Oil)
- OGDCL (Oil & Gas Development Company Ltd)

---

## 📜 License
This project is part of a Final Year Project (FYP). For academic or professional inquiries, please contact the repository owner.
