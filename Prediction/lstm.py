"""
LSTM Stock Price Prediction → MySQL `predictions` table
Reads historical_prices from MySQL, trains LSTM, stores predictions in MySQL.

Python 3.10+ / Windows 11. No CSV I/O. Memcached optional.
"""
import sys
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
from sklearn.preprocessing import MinMaxScaler

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

warnings.filterwarnings("ignore")

try:
    from keras.models import Sequential
    from keras.layers import Dense, LSTM
    KERAS_AVAILABLE = True
except ImportError:
    print("[lstm] WARNING: keras/tensorflow not installed. pip install tensorflow keras")
    KERAS_AVAILABLE = False

STOCKS     = ["UBL", "PSO", "HBL", "ENGRO", "OGDC"]
EPOCHS     = 10
BATCH_SIZE = 1
NEURONS    = 1
FORECAST   = 3   # days ahead to forecast


# ── Data ──────────────────────────────────────────────────────────

def load_prices(symbol):
    rows = config.fetchall(
        "SELECT trade_date, close_price FROM historical_prices "
        "WHERE symbol=%s ORDER BY trade_date ASC",
        (symbol,),
    )
    if not rows:
        print(f"[lstm] No data for {symbol} in MySQL.")
    return rows


# ── Transforms ────────────────────────────────────────────────────

def difference(data, interval=1):
    return [data[i] - data[i - interval] for i in range(interval, len(data))]


def inv_diff(last, val):
    return val + last


def to_supervised(data, lag=1):
    result = np.zeros((len(data) - lag, lag + 1))
    for i in range(len(data) - lag):
        result[i, :lag] = data[i: i + lag]
        result[i, lag]  = data[i + lag]
    return result


# ── Model ─────────────────────────────────────────────────────────

def fit_lstm(train, batch, epochs, neurons):
    X, y = train[:, :-1], train[:, -1]
    X = X.reshape(X.shape[0], X.shape[1], 1)
    model = Sequential([
        LSTM(neurons, input_shape=(X.shape[1], X.shape[2])),
        Dense(1),
    ])
    model.compile(loss="mean_squared_error", optimizer="adam")
    model.fit(X, y, epochs=epochs, batch_size=batch, verbose=0, shuffle=False)
    return model


def forecast_step(model, batch, X):
    X = X.reshape(1, 1, len(X))
    return model.predict(X, batch_size=batch, verbose=0)[0, 0]


# ── Save ──────────────────────────────────────────────────────────

def save_prediction(symbol, predicted_value, target_period, direction="NEUTRAL"):
    config.execute(
        """
        INSERT INTO predictions
          (symbol, model_type, predicted_at, target_period,
           predicted_value, direction)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (symbol, "LSTM", datetime.now(), target_period, predicted_value, direction),
    )


# ── Processing ────────────────────────────────────────────────────

def process_stock(symbol):
    print(f"\n[lstm] ── {symbol} ──────────────────────────────────")
    rows = load_prices(symbol)
    if not rows or len(rows) < 50:
        print(f"[lstm] Skipping {symbol} — need ≥50 data points (have {len(rows)})")
        return

    raw = [float(r["close_price"]) for r in rows]
    dates = [r["trade_date"] for r in rows]

    diff_vals = difference(raw, 1)
    supervised = to_supervised(diff_vals, 1)

    train_size = len(supervised) - 10
    train, test = supervised[:train_size], supervised[train_size:]

    scaler = MinMaxScaler(feature_range=(-1, 1))
    train_sc = scaler.fit_transform(train)
    test_sc  = scaler.transform(test)

    print(f"[lstm] Training LSTM ({EPOCHS} epochs, {len(train)} samples)…")
    model = fit_lstm(train_sc, BATCH_SIZE, EPOCHS, NEURONS)

    # Walk-forward test predictions
    predictions = []
    for i in range(len(test_sc)):
        X = test_sc[i, :-1]
        yhat  = forecast_step(model, BATCH_SIZE, X)
        yhat_r = scaler.inverse_transform([[*X, yhat]])[0, -1]
        real_val = inv_diff(raw[train_size + i], yhat_r)

        predictions.append(real_val)
        direction = "BUY" if real_val > raw[train_size + i] else "SELL" if real_val < raw[train_size + i] else "NEUTRAL"
        date_label = str(dates[train_size + i + 1]) if (train_size + i + 1) < len(dates) else "test"
        save_prediction(symbol, round(real_val, 4), date_label, direction)

    # Future forecast
    last_X = test_sc[-1, :-1]
    last_obs = raw[-1]
    for step in range(1, FORECAST + 1):
        yhat  = forecast_step(model, BATCH_SIZE, last_X)
        yhat_r = scaler.inverse_transform([[*last_X, yhat]])[0, -1]
        future_val = inv_diff(last_obs, yhat_r)
        direction = "BUY" if future_val > last_obs else "SELL" if future_val < last_obs else "NEUTRAL"
        save_prediction(symbol, round(future_val, 4), f"future_{step}", direction)
        last_obs = future_val
        print(f"[lstm] {symbol} Future+{step}: {future_val:.2f} [{direction}] → MySQL")

    # Update Memcached counter (optional)
    mc = config.get_memcache_client()
    if mc:
        try:
            mc.set("lstm_counter", (mc.get("lstm_counter") or 0) + 1)
        except Exception:
            pass


def main():
    if not KERAS_AVAILABLE:
        print("[lstm] Cannot run — install TensorFlow: pip install tensorflow keras")
        return

    print(f"[lstm] Started at {datetime.now()}")
    for symbol in STOCKS:
        process_stock(symbol)
    print(f"\n[lstm] All stocks done. Predictions stored in MySQL `predictions`.")


if __name__ == "__main__":
    main()