# Stock Predictor Backend

This project serves as the backend for the SMAP-FYP Stock Prediction system, handling automated data ingestion, technical indicator calculation, and LSTM-based forecasting.

## Architecture & Project Structure

The backend is built with **FastAPI** and uses **Neon PostgreSQL** for persistent data storage.

- **`main.py`**: Entry point for the REST API.
- **`pipeline.py`**: Orchestrates the data pipeline (Scrape -> Analyze -> Predict).
- **`config.py`**: Central configuration and database connection utilities.
- **`Scrapers/`**: Modules for scraping stock prices, news, and economic data.
- **`Technical_Analysis/`**: Tools for calculating RSI, MACD, and other indicators.
- **`Prediction/`**: LSTM model implementation and forecasting logic.
- **`db/`**: Schema definitions and database initialization scripts.

## Setup & Installation

### 1. Environment Configuration

1.  **Python Version**: Ensure you're using Python 3.10.8+.
2.  **Virtual Environment**:
    ```powershell
    python -m venv backend_env
    .\backend_env\Scripts\Activate.ps1
    ```
3.  **Dependencies**:
    ```powershell
    pip install -r requirements.txt
    ```

### 2. Database & Variables

1.  Copy `.env_example` to `.env`.
2.  Update `DATABASE_URL` with your **Neon PostgreSQL** connection string.
3.  Ensure your schema is up to date (see `db/schema.sql`).

## Running the Application

### Start the API Server

```powershell
python main.py
```
*Accessible at `http://localhost:8000`.*

### Trigger the Data Pipeline

To manually run the full pipeline (Scraping -> Indicators -> Predictions):

```powershell
python pipeline.py
```

## API Documentation

The following endpoints are available:

- `GET /api/stocks`: List all available stock symbols.
- `GET /api/predictions/{symbol}`: Latest AI-generated price predictions.
- `GET /api/historical/{symbol}`: Last 100 days of historical price data.
- `POST /api/trigger`: Trigger the backend pipeline to update all data.

## Features
- **Automated Scraping**: Daily stock price updates from multiple sources.
- **LSTM Predictions**: Advanced machine learning for multi-day price forecasting.
- **Technical Analysis**: Real-time calculation of key trading indicators.
- **RESTful API**: Clean interface for frontend integration.
