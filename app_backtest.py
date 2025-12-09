import backtrader as bt
import yfinance as yf
import pandas as pd

# Definisi Strategi Sederhana: Moving Average Crossover
class MACross(bt.Strategy):
    params = (
        ('fast_period', 10),
        ('slow_period', 30)
    )

    def __init__(self):
        # Indikator yang akan digunakan
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.data, period=self.p.fast_period)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.data, period=self.p.slow_period)
        
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        
        self.order = None

    def next(self):
        if self.order:
            return  # Tunggu order selesai

        # Jika belum punya posisi
        if not self.position:
            # Garis Cepat memotong Garis Lambat dari bawah ke atas (BUY)
            if self.crossover > 0:
                self.order = self.buy()
        
        # Jika sudah punya posisi
        else:
            # Garis Cepat memotong Garis Lambat dari atas ke bawah (SELL/EXIT)
            if self.crossover < 0:
                self.order = self.sell()

# Fungsi utama untuk menjalankan backtest
def run_backtest(ticker, start_date, end_date, fast_period, slow_period, initial_cash):
    # 1. Unduh Data
    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        # Konversi ke format yang disukai Backtrader
        data_feed = bt.feeds.PandasData(dataname=data)
    except Exception as e:
        return {"error": f"Gagal mengunduh data: {e}"}

    # 2. Inisialisasi Cerebro (Mesin Utama Backtrader)
    cerebro = bt.Cerebro()
    cerebro.adddata(data_feed)
    cerebro.broker.setcash(initial_cash)
    
    # Tambahkan Strategi dengan Parameter yang Diberikan Pengguna
    cerebro.addstrategy(MACross, 
                        fast_period=fast_period, 
                        slow_period=slow_period)

    # Tambahkan Analisis Kinerja
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    
    # Initial Value
    start_value = cerebro.broker.getvalue()

    # 3. Jalankan Backtest
    print(f"Starting Portfolio Value: {start_value:.2f}")
    results = cerebro.run()
    
    # Final Value
    final_value = cerebro.broker.getvalue()
    
    # 4. Ambil dan Format Hasil
    strat = results[0]
    
    # Ekstrak Data untuk Grafik
    date_list = [bt.num2date(d).date() for d in cerebro.datas[0].datetime.array]
    value_list = []
    
    # Dapatkan nilai portofolio dari salah satu analyzer (misalnya, Equity Curve)
    # Ini memerlukan analyzer khusus yang lebih kompleks atau modifikasi, 
    # untuk kesederhanaan, kita gunakan nilai akhir saja
    
    # Ekstrak Metrik
    returns_analyzer = strat.analyzers.returns.get_analysis()
    drawdown_analyzer = strat.analyzers.drawdown.get_analysis()

    metrics = {
        "ticker": ticker,
        "start_cash": initial_cash,
        "final_cash": final_value,
        "total_return_percent": returns_analyzer['rtot'] * 100,
        "annual_return_percent": returns_analyzer['rann'] * 100,
        "max_drawdown_percent": drawdown_analyzer['max']['drawdown'],
        "sharpe_ratio": returns_analyzer.get('sharperatio', 'N/A'), # Sharpe Ratio kadang tidak terhitung jika data terlalu pendek
    }
    
    # 5. Output Grafik (simpan sementara atau gunakan Plotly)
    # Untuk Streamlit, kita akan menggunakan metode plot bawaan Cerebro yang disimpan ke file/buffer.
    # Namun, cara yang lebih mudah adalah dengan menggunakan plot equity curve secara manual. 
    # Karena Backtrader sulit diintegrasikan dengan Streamlit secara mulus untuk plot, 
    # kita akan plot data secara manual di file streamlit_ui.py
    
    return metrics, cerebro # Mengembalikan cerebro untuk visualisasi di Streamlit
