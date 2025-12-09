import backtrader as bt
import pandas as pd
import numpy as np

# Definisi Strategi Sederhana: Moving Average Crossover
class MACross(bt.Strategy):
    """
    Strategi Beli/Jual ketika Fast MA memotong Slow MA.
    """
    params = (
        ('fast_period', 10),
        ('slow_period', 30)
    )

    def __init__(self):
        # Indikator yang digunakan
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.data, period=self.p.fast_period)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.data, period=self.p.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        
        self.order = None
        
        # Variabel untuk menyimpan data sinyal dan nilai portofolio untuk plot
        self.buys = []
        self.sells = []
        self.equity_curve = []

    def next(self):
        # Simpan nilai portofolio untuk Kurva Ekuitas
        self.equity_curve.append(self.broker.getvalue())

        if self.order:
            return  # Tunggu order selesai

        # Sinyal Beli (Fast MA > Slow MA)
        if not self.position:
            if self.crossover > 0:
                self.order = self.buy()
                self.buys.append(self.data.datetime.date(0)) # Simpan tanggal beli

        # Sinyal Jual (Fast MA < Slow MA)
        else:
            if self.crossover < 0:
                self.order = self.sell()
                self.sells.append(self.data.datetime.date(0)) # Simpan tanggal jual

    def notify_order(self, order):
        # Pastikan order diselesaikan untuk menghindari duplikasi
        if order.status in [order.Completed]:
            self.order = None

# Fungsi utama untuk menjalankan backtest
def run_backtest(data_df, fast_period, slow_period, initial_cash):
    """
    Menjalankan Backtest dan mengembalikan metrik serta data plot.
    """
    if data_df.empty:
        return {"error": "Data kosong."}, None, None, None

    # Inisialisasi Cerebro (Mesin Backtrader)
    cerebro = bt.Cerebro()
    
    # Feed Data (Backtrader menerima Pandas DataFrame)
    data_feed = bt.feeds.PandasData(dataname=data_df)
    cerebro.adddata(data_feed)
    cerebro.broker.setcash(initial_cash)
    
    # Tambahkan Strategi
    cerebro.addstrategy(MACross, 
                        fast_period=fast_period, 
                        slow_period=slow_period)

    # Tambahkan Analisis Kinerja
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    
    # Jalankan Backtest
    results = cerebro.run()
    
    strat = results[0]
    final_value = cerebro.broker.getvalue()
    
    # Ekstrak Metrik
    returns_analyzer = strat.analyzers.returns.get_analysis()
    drawdown_analyzer = strat.analyzers.drawdown.get_analysis()

    metrics = {
        "start_cash": initial_cash,
        "final_cash": final_value,
        # Menggunakan .get(key, default) untuk menghindari error jika data terlalu pendek
        "total_return_percent": returns_analyzer.get('rtot', 0) * 100,
        "annual_return_percent": returns_analyzer.get('rann', 0) * 100,
        "max_drawdown_percent": drawdown_analyzer['max']['drawdown'] if drawdown_analyzer.get('max') else 0,
        "sharpe_ratio": returns_analyzer.get('sharperatio', 'N/A'),
    }
    
    # Siapkan data untuk Plotting Kurva Ekuitas (hanya sebanyak data yang diproses)
    equity_values = strat.equity_curve
    equity_df = pd.DataFrame({
        'Date': data_df.index[:len(equity_values)], # Sesuaikan panjang data dengan curve
        'Value': equity_values
    })
    
    # Sinyal untuk plot
    buy_dates = strat.buys
    sell_dates = strat.sells

    return metrics, equity_df, buy_dates, sell_dates
