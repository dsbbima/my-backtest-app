import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import date, timedelta

# Import fungsi backtest dari file app_backtest.py
from app_backtest import run_backtest 

## Konfigurasi Streamlit
st.set_page_config(layout="wide")
st.title("📈 Backtest Web App: Moving Average Crossover")
st.caption("Dibangun dengan Streamlit, Backtrader, dan Plotly. Data bersumber dari Yahoo Finance.")

# --- Bagian Input Pengguna (Sidebar) ---
st.sidebar.header("⚙️ Parameter Uji Coba")

with st.sidebar.form(key='backtest_form'):
    # Input Data
    ticker = st.text_input("Kode Saham (Ticker)", value='BBCA.JK').upper() # Contoh Ticker BBCA.JK untuk data bursa Indonesia
    start_date = st.date_input("Tanggal Mulai", value=date.today() - timedelta(days=365*3))
    end_date = st.date_input("Tanggal Akhir", value=date.today() - timedelta(days=1))
    
    st.markdown("---")
    
    # Input Strategi
    st.subheader("Parameter Strategi (MA Crossover)")
    fast_period = st.slider("Periode MA Cepat", min_value=5, max_value=50, value=10, step=1)
    slow_period = st.slider("Periode MA Lambat", min_value=30, max_value=200, value=30, step=5)
    
    st.markdown("---")

    # Input Keuangan
    initial_cash = st.number_input("Modal Awal (Cash)", min_value=10000, value=100000, step=10000)
    
    run_button = st.form_submit_button("Jalankan Backtest")

# --- Bagian Hasil ---
if run_button:
    
    if start_date >= end_date:
        st.error("Tanggal Mulai harus sebelum Tanggal Akhir.")
        st.stop()
        
    st.info(f"⏳ Mengunduh data historis untuk **{ticker}**...")
    
    # 1. Unduh Data
    try:
        # Unduh data dan HANYA gunakan kolom 'Open', 'High', 'Low', 'Close', 'Volume'
        data_df = yf.download(ticker, 
                              start=start_date.strftime('%Y-%m-%d'), 
                              end=end_date.strftime('%Y-%m-%d'), 
                              auto_adjust=False) # Penting: matikan auto_adjust agar Backtrader bisa memprosesnya

        if data_df.empty:
             st.error(f"Tidak ada data ditemukan untuk {ticker}. Cek kode ticker.")
             st.stop()
        
        st.success(f"Data {ticker} berhasil diunduh.")

    except Exception as e:
        st.error(f"Gagal mengunduh data dari yfinance. Pastikan kode ticker benar. Error: {e}")
        st.stop()

    st.subheader(f"🔄 Menjalankan simulasi backtest...")
    
    # 2. Panggil fungsi backtest
    metrics, equity_df, buy_dates, sell_dates = run_backtest(
        data_df=data_df, 
        fast_period=fast_period, 
        slow_period=slow_period,
        initial_cash=initial_cash
    )
    
    # 3. Tampilkan Metrik Kinerja
    st.subheader(f"✅ Laporan Kinerja: {ticker}")
    col1, col2, col3, col4 = st.columns(4)
    
    final_cash = metrics['final_cash']
    start_cash = metrics['start_cash']
    
    col1.metric("Modal Akhir", f"Rp {final_cash:,.0f}", delta=f"Return: {final_cash - start_cash:,.0f}")
    col2.metric("Return Total", f"{metrics['total_return_percent']:.2f} %")
    col3.metric("Max Drawdown", f"{metrics['max_drawdown_percent']:.2f} %")
    col4.metric("Sharpe Ratio", f"{metrics['sharpe_ratio']}")

    st.markdown("---")
    
    # 4. Visualisasi Kurva Ekuitas (Nilai Portofolio)
    st.subheader("Kurva Ekuitas (Equity Curve)")
    
    fig_equity = go.Figure()
    fig_equity.add_trace(go.Scatter(x=equity_df['Date'], y=equity_df['Value'], mode='lines', name='Nilai Portofolio'))
    fig_equity.update_layout(title_text='Perkembangan Nilai Portofolio (Equity Curve)')
    st.plotly_chart(fig_equity, use_container_width=True)

    st.markdown("---")

    # 5. Visualisasi Candlestick dengan Sinyal Jual/Beli
    st.subheader(f"Grafik Candlestick {ticker} dengan Sinyal Trading")
    
    # Hitung Moving Average untuk visualisasi
    data_df['FastMA'] = data_df['Close'].rolling(window=fast_period).mean()
    data_df['SlowMA'] = data_df['Close'].rolling(window=slow_period).mean()
    
    fig_chart = go.Figure()
    
    # Candlestick
    fig_chart.add_trace(go.Candlestick(x=data_df.index,
                                    open=data_df['Open'],
                                    high=data_df['High'],
                                    low=data_df['Low'],
                                    close=data_df['Close'],
                                    name='Harga'))

    # Moving Averages
    fig_chart.add_trace(go.Scatter(x=data_df.index, y=data_df['FastMA'], mode='lines', name=f'MA Cepat ({fast_period})', line=dict(color='orange')))
    fig_chart.add_trace(go.Scatter(x=data_df.index, y=data_df['SlowMA'], mode='lines', name=f'MA Lambat ({slow_period})', line=dict(color='purple')))
    
    # Plot Sinyal Beli (Titik hijau di bawah harga)
    buy_data_points = data_df[data_df.index.isin(buy_dates)]
    fig_chart.add_trace(go.Scatter(x=buy_data_points.index, y=buy_data_points['Low'] * 0.99, 
                                    mode='markers', name='BUY', 
                                    marker=dict(symbol='triangle-up', size=10, color='green')))

    # Plot Sinyal Jual (Titik merah di atas harga)
    sell_data_points = data_df[data_df.index.isin(sell_dates)]
    fig_chart.add_trace(go.Scatter(x=sell_data_points.index, y=sell_data_points['High'] * 1.01, 
                                    mode='markers', name='SELL', 
                                    marker=dict(symbol='triangle-down', size=10, color='red')))


    fig_chart.update_layout(xaxis_rangeslider_visible=False, title_text="Sinyal Trading (Beli/Jual)")
    st.plotly_chart(fig_chart, use_container_width=True)
