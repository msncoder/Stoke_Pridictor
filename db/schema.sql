-- ============================================================
-- SMAP-FYP Database Schema
-- Stock Market Analyzer & Predictor System
-- ============================================================
-- Run this once to initialize the database:
--   mysql -u root -p < db/schema.sql

CREATE DATABASE IF NOT EXISTS smap_fyp
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE smap_fyp;

-- ============================================================
-- 1. STOCK PRICES  (scraped live from investing.com)
-- ============================================================
CREATE TABLE IF NOT EXISTS stock_prices (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    symbol      VARCHAR(20)   NOT NULL COMMENT 'e.g. HBL, OGDCL, UBL',
    price       DECIMAL(12,4) NOT NULL,
    scraped_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_url  VARCHAR(512)  DEFAULT NULL,
    INDEX idx_symbol          (symbol),
    INDEX idx_scraped_at      (scraped_at),
    INDEX idx_symbol_time     (symbol, scraped_at)
) ENGINE=InnoDB COMMENT='Live stock prices scraped from investing.com';

-- ============================================================
-- 2. COMMODITY PRICES  (Gold, Oil, USD Index)
-- ============================================================
CREATE TABLE IF NOT EXISTS commodity_prices (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    commodity   VARCHAR(30)   NOT NULL COMMENT 'e.g. GOLD, OIL, USD_INDEX',
    price       DECIMAL(12,4) NOT NULL,
    scraped_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_commodity       (commodity),
    INDEX idx_scraped_at      (scraped_at)
) ENGINE=InnoDB COMMENT='Commodity and currency prices scraped from investing.com';

-- ============================================================
-- 3. HISTORICAL OHLCV DATA  (imported from original CSVs)
-- ============================================================
CREATE TABLE IF NOT EXISTS historical_prices (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    symbol      VARCHAR(20)   NOT NULL,
    trade_date  DATE          NOT NULL,
    open_price  DECIMAL(12,4) DEFAULT NULL,
    high_price  DECIMAL(12,4) DEFAULT NULL,
    low_price   DECIMAL(12,4) DEFAULT NULL,
    close_price DECIMAL(12,4) NOT NULL,
    volume      BIGINT UNSIGNED DEFAULT NULL,
    UNIQUE KEY  uq_symbol_date (symbol, trade_date),
    INDEX idx_symbol           (symbol),
    INDEX idx_trade_date       (trade_date)
) ENGINE=InnoDB COMMENT='Historical OHLCV data for PSX stocks';

-- ============================================================
-- 4. NEWS ARTICLES  (dawn.py, kseBusiness.py, kseNational.py)
-- ============================================================
CREATE TABLE IF NOT EXISTS articles (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(1000) NOT NULL,
    body        LONGTEXT      DEFAULT NULL,
    source      VARCHAR(100)  DEFAULT NULL COMMENT 'e.g. dawn, kse_business',
    url         VARCHAR(1024) DEFAULT NULL,
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY  uq_title      (title(255)),
    FULLTEXT    ft_title_body (title, body),
    INDEX idx_source          (source),
    INDEX idx_created_at      (created_at)
) ENGINE=InnoDB COMMENT='Scraped news articles from Dawn and KSE news';

-- ============================================================
-- 5. NEWS SENTIMENT  (newsfeed.py)
-- ============================================================
CREATE TABLE IF NOT EXISTS news_sentiment (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    stock       VARCHAR(20)   NOT NULL COMMENT 'e.g. HBL, OGDCL',
    title       VARCHAR(1000) DEFAULT NULL,
    polarity    DECIMAL(8,4)  DEFAULT NULL COMMENT 'pysentiment2 score',
    subjectivity DECIMAL(8,4) DEFAULT NULL,
    trade_signal ENUM('BUY','SELL','NEUTRAL') DEFAULT 'NEUTRAL',
    scored_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_stock           (stock),
    INDEX idx_scored_at       (scored_at)
) ENGINE=InnoDB COMMENT='News sentiment scores per stock';

-- ============================================================
-- 6. TECHNICAL INDICATORS
-- ============================================================
CREATE TABLE IF NOT EXISTS indicators (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    symbol          VARCHAR(20)     NOT NULL,
    trade_date      DATE            NOT NULL,
    indicator_name  VARCHAR(50)     NOT NULL COMMENT 'e.g. RSI, MACD, MA_14',
    value           DECIMAL(16,6)   DEFAULT NULL,
    trade_signal ENUM('BUY','SELL','NEUTRAL') DEFAULT 'NEUTRAL',
    period          SMALLINT UNSIGNED DEFAULT NULL COMMENT 'indicator period',
    calculated_at   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol_date      (symbol, trade_date),
    INDEX idx_indicator        (indicator_name),
    INDEX idx_symbol_indicator (symbol, indicator_name)
) ENGINE=InnoDB COMMENT='Calculated technical indicators for all stocks';

-- ============================================================
-- 7. LSTM PREDICTIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS predictions (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    symbol          VARCHAR(20)     NOT NULL,
    model_type      VARCHAR(50)     NOT NULL DEFAULT 'LSTM',
    predicted_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    target_period   VARCHAR(20)     DEFAULT NULL COMMENT 'e.g. next_1h, next_day',
    predicted_value DECIMAL(12,4)   NOT NULL,
    actual_value    DECIMAL(12,4)   DEFAULT NULL COMMENT 'filled in by valupdate.py',
    difference      DECIMAL(12,4)   DEFAULT NULL COMMENT 'actual - predicted',
    pct_error       DECIMAL(8,4)    DEFAULT NULL COMMENT 'abs(diff)/actual * 100',
    direction       ENUM('BUY','SELL','NEUTRAL') DEFAULT NULL,
    confidence_pct  DECIMAL(5,2)    DEFAULT NULL,
    buy_signals     TINYINT UNSIGNED DEFAULT NULL,
    sell_signals    TINYINT UNSIGNED DEFAULT NULL,
    INDEX idx_symbol          (symbol),
    INDEX idx_predicted_at    (predicted_at),
    INDEX idx_symbol_time     (symbol, predicted_at)
) ENGINE=InnoDB COMMENT='LSTM and custom algorithm predictions';

-- ============================================================
-- 8. DOWNLOADED DOCUMENTS  (downloader.py)
-- ============================================================
CREATE TABLE IF NOT EXISTS documents (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(500)  NOT NULL,
    body        LONGTEXT      DEFAULT NULL,
    source_url  VARCHAR(1024) DEFAULT NULL,
    file_type   VARCHAR(20)   DEFAULT 'pdf',
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY  uq_title      (title(255)),
    FULLTEXT    ft_body       (body),
    INDEX idx_created_at      (created_at)
) ENGINE=InnoDB COMMENT='Downloaded and parsed PDF/article documents';
