import sqlite3
import json
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime

# Настройка конфигурации Streamlit
st.set_page_config(
    page_title="Архитектура Предсказателя Будущего",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = "predictive_analytics.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ==========================================
# ИНТЕРФЕЙС (STREAMLIT)
# ==========================================

st.title("🔮 Предиктивная аналитическая система")
st.caption("Прототип ядра сквозного прогнозирования на основе детерминированных взвешенных моделей")

# Боковая панель управления
st.sidebar.header("🎛️ Симуляция входящих потоков")
st.sidebar.markdown("Измените параметры ниже для ручной генерации новых пакетов данных в реальном времени.")

with st.sidebar.form(key='data_stream_form'):
    st.markdown("### 📊 Источник 1: Polymarket")
    poly_price = st.slider("Цена акции YES ($)", 0.01, 1.00, 0.56, step=0.01)
    
    st.markdown("### 📰 Источник 2: SEC Regulatory Sentiment")
    sec_score = st.slider("Оценка тональности документов (0-100)", 0, 100, 65)
    
    st.markdown("### 📈 Источник 3: Binance REST API")
    binance_multiplier = st.slider("Множитель объема торгов к 30d среднему", 0.1, 3.0, 1.45, step=0.05)
    
    submit_button = st.form_submit_button(label='🚀 Сгенерировать и записать такт расчета')

# Логика обработки формы и записи данных
if submit_button:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    event_code = "CRYPTO-SOL-ETF-2026"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Запись raw data
    raw_poly = json.dumps({"yes_token_price": poly_price})
    raw_sec = json.dumps({"sentiment_index": sec_score / 100.0})
    raw_binance = json.dumps({"pair": "SOLUSDT", "24h_volume_multiplier": binance_multiplier})
    
    cursor.execute("INSERT INTO raw_data_records (source_id, event_code, raw_payload, fetched_at) VALUES (1, ?, ?, ?)", (event_code, raw_poly, current_time))
    cursor.execute("INSERT INTO raw_data_records (source_id, event_code, raw_payload, fetched_at) VALUES (2, ?, ?, ?)", (event_code, raw_sec, current_time))
    cursor.execute("INSERT INTO raw_data_records (source_id, event_code, raw_payload, fetched_at) VALUES (3, ?, ?, ?)", (event_code, raw_binance, current_time))
    
    # 2. Пересчет  слоя метрик
    poly_norm = poly_price * 100.0
    binance_norm = min(binance_multiplier * 65.0, 100.0)
    
    cursor.execute("DELETE FROM normalized_indicators WHERE event_code = ?", (event_code,))
    cursor.executemany("INSERT INTO normalized_indicators (event_code, metric_name, normalized_value, metric_weight) VALUES (?, ?, ?, ?)", [
        (event_code, 'polymarket_probability', poly_norm, 0.35),
        (event_code, 'sec_sentiment_score', float(sec_score), 0.45),
        (event_code, 'binance_volume_momentum', binance_norm, 0.20)
    ])
    
    # 3. Фиксация  scor для формирования аудита изменений
    cursor.execute("SELECT confidence_score, final_verdict FROM predictions WHERE event_code = ? ORDER BY prediction_id DESC LIMIT 1", (event_code,))
    last_pred = cursor.fetchone()
    previous_score = last_pred['confidence_score'] if last_pred else 60.95
    old_verdict = last_pred['final_verdict'] if last_pred else "Unknown"
    
    # 4. Вычисление финальной модели
    new_confidence_score = round((poly_norm * 0.35) + (sec_score * 0.45) + (binance_norm * 0.20), 2)
    risk_factor = round(100.0 - new_confidence_score, 2)
    new_verdict = "Highly Probable" if new_confidence_score > 70 else ("Moderately Probable" if new_confidence_score > 50 else "Unlikely")
    
    # Запись в аудит при обнаружении сдвигов тренда
    if abs(new_confidence_score - previous_score) > 0.01:
        reason = f"Dashboard Manual Trigger. Binance Momentum Shift to {round(binance_norm, 1)}/100."
        cursor.execute("INSERT INTO prediction_audit_history (event_code, previous_score, new_score, change_reason, updated_at) VALUES (?, ?, ?, ?, ?)",
                       (event_code, previous_score, new_confidence_score, reason, current_time))
    
    # 5. Публикация  прогноза
    err_condition = "Notice of Disapproval by SEC or calendar expiration past 2026-12-31."
    cursor.execute("""
        INSERT INTO predictions (event_code, target_object, final_verdict, confidence_score, risk_factor, error_trigger_condition, generated_at)
        VALUES (?, 'Solana Spot ETF Approval (USA)', ?, ?, ?, ?, ?)
    """, (event_code, new_verdict, new_confidence_score, risk_factor, err_condition, current_time))
    
    conn.commit()
    conn.close()
    st.sidebar.success("Пакет данных обработан! Метрики пересчитаны.")

# ==========================================
# ОТРЕСОВКА ДАННЫХ ИЗ BD
# ==========================================
conn = get_db_connection()

# Загрузка последней карточки прогноза
latest_pred = conn.execute("SELECT * FROM predictions ORDER BY prediction_id DESC LIMIT 1").fetchone()

if latest_pred:
    # Отрисовка метрик верхнего уровня (Карточка прогноза)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎯 Целевой объект", "Solana Spot ETF")
    with col2:
        st.metric("📊 Текущий вердикт", latest_pred['final_verdict'])
    with col3:
        st.metric("🔥 Уверенность модели", f"{latest_pred['confidence_score']}%")
    with col4:
        st.metric("⚠️ Фактор риска", f"{latest_pred['risk_factor']}%")
        
    st.info(f"🛑 **Критерий системной ошибки (Error Threshold):** {latest_pred['error_trigger_condition']}")

    # Визуализация накопленной истории изменений (График тренда)
    st.subheader("📈 Ретроспективный анализ изменения тренда уверенности")
    
    history_df = pd.read_sql_query(
        "SELECT prediction_id, confidence_score, generated_at FROM predictions ORDER BY prediction_id ASC", conn
    )
    
    if len(history_df) >= 2:
        fig, ax = plt.subplots(figsize=(12, 4.5))
        ax.plot(history_df['generated_at'], history_df['confidence_score'], marker='o', color='#007bff', linewidth=2.5, label="Уверенность системы (%)")
        ax.axhline(y=70, color='#28a745', linestyle='--', alpha=0.7, label="Порог Высокой Вероятности (70%)")
        ax.axhline(y=50, color='#dc3545', linestyle='--', alpha=0.7, label="Порог Низкой Вероятности (50%)")
        
        ax.set_ylabel("Процент уверенности", fontsize=10)
        ax.set_xlabel("Метка времени расчета (UTC)", fontsize=10)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.set_ylim(20, 105)
        ax.legend(loc="lower left")
        plt.xticks(rotation=15, ha='right')
        st.pyplot(fig)
    else:
        st.warning("Недостаточно исторических тактов в БД для построения линии тренда. Сделайте несколько симуляций через боковую панель.")

    # Вывод сырых таблиц базы данных для проверки сходимости
    st.subheader("🗄️ Просмотр таблиц базы данных (Сходимость расчетов)")
    
    tab1, tab2, tab3 = st.tabs(["📌 Карточки прогнозов (Predictions)", "🔄 Лог изменений (Audit History)", "📊 Входные индикаторы"])
    
    with tab1:
        preds_df = pd.read_sql_query("SELECT prediction_id, event_code, final_verdict, confidence_score, risk_factor, generated_at FROM predictions ORDER BY prediction_id DESC", conn)
        st.dataframe(preds_df, use_container_width=True)
        
    with tab2:
        audit_df = pd.read_sql_query("SELECT * FROM prediction_audit_history ORDER BY audit_id DESC", conn)
        st.dataframe(audit_df, use_container_width=True)
        
    with tab3:
        indicators_df = pd.read_sql_query("SELECT * FROM normalized_indicators", conn)
        st.dataframe(indicators_df, use_container_width=True)
else:
    st.error("База данных пуста. Отправьте первую форму в боковой панели, чтобы инициализировать математический расчет.")

conn.close()
