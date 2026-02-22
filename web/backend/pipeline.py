import sys
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config

# Import existing modules
try:
    from Scrapers import ogdcl, hbl, pso, engro, ubl
    from Technical_Analysis import indicators_all
    from Prediction import lstm
except ImportError as e:
    logging.error(f"Failed to import modules: {e}")
    # We'll try to fix imports during runtime if needed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_scrapers():
    logging.info("Starting Scrapers...")
    # This project has individual scraper files. We'll attempt to run them.
    # Note: Many scrapers use Selenium which might be slow.
    stocks = [
        ("OGDCL", "Scrapers.OGDCL"),
        ("HBL", "Scrapers.hbl"),
        ("PSO", "Scrapers.pso"),
        ("ENGRO", "Scrapers.engro"),
        ("UBL", "Scrapers.ubl")
    ]
    
    import importlib
    for symbol, module_path in stocks:
        try:
            logging.info(f"Running scraper for {symbol}...")
            module = importlib.import_module(module_path)
            if hasattr(module, 'get_price') and hasattr(module, 'save_price'):
                price = module.get_price()
                if price:
                    module.save_price(price)
                    logging.info(f"Saved price for {symbol}: {price}")
            elif hasattr(module, 'main'):
                # Some might have a main that doesn't loop
                module.main()
        except Exception as e:
            logging.error(f"Error scraping {symbol}: {e}")

def run_indicators():
    logging.info("Calculating Technical Indicators...")
    try:
        from Technical_Analysis import indicators_all
        indicators_all.main()
        logging.info("Indicators updated successfully.")
    except Exception as e:
        logging.error(f"Error calculating indicators: {e}")

def run_predictions():
    logging.info("Running LSTM Predictions...")
    try:
        from Prediction import lstm
        lstm.main()
        logging.info("Predictions updated successfully.")
    except Exception as e:
        logging.error(f"Error running predictions: {e}")

def run_full_pipeline():
    logging.info("--- Starting Full Pipeline ---")
    start_time = datetime.now()
    
    # 1. Scrape latest prices
    # Note: Existing scrapers might need historical data import first
    # For now we'll trigger the per-stock scrapers
    run_scrapers()
    
    # 2. Update technical indicators
    run_indicators()
    
    # 3. Update predictions
    run_predictions()
    
    end_time = datetime.now()
    logging.info(f"--- Pipeline Finished in {end_time - start_time} ---")
    return {"status": "success", "duration": str(end_time - start_time)}

if __name__ == "__main__":
    run_full_pipeline()
