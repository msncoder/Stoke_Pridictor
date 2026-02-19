"""
Actual vs Predicted Tracker → MySQL
Fills in `actual_value`, `difference`, and `pct_error` for
LSTM predictions that have a matching historical price.

Python 3.10+ / Windows 11. No CSV I/O.
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

STOCKS = ["UBL", "PSO", "HBL", "ENGRO", "OGDC"]


def update_actuals(symbol):
    """
    For each unfilled prediction row whose target_period is a date string
    (not future_*), look up the actual close price and compute accuracy.
    """
    pending = config.fetchall(
        """
        SELECT p.id, p.target_period, p.predicted_value
        FROM predictions p
        WHERE p.symbol = %s
          AND p.actual_value IS NULL
          AND p.target_period NOT LIKE 'future_%%'
        ORDER BY p.predicted_at ASC
        """,
        (symbol,),
    )

    if not pending:
        print(f"[valupdate] {symbol}: No pending predictions to update.")
        return

    updated = 0
    for row in pending:
        # Try to parse target_period as a date
        try:
            target_date = str(row["target_period"])[:10]
            actual_row = config.fetchone(
                "SELECT close_price FROM historical_prices WHERE symbol=%s AND trade_date=%s",
                (symbol, target_date),
            )
        except Exception:
            continue

        if not actual_row:
            continue

        actual = float(actual_row["close_price"])
        predicted = float(row["predicted_value"])
        diff = actual - predicted
        pct_error = abs(diff / actual * 100) if actual else None

        config.execute(
            """
            UPDATE predictions
            SET actual_value = %s,
                difference   = %s,
                pct_error    = %s
            WHERE id = %s
            """,
            (actual, round(diff, 4), round(pct_error, 4) if pct_error is not None else None, row["id"]),
        )
        updated += 1

    print(f"[valupdate] {symbol}: Updated {updated}/{len(pending)} predictions with actuals.")


def print_summary(symbol):
    """Print accuracy statistics from predictions table."""
    stats = config.fetchone(
        """
        SELECT
            COUNT(*)                              AS total_rows,
            SUM(actual_value IS NOT NULL)         AS filled,
            AVG(ABS(pct_error))                   AS avg_pct_error,
            SUM(direction = 'BUY'  AND difference > 0) AS correct_buy,
            SUM(direction = 'SELL' AND difference < 0) AS correct_sell
        FROM predictions
        WHERE symbol = %s
          AND model_type = 'LSTM'
          AND actual_value IS NOT NULL
        """,
        (symbol,),
    )
    if stats and stats["filled"]:
        print(f"[valupdate] {symbol} summary: filled={stats['filled']} | "
              f"avg_error={stats['avg_pct_error']:.2f}% | "
              f"correct_buy={stats['correct_buy']} correct_sell={stats['correct_sell']}")


def main():
    print(f"[valupdate] Started at {datetime.now()}")
    for symbol in STOCKS:
        update_actuals(symbol)
        print_summary(symbol)
    print(f"[valupdate] Done at {datetime.now()}. Results in MySQL `predictions`.")


if __name__ == "__main__":
    main()
