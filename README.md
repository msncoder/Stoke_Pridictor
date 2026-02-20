# Stock Market Analyzer & Predictor System (SMAP) - FYP

The project aimed to predict daily closing and hourly stock prices of various stocks listed on the Pakistan Stock Exchange thereby being a source of timely guidance for investors

System Features: Live data processing and technical analysis, User profile and stats and Scalable to other stocks

Technologies/language involved: Python, Hadoop, D3.js, MySQL, Ubuntu, TensorFlow

For scraping: Goose, BeautifulSoup4

For NLP news analysis: nltk(stemming, lemmatization, stopwords removal etc.) and Pysentiment(Python financial news sentiment library)

For prediction: Univariate Long-Short Term Memory (LSTM) for hourly predictions and indicators-based own-built algorithm for daily closing price predictions

Data sources: Quandl, investing.com, nccpl and misc websites

News source: Dawn.com, Ksebusiness.com, Ksenational.com, RSS feeds

Prediction done for HBL, UBL, ENGRO FERTILIZER, PSO and OGDCL with 55 to 60% accuracy.

Step to compile this project:
1. python db/import_historical.py --all
2. python Scrapers/dawn.py
3. python Scrapers/newsfeed.py
4. python Scrapers/hbl.py
5. python Scrapers/ubl.py
6. python Scrapers/engro.py
7. python Scrapers/pso.py
8. python Scrapers/ogdcl.py
9. python Scrapers/oil.py
10. python Scrapers/use_investing.py
11. python Scrapers/gold.py
12. python Scrapers/kebusiness.py
13. python Scrapers/ksenational.py
python "Technical Analysis/daily_indicators.py"
python Prediction/lstm.py
-- View latest predictions
SELECT * FROM predictions ORDER BY predicted_at DESC LIMIT 10;

-- View calculated indicators
SELECT * FROM indicators WHERE symbol='HBL' ORDER BY trade_date DESC LIMIT 10;



