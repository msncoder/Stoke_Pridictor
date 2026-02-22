from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
import uvicorn
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from web.backend import pipeline

app = FastAPI(title="SMAP-FYP Stock Prediction API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Scheduler Setup ---
scheduler = BackgroundScheduler()

@app.on_event("startup")
def start_scheduler():
    # Schedule the full pipeline to run daily at midnight
    scheduler.add_job(pipeline.run_full_pipeline, 'cron', hour=0, minute=0)
    scheduler.start()
    print("[Main] Scheduler started. Pipeline scheduled for 00:00 daily.")

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"message": "SMAP-FYP API is running"}

@app.get("/api/stocks")
def get_stocks():
    """Return available stock symbols."""
    rows = config.fetchall("SELECT DISTINCT symbol FROM historical_prices")
    return {"stocks": [r['symbol'] for r in rows]}

@app.get("/api/predictions/{symbol}")
def get_predictions(symbol: str):
    """Return latest predictions for a given stock."""
    rows = config.fetchall(
        "SELECT * FROM predictions WHERE symbol = %s ORDER BY predicted_at DESC LIMIT 50",
        (symbol,)
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No predictions found for {symbol}")
    return {"symbol": symbol, "predictions": rows}

@app.get("/api/historical/{symbol}")
def get_historical(symbol: str):
    """Return historical prices for a given stock."""
    rows = config.fetchall(
        "SELECT trade_date, close_price FROM historical_prices WHERE symbol = %s ORDER BY trade_date DESC LIMIT 100",
        (symbol,)
    )
    # Reverse to have chronological order for charts
    return {"symbol": symbol, "data": rows[::-1]}

@app.post("/api/trigger")
def trigger_pipeline(background_tasks: BackgroundTasks):
    """Manually trigger the full pipeline in the background."""
    background_tasks.add_task(pipeline.run_full_pipeline)
    return {"message": "Pipeline triggered in background", "status": "processing"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
