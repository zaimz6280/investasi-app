"""
Aplikasi Analisis & Rekomendasi Investasi
------------------------------------------
Menampilkan data harga terkini, metrik risiko, dan skor rekomendasi
untuk saham, kripto, atau aset campuran menggunakan data dari Yahoo Finance.

PENTING: Aplikasi ini adalah ALAT BANTU ANALISIS, bukan nasihat keuangan.
Semua keputusan investasi tetap menjadi tanggung jawab pengguna.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# =========================================================
# KONFIGURASI HALAMAN
# =========================================================
st.set_page_config(
    page_title="Analisis & Rekomendasi Investasi",
    page_icon="📈",
    layout="wide",
)

# =========================================================
# BANNER / HERO SECTION (visual, tanpa gambar eksternal)
# =========================================================
st.markdown(
    """
    <div style="
        background: linear-gradient(120deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        padding: 28px 32px;
        border-radius: 16px;
        margin-bottom: 18px;
    ">
        <h1 style="color:white; margin:0; font-size: 32px;">📈 Analisis & Rekomendasi Investasi</h1>
        <p style="color:#cfe8ff; margin:6px 0 0 0; font-size: 15px;">
            🌍 Saham &nbsp;•&nbsp; 🪙 Kripto &nbsp;•&nbsp; 📦 ETF/Reksadana &nbsp;—&nbsp;
            data real-time dari Yahoo Finance
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption("⚠️ Alat bantu analisis, bukan nasihat keuangan. *Asset of the Day* di bawah untuk contoh cepat.")

# =========================================================
# DAFTAR ASET CONTOH (bisa ditambah/diubah pengguna)
# =========================================================
PRESET_ASSETS = {
    "Saham Indonesia (IDX)": [
        "BBCA.JK", "BBRI.JK", "BMRI.JK", "TLKM.JK", "ASII.JK",
        "UNVR.JK", "ICBP.JK", "ANTM.JK", "GOTO.JK", "ADRO.JK",
    ],
    "Saham AS (US)": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
        "TSLA", "META", "JPM", "V", "JNJ",
    ],
    "Kripto": [
        "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD",
        "ADA-USD", "DOGE-USD", "AVAX-USD",
    ],
    "Reksadana/ETF Populer": [
        "SPY", "QQQ", "VOO", "GLD", "AGG", "VWO",
    ],
}

CATEGORY_ICON = {
    "Saham Indonesia (IDX)": "🏦",
    "Saham AS (US)": "🗽",
    "Kripto": "🪙",
    "Reksadana/ETF Populer": "📦",
}

# =========================================================
# ASSET OF THE DAY — dipilih otomatis tiap hari (bukan acak tiap refresh)
# =========================================================
import hashlib

@st.cache_data(ttl=3600, show_spinner=False)
def pilih_asset_of_the_day():
    """Pilih 1 aset secara konsisten untuk hari ini (berubah tiap hari, bukan tiap refresh)."""
    semua = [(t, kat) for kat, tickers in PRESET_ASSETS.items() for t in tickers]
    seed = int(hashlib.md5(datetime.now().strftime("%Y-%m-%d").encode()).hexdigest(), 16)
    ticker, kategori_asset = semua[seed % len(semua)]
    return ticker, kategori_asset

aotd_ticker, aotd_kategori = pilih_asset_of_the_day()

st.markdown("#### ✨ Asset of the Day")
try:
    aotd_data = yf.download(aotd_ticker, period="1mo", progress=False, auto_adjust=True)
    aotd_close = aotd_data["Close"].dropna()
    if isinstance(aotd_close, pd.DataFrame):
        aotd_close = aotd_close.iloc[:, 0]

    harga_now = float(aotd_close.iloc[-1])
    harga_prev = float(aotd_close.iloc[-2]) if len(aotd_close) > 1 else harga_now
    perubahan = (harga_now / harga_prev - 1) * 100 if harga_prev else 0

    col_icon, col_info, col_chart = st.columns([1, 2, 3])
    with col_icon:
        st.markdown(
            f"""
            <div style="
                background: {'#1f7a4d' if perubahan >= 0 else '#a13030'};
                border-radius: 14px;
                width: 90px; height: 90px;
                display: flex; align-items: center; justify-content: center;
                font-size: 42px;
            ">{CATEGORY_ICON.get(aotd_kategori, '💹')}</div>
            """,
            unsafe_allow_html=True,
        )
    with col_info:
        st.metric(
            label=f"{aotd_ticker} • {aotd_kategori}",
            value=f"{harga_now:,.2f}",
            delta=f"{perubahan:+.2f}% (1 hari)",
        )
    with col_chart:
        mini_fig = go.Figure(go.Scatter(
            x=aotd_close.index, y=aotd_close.values,
            mode="lines", line=dict(color="#2ecc71" if perubahan >= 0 else "#e74c3c", width=2),
            fill="tozeroy", fillcolor="rgba(46,204,113,0.1)" if perubahan >= 0 else "rgba(231,76,60,0.1)",
        ))
        mini_fig.update_layout(
            height=110, margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(mini_fig, use_container_width=True, config={"displayModeBar": False})
except Exception:
    st.caption(f"✨ Asset of the Day: **{aotd_ticker}** ({aotd_kategori}) — data belum bisa dimuat.")

st.divider()

# =========================================================
# SIDEBAR - INPUT PENGGUNA
# =========================================================
with st.sidebar:
    st.header("⚙️ Pengaturan Analisis")

    kategori = st.multiselect(
        "Pilih kategori aset",
        options=list(PRESET_ASSETS.keys()),
        default=["Saham Indonesia (IDX)", "Kripto"],
    )

    default_tickers = []
    for k in kategori:
        default_tickers.extend(PRESET_ASSETS[k])

    tickers_input = st.text_area(
        "Kode aset (ticker), pisahkan dengan koma",
        value=", ".join(default_tickers),
        height=120,
        help="Contoh: BBCA.JK, BTC-USD, AAPL. Gunakan format Yahoo Finance.",
    )

    periode = st.selectbox(
        "Rentang data historis",
        options=["3mo", "6mo", "1y", "2y", "5y"],
        index=2,
    )

    risk_free_rate = st.slider(
        "Suku bunga bebas risiko tahunan (%) — untuk Sharpe Ratio",
        min_value=0.0, max_value=15.0, value=6.0, step=0.5,
        help="Contoh: gunakan perkiraan BI Rate atau suku bunga deposito.",
    ) / 100

    run_button = st.button("🔍 Jalankan Analisis", type="primary", use_container_width=True)

# =========================================================
# FUNGSI-FUNGSI ANALISIS
# =========================================================

@st.cache_data(ttl=900, show_spinner=False)
def ambil_data(ticker: str, periode: str) -> pd.DataFrame:
    """Ambil data historis harga penutupan dari Yahoo Finance."""
    data = yf.download(ticker, period=periode, progress=False, auto_adjust=True)
    return data


def hitung_metrik(data: pd.DataFrame, risk_free_rate: float) -> dict:
    """Hitung metrik return dan risiko dari data harga historis."""
    if data.empty or len(data) < 10:
        return None

    close = data["Close"].dropna()
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    returns = close.pct_change().dropna()

    if len(returns) < 5:
        return None

    # Return
    harga_terkini = float(close.iloc[-1])
    harga_awal = float(close.iloc[0])
    total_return = (harga_terkini / harga_awal) - 1
    n_hari = len(close)
    return_tahunan = (1 + total_return) ** (252 / n_hari) - 1 if n_hari > 0 else 0

    # Risiko (volatilitas tahunan)
    volatilitas_harian = returns.std()
    volatilitas_tahunan = volatilitas_harian * np.sqrt(252)

    # Sharpe Ratio (risk-adjusted return)
    sharpe = (return_tahunan - risk_free_rate) / volatilitas_tahunan if volatilitas_tahunan > 0 else 0

    # Max Drawdown
    kumulatif = (1 + returns).cumprod()
    puncak = kumulatif.cummax()
    drawdown = (kumulatif - puncak) / puncak
    max_drawdown = drawdown.min()

    # Value at Risk (VaR) 95% - pendekatan historis
    # Estimasi kerugian maksimum dalam 1 hari dengan keyakinan 95%
    var_95 = np.percentile(returns, 5)

    # Probabilitas hari negatif (historis)
    prob_rugi_harian = (returns < 0).mean()

    # Kategori risiko berdasarkan volatilitas tahunan
    if volatilitas_tahunan < 0.20:
        kategori_risiko = "Rendah"
    elif volatilitas_tahunan < 0.45:
        kategori_risiko = "Sedang"
    else:
        kategori_risiko = "Tinggi"

    # Skor rekomendasi sederhana (gabungan Sharpe & momentum, dinormalisasi kasar)
    momentum_20h = close.pct_change(min(20, n_hari - 1)).iloc[-1] if n_hari > 20 else total_return
    skor_mentah = (sharpe * 0.6) + (momentum_20h * 0.4)

    return {
        "harga_terkini": harga_terkini,
        "return_tahunan": return_tahunan,
        "volatilitas_tahunan": volatilitas_tahunan,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "var_95": var_95,
        "prob_rugi_harian": prob_rugi_harian,
        "kategori_risiko": kategori_risiko,
        "skor_mentah": skor_mentah,
        "close_series": close,
    }


def label_rekomendasi(skor: float) -> str:
    if skor > 0.8:
        return "🟢 Sangat Menarik"
    elif skor > 0.3:
        return "🟢 Menarik"
    elif skor > -0.2:
        return "🟡 Netral"
    elif skor > -0.6:
        return "🟠 Waspada"
    else:
        return "🔴 Berisiko Tinggi"


# =========================================================
# JALANKAN ANALISIS
# =========================================================
if run_button:
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

    if not tickers:
        st.error("Masukkan minimal satu kode aset (ticker).")
        st.stop()

    hasil = []
    progress = st.progress(0, text="Mengambil data...")
    gagal = []

    for i, ticker in enumerate(tickers):
        try:
            data = ambil_data(ticker, periode)
            metrik = hitung_metrik(data, risk_free_rate)
            if metrik:
                metrik["ticker"] = ticker
                hasil.append(metrik)
            else:
                gagal.append(ticker)
        except Exception:
            gagal.append(ticker)
        progress.progress((i + 1) / len(tickers), text=f"Memproses {ticker}...")

    progress.empty()

    if gagal:
        st.info(f"Tidak dapat mengambil data untuk: {', '.join(gagal)}")

    if not hasil:
        st.error("Tidak ada data yang berhasil diambil. Periksa kembali kode aset.")
        st.stop()

    # Normalisasi skor ke rentang -1 s.d 1 (relatif antar aset yang dipilih)
    skor_list = [h["skor_mentah"] for h in hasil]
    skor_max = max(abs(min(skor_list)), abs(max(skor_list)), 1e-9)
    for h in hasil:
        h["skor_normal"] = h["skor_mentah"] / skor_max

    # Urutkan berdasarkan skor tertinggi
    hasil_sorted = sorted(hasil, key=lambda x: x["skor_normal"], reverse=True)

    # ---------------- TABEL RINGKASAN ----------------
    st.subheader("📊 Ringkasan & Rekomendasi")

    tabel_data = []
    for h in hasil_sorted:
        tabel_data.append({
            "Aset": h["ticker"],
            "Harga Terkini": f"{h['harga_terkini']:,.2f}",
            "Return Tahunan": f"{h['return_tahunan']*100:.1f}%",
            "Volatilitas Tahunan": f"{h['volatilitas_tahunan']*100:.1f}%",
            "Sharpe Ratio": f"{h['sharpe']:.2f}",
            "Max Drawdown": f"{h['max_drawdown']*100:.1f}%",
            "VaR 95% (harian)": f"{h['var_95']*100:.1f}%",
            "Prob. Hari Rugi": f"{h['prob_rugi_harian']*100:.0f}%",
            "Kategori Risiko": h["kategori_risiko"],
            "Sinyal": label_rekomendasi(h["skor_normal"]),
        })

    df_tabel = pd.DataFrame(tabel_data)
    st.dataframe(df_tabel, use_container_width=True, hide_index=True)

    st.caption(
        "**Cara baca**: Sharpe Ratio tinggi = return lebih baik dibanding risikonya. "
        "VaR 95% harian = perkiraan kerugian maksimum dalam 1 hari dengan keyakinan 95% "
        "(berdasarkan data historis). Prob. Hari Rugi = persentase hari dengan return negatif "
        "sepanjang periode data."
    )

    # ---------------- GRAFIK RISK vs RETURN ----------------
    st.subheader("🎯 Peta Risiko vs Return")

    df_scatter = pd.DataFrame([{
        "Aset": h["ticker"],
        "Volatilitas (%)": h["volatilitas_tahunan"] * 100,
        "Return Tahunan (%)": h["return_tahunan"] * 100,
        "Kategori Risiko": h["kategori_risiko"],
        "Sharpe": h["sharpe"],
    } for h in hasil])

    fig_scatter = px.scatter(
        df_scatter, x="Volatilitas (%)", y="Return Tahunan (%)",
        text="Aset", color="Kategori Risiko", size=df_scatter["Sharpe"].abs() + 0.1,
        color_discrete_map={"Rendah": "#2ecc71", "Sedang": "#f39c12", "Tinggi": "#e74c3c"},
        hover_data={"Sharpe": ":.2f"},
    )
    fig_scatter.update_traces(textposition="top center")
    fig_scatter.add_hline(y=0, line_dash="dot", line_color="gray")
    fig_scatter.update_layout(height=500)
    st.plotly_chart(fig_scatter, use_container_width=True)

    # ---------------- GRAFIK HARGA HISTORIS ----------------
    st.subheader("📉 Pergerakan Harga (Ternormalisasi)")
    st.caption("Semua harga dinormalisasi ke basis 100 di awal periode agar mudah dibandingkan.")

    fig_harga = go.Figure()
    for h in hasil:
        series = h["close_series"]
        normalized = (series / series.iloc[0]) * 100
        fig_harga.add_trace(go.Scatter(
            x=normalized.index, y=normalized.values,
            mode="lines", name=h["ticker"],
        ))
    fig_harga.update_layout(
        height=500,
        yaxis_title="Harga (basis 100)",
        xaxis_title="Tanggal",
        hovermode="x unified",
    )
    st.plotly_chart(fig_harga, use_container_width=True)

    # ---------------- DETAIL PER ASET ----------------
    with st.expander("📋 Lihat detail metrik per aset"):
        for h in hasil_sorted:
            st.markdown(f"**{h['ticker']}** — {label_rekomendasi(h['skor_normal'])}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Return Tahunan", f"{h['return_tahunan']*100:.1f}%")
            c2.metric("Volatilitas", f"{h['volatilitas_tahunan']*100:.1f}%")
            c3.metric("Sharpe Ratio", f"{h['sharpe']:.2f}")
            c4.metric("Max Drawdown", f"{h['max_drawdown']*100:.1f}%")
            st.divider()

    st.caption(f"Data diperbarui: {datetime.now().strftime('%d %B %Y, %H:%M')}")

else:
    st.info(
        "👈 Atur kategori aset dan rentang waktu di sidebar, lalu klik "
        "**'Jalankan Analisis'** untuk melihat hasilnya."
    )

    st.markdown("""
    ### Apa yang bisa dilakukan aplikasi ini?
    - 📈 Mengambil data harga terkini untuk saham, kripto, dan ETF/reksadana dari Yahoo Finance
    - 📊 Menghitung metrik risiko: volatilitas, Sharpe Ratio, Max Drawdown, Value at Risk (VaR)
    - 🎯 Memetakan aset berdasarkan risiko vs return dalam satu grafik
    - 🏆 Memberi skor & sinyal relatif antar aset yang kamu pilih

    ### Yang TIDAK dilakukan aplikasi ini
    - ❌ Tidak memprediksi harga masa depan
    - ❌ Tidak memberi jaminan keuntungan
    - ❌ Tidak menggantikan riset fundamental atau nasihat profesional
    """)
