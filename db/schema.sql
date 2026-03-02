-- ============================================================
-- SMAP-FYP Database Schema (PostgreSQL / Neon)
-- Stock Market Analyzer & Predictor System
-- ============================================================

-- 1. STOCK PRICES (scraped live from investing.com)
CREATE TABLE IF NOT EXISTS stock_prices (
    id          BIGSERIAL PRIMARY KEY,
    symbol      VARCHAR(20)   NOT NULL,
    price       DECIMAL(12,4) NOT NULL,
    scraped_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_url  VARCHAR(512)  DEFAULT NULL
);
CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol ON stock_prices(symbol);
CREATE INDEX IF NOT EXISTS idx_stock_prices_scraped_at ON stock_prices(scraped_at);
CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol_time ON stock_prices(symbol, scraped_at);

-- 2. COMMODITY PRICES (Gold, Oil, USD Index)
CREATE TABLE IF NOT EXISTS commodity_prices (
    id          BIGSERIAL PRIMARY KEY,
    commodity   VARCHAR(30)   NOT NULL,
    price       DECIMAL(12,4) NOT NULL,
    scraped_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_commodity_prices_commodity ON commodity_prices(commodity);
CREATE INDEX IF NOT EXISTS idx_commodity_prices_scraped_at ON commodity_prices(scraped_at);

-- 3. HISTORICAL OHLCV DATA (imported from original CSVs)
CREATE TABLE IF NOT EXISTS historical_prices (
    id          BIGSERIAL PRIMARY KEY,
    symbol      VARCHAR(20)   NOT NULL,
    trade_date  DATE          NOT NULL,
    open_price  DECIMAL(12,4) DEFAULT NULL,
    high_price  DECIMAL(12,4) DEFAULT NULL,
    low_price   DECIMAL(12,4) DEFAULT NULL,
    close_price DECIMAL(12,4) NOT NULL,
    volume      BIGINT        DEFAULT NULL,
    UNIQUE (symbol, trade_date)
);
CREATE INDEX IF NOT EXISTS idx_historical_prices_symbol ON historical_prices(symbol);
CREATE INDEX IF NOT EXISTS idx_historical_prices_trade_date ON historical_prices(trade_date);

-- 4. NEWS ARTICLES (dawn.py, kseBusiness.py, kseNational.py)
CREATE TABLE IF NOT EXISTS articles (
    id          BIGSERIAL PRIMARY KEY,
    title       VARCHAR(1000) NOT NULL,
    body        TEXT          DEFAULT NULL,
    source      VARCHAR(100)  DEFAULT NULL,
    url         VARCHAR(1024) DEFAULT NULL,
    created_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (title)
);
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles(created_at);
-- Full-text search index (PostgreSQL)
CREATE INDEX IF NOT EXISTS idx_articles_fts ON articles USING GIN(to_tsvector('english', title || ' ' || coalesce(body, '')));

-- 5. NEWS SENTIMENT (newsfeed.py)
CREATE TABLE IF NOT EXISTS news_sentiment (
    id          BIGSERIAL PRIMARY KEY,
    stock       VARCHAR(20)   NOT NULL,
    title       VARCHAR(1000) DEFAULT NULL,
    polarity    DECIMAL(8,4)  DEFAULT NULL,
    subjectivity DECIMAL(8,4) DEFAULT NULL,
    trade_signal VARCHAR(10)  DEFAULT 'NEUTRAL',
    scored_at   TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_news_sentiment_stock ON news_sentiment(stock);
CREATE INDEX IF NOT EXISTS idx_news_sentiment_scored_at ON news_sentiment(scored_at);

-- 6. TECHNICAL INDICATORS
CREATE TABLE IF NOT EXISTS indicators (
    id              BIGSERIAL PRIMARY KEY,
    symbol          VARCHAR(20)   NOT NULL,
    trade_date      DATE          NOT NULL,
    indicator_name  VARCHAR(50)   NOT NULL,
    value           DECIMAL(16,6) DEFAULT NULL,
    trade_signal    VARCHAR(10)   DEFAULT 'NEUTRAL',
    period          SMALLINT      DEFAULT NULL,
    calculated_at   TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (symbol, trade_date, indicator_name)
);
CREATE INDEX IF NOT EXISTS idx_indicators_symbol_date ON indicators(symbol, trade_date);
CREATE INDEX IF NOT EXISTS idx_indicators_name ON indicators(indicator_name);
CREATE INDEX IF NOT EXISTS idx_indicators_symbol_indicator ON indicators(symbol, indicator_name);

-- 7. LSTM PREDICTIONS
CREATE TABLE IF NOT EXISTS predictions (
    id              BIGSERIAL PRIMARY KEY,
    symbol          VARCHAR(20)   NOT NULL,
    model_type      VARCHAR(50)   NOT NULL DEFAULT 'LSTM',
    predicted_at    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    target_period   VARCHAR(20)   DEFAULT NULL,
    predicted_value DECIMAL(12,4) NOT NULL,
    actual_value    DECIMAL(12,4) DEFAULT NULL,
    difference      DECIMAL(12,4) DEFAULT NULL,
    pct_error       DECIMAL(8,4)  DEFAULT NULL,
    direction       VARCHAR(10)   DEFAULT NULL,
    confidence_pct  DECIMAL(5,2)  DEFAULT NULL,
    buy_signals     SMALLINT      DEFAULT NULL,
    sell_signals    SMALLINT      DEFAULT NULL,
    UNIQUE (symbol, predicted_at, model_type)
);

CREATE INDEX IF NOT EXISTS idx_predictions_symbol ON predictions(symbol);
CREATE INDEX IF NOT EXISTS idx_predictions_predicted_at ON predictions(predicted_at);
CREATE INDEX IF NOT EXISTS idx_predictions_symbol_time ON predictions(symbol, predicted_at);

-- 8. DOWNLOADED DOCUMENTS (downloader.py)
CREATE TABLE IF NOT EXISTS documents (
    id          BIGSERIAL PRIMARY KEY,
    title       VARCHAR(500)  NOT NULL,
    body        TEXT          DEFAULT NULL,
    source_url  VARCHAR(1024) DEFAULT NULL,
    file_type   VARCHAR(20)   DEFAULT 'pdf',
    created_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (title)
);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
-- Full-text search index (PostgreSQL)
CREATE INDEX IF NOT EXISTS idx_documents_fts ON documents USING GIN(to_tsvector('english', coalesce(body, '')));
