"""
Aplikasi Analisis & Rekomendasi Investasi
------------------------------------------
Menampilkan data harga terkini, metrik risiko, dan skor rekomendasi
untuk saham, kripto, atau aset campuran menggunakan data dari Yahoo Finance.

PENTING: Aplikasi ini adalah ALAT BANTU ANALISIS, bukan nasihat keuangan.
Semua keputusan investasi tetap menjadi tanggung jawab pengguna.
"""

import streamlit as st
import streamlit.components.v1 as components
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
# SUKU BUNGA BEBAS RISIKO OTOMATIS (^IRX = obligasi AS 13 minggu, ~1 kuartal)
# =========================================================
@st.cache_data(ttl=3600, show_spinner=False)
def ambil_suku_bunga_otomatis() -> float:
    """Ambil suku bunga bebas risiko dari yield obligasi pemerintah AS 13 minggu (^IRX, ~1 kuartal)."""
    try:
        data = yf.download("^IRX", period="5d", progress=False, auto_adjust=True)
        close = data["Close"].dropna()
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        nilai_persen = float(close.iloc[-1])
        # Validasi kewajaran: yield jangka pendek biasanya di rentang 0.1%-15%
        if 0.1 <= nilai_persen <= 15:
            return nilai_persen / 100
        return 0.04  # fallback kalau angkanya di luar rentang wajar
    except Exception:
        return 0.04  # fallback default 4% kalau gagal ambil data

suku_bunga_otomatis = ambil_suku_bunga_otomatis()

# =========================================================
# ANIMASI OPENING "GERBANG TERBUKA" — cuma muncul sekali per sesi
# =========================================================
if "gerbang_terbuka" not in st.session_state:
    st.session_state.gerbang_terbuka = True
    st.markdown(
        """
        <style>
        @keyframes bukaKiri {
            0%   { transform: translateX(0); }
            100% { transform: translateX(-101%); }
        }
        @keyframes bukaKanan {
            0%   { transform: translateX(0); }
            100% { transform: translateX(101%); }
        }
        @keyframes putarRoda {
            0%   { transform: translate(-50%, -50%) rotate(0deg); }
            100% { transform: translate(-50%, -50%) rotate(1080deg); }
        }
        @keyframes hilangRoda {
            0%   { opacity: 1; transform: translate(-50%, -50%) rotate(1080deg) scale(1); }
            100% { opacity: 0; transform: translate(-50%, -50%) rotate(1260deg) scale(0.5); }
        }
        @keyframes munculLogo {
            0%   { opacity: 0; transform: translate(-50%, -50%) scale(0.85); }
            30%  { opacity: 0; }
            45%  { opacity: 1; transform: translate(-50%, -50%) scale(1.03); }
            65%  { opacity: 1; transform: translate(-50%, -50%) scale(1); }
            88%  { opacity: 0; }
            100% { opacity: 0; }
        }
        @keyframes electricFlow {
            to { stroke-dashoffset: -692; }
        }

        #gerbang-wrapper {
            position: fixed; inset: 0; z-index: 999999;
            pointer-events: none; overflow: hidden;
            background: #05070d;
        }

        #electric-svg {
            position: absolute; inset: 0; width: 100%; height: 100%;
            mix-blend-mode: screen; opacity: 0.75;
        }
        /* Garis dasar: solid, lurus/utuh, tidak putus-putus */
        .electric-base { fill: none; stroke-width: 1.8; opacity: 0.4; }
        .electric-base.cyan { stroke: #00e5ff; }
        .electric-base.purple { stroke: #7b2ff7; }
        /* Percikan yang mengalir DI ATAS garis dasar (ini yang bergerak) */
        .electric-spark {
            fill: none; stroke-width: 3; stroke-linecap: round;
            stroke-dasharray: 26 320;
            animation: electricFlow 1.8s linear infinite;
            filter: drop-shadow(0 0 5px currentColor);
        }
        .electric-spark.cyan { stroke: #baf9ff; }
        .electric-spark.purple { stroke: #e6d1ff; }

        /* ===== PANEL VAULT (pintu brankas kiri & kanan) ===== */
        #gerbang-kiri, #gerbang-kanan {
            position: absolute; top: 0; width: 50%; height: 100%;
            background:
                radial-gradient(circle at 22% 28%, rgba(150,90,40,0.30) 0%, rgba(150,90,40,0) 13%),
                radial-gradient(circle at 75% 65%, rgba(140,80,35,0.25) 0%, rgba(140,80,35,0) 11%),
                radial-gradient(circle at 45% 85%, rgba(120,70,30,0.22) 0%, rgba(120,70,30,0) 9%),
                linear-gradient(135deg, #4a4f5a 0%, #2c2f37 45%, #16181d 100%);
            box-shadow: inset 0 0 60px rgba(0,0,0,0.65);
            animation-duration: 0.9s;
            animation-timing-function: cubic-bezier(0.76, 0, 0.24, 1);
            animation-delay: 1.35s;
            animation-fill-mode: forwards;
        }
        #gerbang-kiri {
            left: 0; animation-name: bukaKiri;
            box-shadow: inset 0 0 60px rgba(0,0,0,0.65), 8px 0 30px rgba(0, 229, 255, 0.15);
        }
        #gerbang-kanan {
            right: 0; animation-name: bukaKanan;
            box-shadow: inset 0 0 60px rgba(0,0,0,0.65), -8px 0 30px rgba(123, 47, 247, 0.15);
        }
        /* Baris paku/rivet besi di tepi dalam tiap panel */
        #gerbang-kiri::before, #gerbang-kanan::before {
            content: ''; position: absolute; top: 0; bottom: 0; width: 16px;
            background-image: radial-gradient(circle, #8a8f96 3px, transparent 3.6px);
            background-size: 22px 32px; background-repeat: repeat-y;
            opacity: 0.85;
        }
        #gerbang-kiri::before { right: 26px; }
        #gerbang-kanan::before { left: 26px; }
        /* Goresan karat memanjang tambahan */
        #gerbang-kiri::after, #gerbang-kanan::after {
            content: ''; position: absolute; inset: 0;
            background:
                linear-gradient(100deg, transparent 40%, rgba(130,75,35,0.12) 50%, transparent 60%),
                linear-gradient(20deg, transparent 60%, rgba(130,75,35,0.10) 68%, transparent 76%);
        }

        /* ===== RODA PEMUTAR: SETIR KAPAL DARI LOGAM BERKARAT ===== */
        #vault-wheel {
            position: absolute; top: 50%; left: 50%;
            width: 240px; height: 240px;
            z-index: 10;
            animation: putarRoda 1.1s cubic-bezier(0.25, 0.85, 0.35, 1) forwards,
                       hilangRoda 0.35s ease-in forwards;
            animation-delay: 0s, 1.05s;
        }
        /* Pelek luar (rim) — cincin logam, tengah tembus (bukan cakram penuh) */
        .wheel-ring {
            position: absolute; inset: 48px; border-radius: 50%;
            background:
                radial-gradient(circle at 25% 20%, rgba(160,95,40,0.28) 0%, rgba(160,95,40,0) 12%),
                radial-gradient(circle at 70% 75%, rgba(140,80,35,0.24) 0%, rgba(140,80,35,0) 10%),
                radial-gradient(circle at 35% 30%, #9a9fa6, #4a4d52 55%, #202226 90%);
            border: 13px solid #5b5f66;
            box-shadow: 0 0 30px rgba(0,0,0,0.7), inset 0 0 20px rgba(0,0,0,0.75),
                        0 0 26px rgba(0, 229, 255, 0.2);
        }
        /* Alur/rib melingkar di pelek, kesan logam ditempa/dibubut */
        .wheel-ring::before {
            content: ''; position: absolute; inset: -13px; border-radius: 50%;
            background: repeating-conic-gradient(
                from 0deg,
                rgba(255,255,255,0.10) 0deg 3deg,
                rgba(0,0,0,0.18) 3deg 7deg
            );
            mix-blend-mode: overlay;
        }
        .wheel-ring::after {
            content: ''; position: absolute; inset: 11px; border-radius: 50%;
            border: 2px dashed rgba(0,0,0,0.4);
        }
        /* Jari-jari roda (spoke) — pivot presisi di titik pusat roda via margin, bukan translate% */
        .wheel-spoke {
            position: absolute; top: 50%; left: 50%;
            margin-left: -5.5px; /* setengah lebar (11px), biar pivot pas di tengah tanpa translate rancu */
            width: 11px; height: 80px;
            background:
                radial-gradient(circle at 30% 65%, rgba(150,85,35,0.35) 0%, rgba(150,85,35,0) 12%),
                linear-gradient(180deg, #9298a0, #6b6f76 55%, #3a3d43);
            border-radius: 4px;
            box-shadow: 0 0 9px rgba(0,0,0,0.5);
            transform-origin: top center; /* pivot = titik pusat roda */
        }
        /* Leher penghubung ke pegangan — nyambung di ujung luar jari-jari */
        .wheel-spoke::before {
            content: ''; position: absolute; top: 77px; left: 50%;
            width: 8px; height: 16px;
            transform: translateX(-50%);
            background: linear-gradient(180deg, #6b6f76, #4a4d52);
            border-radius: 3px;
        }
        /* Pegangan menggelembung (baluster) — pas nempel ujung pelek, tidak melayang */
        .wheel-spoke::after {
            content: '';
            position: absolute; top: 86px; left: 50%;
            width: 24px; height: 26px;
            transform: translateX(-50%);
            border-radius: 50% 50% 40% 40% / 60% 60% 40% 40%;
            background:
                radial-gradient(circle at 30% 22%, rgba(150,85,35,0.4) 0%, rgba(150,85,35,0) 30%),
                radial-gradient(ellipse at 35% 30%, #c3c8ce 0%, #8a8f96 45%, #4a4d52 85%);
            box-shadow: 0 0 12px rgba(0,0,0,0.6), inset -3px -3px 5px rgba(0,0,0,0.45),
                        inset 3px 3px 4px rgba(255,255,255,0.15);
            border: 1.5px solid rgba(150,85,35,0.4);
        }
        .spoke0 { transform: rotate(0deg); }
        .spoke1 { transform: rotate(45deg); }
        .spoke2 { transform: rotate(90deg); }
        .spoke3 { transform: rotate(135deg); }
        .spoke4 { transform: rotate(180deg); }
        .spoke5 { transform: rotate(225deg); }
        .spoke6 { transform: rotate(270deg); }
        .spoke7 { transform: rotate(315deg); }
        /* Poros tengah (hub) */
        .wheel-center {
            position: absolute; top: 50%; left: 50%;
            width: 54px; height: 54px; transform: translate(-50%, -50%);
            border-radius: 50%;
            background: radial-gradient(circle at 35% 30%, #d8dce1, #74787f 55%, #303236);
            box-shadow: 0 0 20px rgba(0, 229, 255, 0.5), inset 0 0 9px rgba(0,0,0,0.5);
            border: 3px solid rgba(150,85,35,0.35);
        }
        .wheel-center::after {
            content: ''; position: absolute; inset: 14px; border-radius: 50%;
            border: 1.5px solid rgba(0,0,0,0.35);
        }

        /* ===== TEKS SAPAAN (diterangin, kontras tinggi) ===== */
        #gerbang-logo {
            position: absolute; top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            width: 92%; max-width: 680px;
            text-align: center; z-index: 20;
            white-space: nowrap;
            animation: munculLogo 2.1s ease-in-out forwards;
        }
        #gerbang-logo .baris1 {
            display: block; font-size: 32px; font-weight: 800;
            letter-spacing: 1px; color: #ffffff;
            text-shadow: 0 0 10px #ffffff, 0 0 26px rgba(0, 229, 255, 0.9);
        }
        #gerbang-logo .baris2 {
            display: block; font-size: 16px; font-weight: 500;
            color: #d6f3ff; margin-top: 8px; letter-spacing: 0.5px;
            text-shadow: 0 0 8px rgba(255,255,255,0.6), 0 0 16px rgba(0, 229, 255, 0.7);
        }
        </style>

        <div id="gerbang-wrapper">
            <svg id="electric-svg" viewBox="0 0 1000 600" preserveAspectRatio="none">
                <polyline class="electric-base cyan" points="0,80 120,60 180,140 300,90 380,180 520,110"/>
                <polyline class="electric-base cyan" points="1000,480 880,500 820,420 700,470 640,380 500,440"/>
                <polyline class="electric-base purple" points="0,520 100,540 160,470 260,510 320,430 460,480"/>
                <polyline class="electric-base purple" points="1000,60 900,90 840,20 720,70 660,10 540,55"/>
                <polyline class="electric-base cyan" points="0,300 90,285 150,320 240,290 300,330 400,300"/>
                <polyline class="electric-base purple" points="1000,300 910,315 850,280 760,310 700,270 600,300"/>

                <polyline class="electric-spark cyan" points="0,80 120,60 180,140 300,90 380,180 520,110"/>
                <polyline class="electric-spark cyan" points="1000,480 880,500 820,420 700,470 640,380 500,440"/>
                <polyline class="electric-spark purple" points="0,520 100,540 160,470 260,510 320,430 460,480"/>
                <polyline class="electric-spark purple" points="1000,60 900,90 840,20 720,70 660,10 540,55"/>
                <polyline class="electric-spark cyan" points="0,300 90,285 150,320 240,290 300,330 400,300"/>
                <polyline class="electric-spark purple" points="1000,300 910,315 850,280 760,310 700,270 600,300"/>
            </svg>

            <div id="gerbang-kiri"></div>
            <div id="gerbang-kanan"></div>

            <div id="vault-wheel">
                <div class="wheel-ring"></div>
                <div class="wheel-spoke spoke0"></div>
                <div class="wheel-spoke spoke1"></div>
                <div class="wheel-spoke spoke2"></div>
                <div class="wheel-spoke spoke3"></div>
                <div class="wheel-spoke spoke4"></div>
                <div class="wheel-spoke spoke5"></div>
                <div class="wheel-spoke spoke6"></div>
                <div class="wheel-spoke spoke7"></div>
                <div class="wheel-center"></div>
            </div>

            <div id="gerbang-logo">
                <span class="baris1">Hello, Sir.</span>
                <span class="baris2">Welcome with your loyalty partner.</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Suara sapaan (Web Speech API, jalan lewat iframe komponen) ---
    components.html(
        """
        <script>
        (function() {
            try {
                const synth = window.speechSynthesis;
                const utter = new SpeechSynthesisUtterance("Hello, sir. Welcome with your loyalty partner.");

                function pilihSuaraLaluBicara() {
                    const voices = synth.getVoices();
                    let suara = voices.find(v => /en/i.test(v.lang) && /male|david|daniel|google uk english male/i.test(v.name));
                    if (!suara) suara = voices.find(v => /en/i.test(v.lang));
                    if (suara) utter.voice = suara;
                    utter.pitch = 0.75;   // sedikit lebih rendah, kesan robotik
                    utter.rate = 0.92;    // sedikit lebih lambat, kesan tenang & elegan
                    synth.speak(utter);
                }

                if (synth.getVoices().length === 0) {
                    synth.onvoiceschanged = pilihSuaraLaluBicara;
                } else {
                    pilihSuaraLaluBicara();
                }
            } catch (e) {
                console.log("Speech synthesis tidak didukung/diblokir:", e);
            }
        })();
        </script>
        """,
        height=0,
    )

# =========================================================
# TEMA DARK ELECTRIC (CSS custom di atas tema dasar config.toml)
# =========================================================
st.markdown(
    """
    <style>
    /* Latar belakang utama: gradient gelap kebiruan-ungu, bukan hitam polos */
    .stApp {
        background: radial-gradient(circle at 15% 0%, #131a35 0%, #0a0e17 45%, #05070d 100%);
    }

    /* Sidebar sedikit beda nuansa biar ada kedalaman */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #10142a 0%, #0a0e17 100%);
        border-right: 1px solid rgba(0, 229, 255, 0.15);
    }

    /* Kartu metric (st.metric) dikasih border glow tipis */
    div[data-testid="stMetric"] {
        background: rgba(0, 229, 255, 0.05);
        border: 1px solid rgba(0, 229, 255, 0.35);
        border-radius: 12px;
        padding: 12px 16px;
        box-shadow: 0 0 18px rgba(0, 229, 255, 0.08);
    }

    /* Tombol utama dikasih efek glow neon */
    div.stButton > button, .stDownloadButton > button {
        background: linear-gradient(90deg, #00c2ff 0%, #7b2ff7 100%);
        color: white;
        border: none;
        border-radius: 10px;
        box-shadow: 0 0 16px rgba(0, 194, 255, 0.5);
        transition: box-shadow 0.25s ease, transform 0.15s ease;
    }
    div.stButton > button:hover, .stDownloadButton > button:hover {
        box-shadow: 0 0 26px rgba(123, 47, 247, 0.7);
        transform: translateY(-1px);
        color: white;
    }

    /* Tabel dataframe: border tipis neon */
    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(0, 229, 255, 0.2);
        border-radius: 10px;
    }

    /* Judul markdown h1-h4 dikasih sedikit glow */
    h1, h2, h3, h4 {
        text-shadow: 0 0 14px rgba(0, 229, 255, 0.25);
    }

    /* Divider custom biar nggak garis putih polos */
    hr {
        border-color: rgba(0, 229, 255, 0.2) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# BANNER / HERO SECTION (visual, tanpa gambar eksternal)
# =========================================================
st.markdown(
    """
    <div style="
        background: linear-gradient(120deg, #0a0e2a 0%, #14183f 45%, #1e0b3d 100%);
        padding: 28px 32px;
        border-radius: 16px;
        margin-bottom: 18px;
        border: 1px solid rgba(0, 229, 255, 0.25);
        box-shadow: 0 0 30px rgba(123, 47, 247, 0.15);
    ">
        <h1 style="
            color:#e6f1ff; margin:0; font-size: 32px;
            text-shadow: 0 0 18px rgba(0, 229, 255, 0.5);
        ">📈 Analisis &amp; Rekomendasi Investasi</h1>
        <p style="color:#8fd8ff; margin:6px 0 0 0; font-size: 15px;">
            🌍 Saham &nbsp;•&nbsp; 🪙 Kripto &nbsp;•&nbsp; 📦 ETF/Reksadana &nbsp;—&nbsp;
            data real-time dari Yahoo Finance
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "<p style='font-style: italic; color: rgba(230,241,255,0.45); font-size: 12.5px; margin-top: -8px;'>"
    "Alat bantu analisis, bukan nasihat keuangan.</p>",
    unsafe_allow_html=True,
)

# =========================================================
# BADGE KANAN ATAS — Suku Bunga Otomatis (efek hijau glitter)
# =========================================================
st.markdown(
    f"""
    <style>
    @keyframes glitterShine {{
        0%   {{ background-position: 0% 50%; }}
        100% {{ background-position: 200% 50%; }}
    }}
    @keyframes glitterPulse {{
        0%, 100% {{ text-shadow: 0 0 8px rgba(80,255,150,0.6), 0 0 18px rgba(80,255,150,0.4); }}
        50%      {{ text-shadow: 0 0 14px rgba(140,255,190,0.9), 0 0 28px rgba(80,255,150,0.6); }}
    }}
    @keyframes sparkleBlink {{
        0%, 100% {{ opacity: 0.2; transform: scale(0.8); }}
        50%      {{ opacity: 1;   transform: scale(1.15); }}
    }}
    #suku-bunga-badge {{
        position: fixed; top: 14px; right: 18px; z-index: 100000;
        background: rgba(6, 20, 14, 0.55);
        border: 1px solid rgba(80, 255, 150, 0.35);
        border-radius: 12px;
        padding: 8px 16px;
        backdrop-filter: blur(6px);
        box-shadow: 0 0 20px rgba(80, 255, 150, 0.15);
        text-align: right;
        pointer-events: none;
    }}
    #suku-bunga-badge .label {{
        display: block; font-size: 10.5px; letter-spacing: 0.5px;
        color: rgba(200, 255, 220, 0.65); margin-bottom: 2px;
    }}
    #suku-bunga-badge .nilai {{
        font-size: 22px; font-weight: 800;
        background: linear-gradient(90deg, #4dffa0, #b8ffd9, #4dffa0, #7dffb8);
        background-size: 200% auto;
        -webkit-background-clip: text; background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: glitterShine 2.5s linear infinite, glitterPulse 1.8s ease-in-out infinite;
    }}
    #suku-bunga-badge .sparkle {{
        display: inline-block; margin-left: 3px; font-size: 13px;
        animation: sparkleBlink 1.4s ease-in-out infinite;
    }}
    #suku-bunga-badge .sparkle.s2 {{ animation-delay: 0.5s; }}
    @media (max-width: 640px) {{
        #suku-bunga-badge {{ top: 8px; right: 8px; padding: 6px 12px; }}
        #suku-bunga-badge .nilai {{ font-size: 17px; }}
    }}
    </style>
    <div id="suku-bunga-badge">
        <span class="label">📡 Suku Bunga (13 Minggu / ~1 Kuartal)</span>
        <span class="nilai">{suku_bunga_otomatis*100:.2f}%</span>
        <span class="sparkle s1">✨</span><span class="sparkle s2">✨</span>
    </div>
    """,
    unsafe_allow_html=True,
)

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
                background: {'linear-gradient(135deg, #00c896, #00e5ff)' if perubahan >= 0 else 'linear-gradient(135deg, #ff4d6d, #ff8a00)'};
                border-radius: 14px;
                width: 90px; height: 90px;
                display: flex; align-items: center; justify-content: center;
                font-size: 42px;
                box-shadow: 0 0 22px {'rgba(0, 229, 255, 0.5)' if perubahan >= 0 else 'rgba(255, 77, 109, 0.5)'};
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

    st.markdown("**Suku bunga bebas risiko** _(untuk Sharpe Ratio)_")
    gunakan_manual = st.checkbox(
        "Atur manual (bukan otomatis)",
        value=False,
        help="Defaultnya otomatis, diambil dari yield obligasi pemerintah AS 13 minggu (^IRX, ~1 kuartal) — durasi pendek, lebih responsif ke kondisi terkini.",
    )
    if gunakan_manual:
        risk_free_rate = st.slider(
            "Suku bunga bebas risiko tahunan (%)",
            min_value=0.0, max_value=15.0, value=6.0, step=0.5,
        ) / 100
    else:
        risk_free_rate = suku_bunga_otomatis
        st.caption(f"📡 Otomatis: **{risk_free_rate*100:.2f}%** (yield obligasi AS 13 minggu, ^IRX)")

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
        "ohlc_data": data,
        "pola_candlestick": deteksi_pola_candlestick(data),
    }


def deteksi_pola_candlestick(data: pd.DataFrame) -> str:
    """Deteksi pola candlestick sederhana dari 2 candle terakhir (harian)."""
    try:
        o = data["Open"].dropna()
        h = data["High"].dropna()
        l = data["Low"].dropna()
        c = data["Close"].dropna()
        for s in (o, h, l, c):
            if isinstance(s, pd.DataFrame):
                s = s.iloc[:, 0]
        if len(c) < 2:
            return "-"

        o1, h1, l1, c1 = float(o.iloc[-1]), float(h.iloc[-1]), float(l.iloc[-1]), float(c.iloc[-1])
        o0, h0, l0, c0 = float(o.iloc[-2]), float(h.iloc[-2]), float(l.iloc[-2]), float(c.iloc[-2])

        body1 = abs(c1 - o1)
        range1 = h1 - l1 if (h1 - l1) > 0 else 1e-9
        upper_shadow1 = h1 - max(c1, o1)
        lower_shadow1 = min(c1, o1) - l1
        body0 = abs(c0 - o0)

        # Doji: body sangat kecil dibanding range harian
        if body1 / range1 < 0.08:
            return "🟨 Doji"

        # Hammer: body kecil di atas, shadow bawah panjang, shadow atas pendek
        if body1 / range1 < 0.35 and lower_shadow1 > body1 * 2 and upper_shadow1 < body1 * 0.6:
            return "🔨 Hammer"

        # Shooting Star: kebalikan Hammer, shadow atas panjang
        if body1 / range1 < 0.35 and upper_shadow1 > body1 * 2 and lower_shadow1 < body1 * 0.6:
            return "🌠 Shooting Star"

        # Bullish Engulfing: candle merah lalu candle hijau yang "menelan" body sebelumnya
        if c0 < o0 and c1 > o1 and c1 >= o0 and o1 <= c0 and body1 > body0:
            return "🟢 Bullish Engulfing"

        # Bearish Engulfing: kebalikannya
        if c0 > o0 and c1 < o1 and o1 >= c0 and c1 <= o0 and body1 > body0:
            return "🔴 Bearish Engulfing"

        # Marubozu: body memenuhi hampir seluruh range (nyaris tanpa shadow)
        if body1 / range1 > 0.92:
            return "🟩 Marubozu Naik" if c1 > o1 else "🟥 Marubozu Turun"

        return "⚪ Netral"
    except Exception:
        return "-"


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
            "Pola Candlestick": h["pola_candlestick"],
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

    # ---------------- GRAFIK CANDLESTICK & POLA ----------------
    st.subheader("🕯️ Grafik Candlestick & Deteksi Pola")
    st.caption(
        "Pola candlestick dideteksi dari 2 candle harian terakhir. Ini sinyal jangka pendek "
        "(bukan jaminan arah harga) — tetap kombinasikan dengan metrik risiko di atas."
    )

    pilihan_candle = st.selectbox(
        "Pilih aset untuk lihat candlestick-nya",
        options=[h["ticker"] for h in hasil_sorted],
        key="pilihan_candlestick",
    )
    h_terpilih = next(h for h in hasil_sorted if h["ticker"] == pilihan_candle)
    ohlc = h_terpilih["ohlc_data"].tail(60)  # 60 candle terakhir biar nggak terlalu padat

    op = ohlc["Open"]; hi = ohlc["High"]; lo = ohlc["Low"]; cl = ohlc["Close"]
    if isinstance(op, pd.DataFrame): op = op.iloc[:, 0]
    if isinstance(hi, pd.DataFrame): hi = hi.iloc[:, 0]
    if isinstance(lo, pd.DataFrame): lo = lo.iloc[:, 0]
    if isinstance(cl, pd.DataFrame): cl = cl.iloc[:, 0]

    fig_candle = go.Figure(data=[go.Candlestick(
        x=ohlc.index, open=op, high=hi, low=lo, close=cl,
        increasing_line_color="#00e5ff", decreasing_line_color="#ff4d6d",
        increasing_fillcolor="rgba(0,229,255,0.5)", decreasing_fillcolor="rgba(255,77,109,0.5)",
    )])
    fig_candle.update_layout(
        height=520,
        xaxis_rangeslider_visible=False,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e6f1ff"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", title="Harga"),
    )
    st.plotly_chart(fig_candle, use_container_width=True)

    st.markdown(f"**Pola terdeteksi (candle terakhir {pilihan_candle}):** {h_terpilih['pola_candlestick']}")

    with st.expander("📖 Arti pola-pola yang bisa terdeteksi"):
        st.markdown("""
        - 🟨 **Doji** — harga buka & tutup nyaris sama → pasar ragu-ragu, bisa jadi tanda pembalikan arah
        - 🔨 **Hammer** — body kecil di atas, ekor bawah panjang → tekanan jual mereda, potensi pembalikan naik (biasanya setelah tren turun)
        - 🌠 **Shooting Star** — kebalikan Hammer, ekor atas panjang → potensi pembalikan turun (biasanya setelah tren naik)
        - 🟢 **Bullish Engulfing** — candle hijau "menelan" candle merah sebelumnya → momentum beli menguat
        - 🔴 **Bearish Engulfing** — candle merah "menelan" candle hijau sebelumnya → momentum jual menguat
        - 🟩/🟥 **Marubozu** — body penuh nyaris tanpa ekor → tren sangat kuat searah body-nya
        - ⚪ **Netral** — tidak ada pola dominan yang terdeteksi hari itu
        """)

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
    - 🕯️ Mendeteksi pola candlestick sederhana dari data harian
    """)
    st.markdown(
        "<p style='font-style: italic; color: rgba(230,241,255,0.4); font-size: 12.5px;'>"
        "Tidak memprediksi harga masa depan atau menggantikan riset profesional.</p>",
        unsafe_allow_html=True,
    )
