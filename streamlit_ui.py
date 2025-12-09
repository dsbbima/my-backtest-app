import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, timedelta

# Import fungsi backtest dari file app_backtest.py
from app_backtest import run_backtest 

## Konfigurasi Streamlit (Header)
st.set_page_config(layout="wide")
st.title("📈 Aplikasi Backtest Trading Sederhana (Streamlit + Backtrader)")
st.caption("Uji strategi Moving Average Crossover menggunakan data historis.")

# --- Bagian Input Pengguna ---
st.sidebar.header("⚙️ Parameter Backtest")

with st.sidebar.form(key='backtest_form'):
    # Input Data
    ticker = st.text_input("Kode Saham (Ticker)", value='BBCA.JK').upper() # Contoh untuk saham Indonesia
    start_date = st.date_input("Tanggal Mulai", value=date.today() - timedelta(days=365*3))
    end_date = st.date_input("Tanggal Akhir", value=date.today() - timedelta(days=1))
    
    st.markdown("---")
    
    # Input Strategi
    st.subheader("Parameter Strategi (MACross)")
    fast_period = st.slider("Periode MA Cepat", min_value=5, max_value=50, value=10, step=1)
    slow_period = st.slider("Periode MA Lambat", min_value=30, max_value=200, value=30, step=5)
    
    st.markdown("---")

    # Input Keuangan
    initial_cash = st.number_input("Modal Awal (Cash)", min_value=10000, value=100000, step=10000)
    
    run_button = st.form_submit_button("Jalankan Backtest")

# --- Bagian Hasil ---
if run_button:
    # Validasi Input
    if start_date >= end_date:
        st.error("Tanggal Mulai harus sebelum Tanggal Akhir.")
    else:
        st.subheader(f"⏳ Menjalankan Backtest untuk {ticker}...")
        
        # Panggil fungsi backtest
        metrics, cerebro = run_backtest(
            ticker=ticker, 
            start_date=start_date.strftime('%Y-%m-%d'), 
            end_date=end_date.strftime('%Y-%m-%d'), 
            fast_period=fast_period, 
            slow_period=slow_period,
            initial_cash=initial_cash
        )
        
        if "error" in metrics:
             st.error(metrics["error"])
        else:
            st.subheader(f"✅ Hasil Backtest: {ticker}")
            
            # Tampilkan Metrik Kinerja (Menggunakan kolom untuk tampilan bersih)
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("Modal Akhir", f"Rp {metrics['final_cash']:,.0f}", delta=f"{metrics['final_cash'] - metrics['start_cash']:,.0f}")
            col2.metric("Return Total (%)", f"{metrics['total_return_percent']:.2f} %")
            col3.metric("Max Drawdown (%)", f"{metrics['max_drawdown_percent']:.2f} %")
            col4.metric("Sharpe Ratio", f"{metrics['sharpe_ratio']}")

            st.markdown("---")

            # Visualisasi (Menggunakan Plotly untuk visualisasi interaktif)
            # Catatan: Integrasi plot Backtrader ke Streamlit rumit. 
            # Cara tercepat adalah meminta Backtrader menyimpan plot ke file/buffer dan menampilkannya,
            # atau menggunakan library terpisah seperti Plotly untuk merender data.
            st.warning("Visualisasi grafik harga (candlestick) memerlukan integrasi Plotly yang lebih kompleks.")
            st.info("Silakan cek terminal Anda untuk melihat plot standar Backtrader yang mungkin muncul sebagai jendela baru (tergantung konfigurasi Anda).")
            
            # Pilihan: Plotting Equity Curve Sederhana (Nilai Portofolio)
            # Cara ini membutuhkan analyzer khusus di Backtrader, 
            # namun untuk demo ini, kami tampilkan hasil akhir metrik saja.
