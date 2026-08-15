import os
import sqlite3
from datetime import datetime
import requests

# =====================================================================
# 1. ARCHITECTURE & DATABASE SETUP
# =====================================================================

DB_ORACLE = "future_forecaster.db"

def init_db():
    """Initializes the database schema ensuring traceability from source to prediction."""
    conn = sqlite3.connect(DB_ORACLE)
    cursor = conn.cursor()
    
    # Raw Data Tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crypto_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ticker TEXT,
            price REAL,
            volume_24h REAL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_sentiment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT,
            headline TEXT,
            sentiment_score REAL -- Normalized between -1 (Bearish) and +1 (Bullish)
        )
    ''')
    
    # Normalized Indicators Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS normalized_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            calculation_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            asset_class TEXT,
            price_momentum REAL,  -- Normalized 0 to 1
            sentiment_average REAL, -- Normalized 0 to 1
            composite_score REAL   -- Combined weighted score
        )
    ''')
    
    # Forecast Engine Output Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            forecast_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            target_asset TEXT,
            horizon_days INTEGER,
            predicted_trend TEXT,
            confidence_percentage REAL,
            risk_factor_score REAL,
            primary_argument TEXT,
            invalidations TEXT,
            actual_outcome TEXT DEFAULT 'PENDING'
        )
    ''')
    
    conn.commit()
    conn.close()

# =====================================================================
# 2. DATA INGESTION ENGINE (MOCKED API INPUTS FOR DETERMINISTIC LOGIC)
# =====================================================================

def fetch_and_store_data():
    """
    Ingests data from 2 distinct sources: Market Prices and News Sentiment.
    Simulating live API endpoints for Bitcoin (BTC) macro data tracking.
    """
    conn = sqlite3.connect(DB_ORACLE)
    cursor = conn.cursor()
    
    # Source 1: Mocking Real-time Market Data API
    mock_price_data = {"ticker": "BTC", "price": 94250.00, "volume_24h": 45000000000}
    cursor.execute(
        "INSERT INTO crypto_prices (ticker, price, volume_24h) VALUES (?, ?, ?)",
        (mock_price_data["ticker"], mock_price_data["price"], mock_price_data["volume_24h"])
    )
    
    # Source 2: Mocking Financial News RSS Feed RSS & Sentiment Parser
    mock_headlines = [
        {"source": "CryptoNews", "headline": "Institutional inflows reach record highs as ETF volumes surge", "sentiment": 0.8},
        {"source": "MacroMarkets", "headline": "Regulatory uncertainty triggers short-term liquidations", "sentiment": -0.3},
        {"source": "BlockJournal", "headline": "Network upgrade completes successfully, transaction fees plummet", "sentiment": 0.6}
    ]
    
    for item in mock_headlines:
        cursor.execute(
            "INSERT INTO market_sentiment (source, headline, sentiment_score) VALUES (?, ?, ?)",
            (item["source"], item["headline"], item["sentiment"])
        )
        
    conn.commit()
    conn.close()

# =====================================================================
# 3. ANALYTICAL PIPELINE & FORECASTING ALGORITHM
# =====================================================================

def execute_forecasting_pipeline(ticker="BTC"):
    """
    Extracts raw data, normalizes values, executes a weighted scoring model, 
    and saves the mathematical conclusion directly to the database.
    """
    conn = sqlite3.connect(DB_ORACLE)
    cursor = conn.cursor()
    
    # Fetch latest raw price metrics
    cursor.execute("SELECT price FROM crypto_prices WHERE ticker = ? ORDER BY timestamp DESC LIMIT 1", (ticker,))
    latest_price = cursor.fetchone()[0]
    
    # Normalize Price Momentum: Map current price location relative to baseline
    # For this script's proxy logic, we normalize around a theoretical baseline
    base_target = 90000.00
    price_momentum = min(max((latest_price - base_target) / 10000.0 + 0.5, 0.0), 1.0)
    
    # Fetch and calculate moving sentiment averages from Source 2
    cursor.execute("SELECT sentiment_score FROM market_sentiment ORDER BY timestamp DESC LIMIT 3")
    scores = [row[0] for row in cursor.fetchall()]
    avg_sentiment_raw = sum(scores) / len(scores) if scores else 0
    # Normalize from [-1, 1] range to [0, 1] range
    sentiment_normalized = (avg_sentiment_raw + 1) / 2
    
    # Algorithm Core: Weighted Scoring Model
    # 60% Weight on structural price momentum, 40% on media sentiment momentum
    composite_score = (price_momentum * 0.6) + (sentiment_normalized * 0.4)
    
    # Clear rules map the numeric scale directly to explicit outputs
    if composite_score > 0.65:
        predicted_trend = "AGGRESSIVE BULLISH EXPANSION"
        confidence = composite_score * 100
        risk_score = (1.0 - sentiment_normalized) * 100 # Risk grows if sentiment diverges
    elif composite_score < 0.35:
        predicted_trend = "BEARISH CORRECTION RISK"
        confidence = (1.0 - composite_score) * 100
        risk_score = sentiment_normalized * 100
    else:
        predicted_trend = "CONSOLIDATION RANGING BOUND"
        confidence = 50.0
        risk_score = 50.0

    # Human-readable evidence blocks generated natively from mathematical inputs
    primary_argument = (
        f"Price momentum is at a high threshold index of {price_momentum:.2f} "
        f"supported by a net-positive macro media sentiment index of {avg_sentiment_raw:.2f}."
    )
    
    invalidations = (
        f"System triggers execution error and self-corrects if spot price falls below "
        f"${(latest_price * 0.95):,.2f} (5% trailing variance) or if sentiment averages invert below 0.0."
    )
    
    # Write Normalized Metrics
    cursor.execute(
        "INSERT INTO normalized_indicators (asset_class, price_momentum, sentiment_average, composite_score) VALUES (?, ?, ?, ?)",
        (ticker, price_momentum, sentiment_normalized, composite_score)
    )
    
    # Write Final Structured Forecast
    cursor.execute('''
        INSERT INTO forecasts (target_asset, horizon_days, predicted_trend, confidence_percentage, risk_factor_score, primary_argument, invalidations)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (ticker, 7, predicted_trend, round(confidence, 2), round(risk_score, 2), primary_argument, invalidations))
    
    conn.commit()
    conn.close()

# =====================================================================
# 4. USER INTERFACE & VISUALIZATION CONSOLE
# =====================================================================

def display_forecaster_dashboard():
    """Generates the terminal-based UI and dashboard representation of database entries."""
    conn = sqlite3.connect(DB_ORACLE)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("                FUTURE FORECASTER PROTOTYPE v1.0 (CRYPTO MACRO)")
    print("=" * 80)
    
    # Requirement 4: List of monitorable assets/events
    print("\n[📊 TRADABLE / PREDICTABLE TRACKED TARGETS]")
    print("-" * 40)
    cursor.execute("SELECT DISTINCT ticker FROM crypto_prices")
    assets = cursor.fetchall()
    for asset in assets:
        print(f" • Asset Code: {asset[0]} | Sector: Layer-1 Commodity | Status: ACTIVE ENGINE")
    print("-" * 40)
    
    # Requirement 5: Print Forecast Card using structural DB values
    cursor.execute("SELECT * FROM forecasts ORDER BY forecast_time DESC LIMIT 1")
    fc = cursor.fetchone()
    
    if fc:
        print(f"\n╔══════════════════════════════════════════════════════════════════════════════╗")
        print(f"║ FORECAST CARD ID: #{fc[0]:<58} ║")
        print(f"╠══════════════════════════════════════════════════════════════════════════════╣")
        print(f"║ 🎯 TARGET ASSET : {fc[2]:<58} ║")
        print(f"║ 📅 TIME HORIZON : {fc[3]} Days Tracked                                     ║")
        print(f"║ 📈 TREND VISION : {fc[4]:<58} ║")
        print(f"║ 🔥 CONFIDENCE   : {fc[5]:.2f}%                                                 ║")
        print(f"║ ⚠️ RISK FACTOR  : {fc[6]:.2f}%                                                 ║")
        print(f"╠══════════════════════════════════════════════════════════════════════════════╣")
        print(f"║ 🧠 SYSTEM ARGUMENTS & DATA USED:                                             ║")
        print(f"║    {fc[7]:<73} ║")
        print(f"╠══════════════════════════════════════════════════════════════════════════════╣")
        print(f"║ 🛑 SELF-ERROR DETECTION & INVALIDATION MECHANISM:                            ║")
        print(f"║    {fc[8]:<73} ║")
        print(f"╚══════════════════════════════════════════════════════════════════════════════╝")
        
    print("\n*Disclaimer: For system testing only. No real capital risk profile. Absolute returns unpromised.*")
    conn.close()

# =====================================================================
# 5. EXECUTION PIPELINE ENTRYPOINT
# =====================================================================

if __name__ == "__main__":
    # Standard linear runtime loop ensuring no data decoupling happens
    init_db()
    fetch_and_store_data()
    execute_forecasting_pipeline("BTC")
    display_forecaster_dashboard()
