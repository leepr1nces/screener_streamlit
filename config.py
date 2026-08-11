# config.py — Konfigurasi Screener IDX Hadi Lie
# Edit file ini untuk menyesuaikan watchlist dan parameter

# ── WATCHLIST ──────────────────────────────────────────────────────────────────
WL2025 = [
    'CUAN','ADMG','CDIA','AYLS','GZCO','DOOH','DEWA','FAST','BNBR','KJEN','DATA',
    'GRIA','FIRE','BAJA','BOAT','GTSI','BRMS','CENT','INDX','BUMI','CINT','KAQI','HRTA',
    'KOCI','DPUM','BINO','GRPH','ELIT','ESIP','ASLC','APEX','JKON','HUMI','IMJS','AGRO',
    'GEMA','KBLV','LABA','BELL','KOKA','JAWA','CSIS','KLAS','JAYA','JAST','HOPE','HDIT',
    'GULA','FORE','DSFI','CHEM','CGAS','CARS','BWPT','BSBK','BRRC','BKSL','BAPA','BABY',
    'ATLA','AHAP','AGRS','ADCP','ACRO','BIPI','KOBX','CAKK','DGIK','DOSS','BBRM','BGTG',
    'FOLK','AISA','BVIC','HDFA','KIOS','BATR','IKAN','ERTX','DYAN','ISEA','HALO','GTBO',
    'KRYA','DGNS','CRSN','BAIK','GPRA','GTRA','GSMF','KUAS','DIVA','INOV','DNAR','ENRG',
    'CITY','DFAM','BEER','MSKY','SDMU','WAPO','PTMP','LUCK','OPMS','FWCT','STRK','MBTO',
    'WOWS','MPIX','NETV','OKAS','KPIG','DKHH','SWID','DEFI','TRON','NTBK','NCKL','ENZO',
    'NICL','WIFI','ARTO',
]

WL_EXTRA = [
    'MBMA','SSMS','EMTK','FILM','SULI','TINS','TOOL','PSDN','ESTA',
    'RICY','SMLE','HERO','IKAN','BBHI',
]

ALL_WL = set(WL2025 + WL_EXTRA)

# ── PARAMETER POLA ─────────────────────────────────────────────────────────────

# BOA — BreakOut Anticipation
BOA = {
    'window_min': 6,         # window minimum (hari)
    'window_max': 9,         # window maximum (hari)
    'range_max': 25,         # Range High-Low maksimum (%)
    'spike_min': 7,          # Spike H/P minimum (%)
    'vol_threshold': 0.7,    # Vol < threshold × avg = "kering"
    'ol_doji_min': 3,        # OL+Doji minimal dalam window
    'dist_low_max': 15,      # Close dari Low maksimum (%)
    'cavg_min': 3,           # Close < Avg minimal (hari)
}

# P1 — RCDrop1
P1 = {
    'spike_hvp_min': 10,     # Spike H/P minimal (%)
    'spike_vol_min': 2.0,    # Volume spike minimal × avg
    'lag_max': 5,            # Maksimal lag setelah spike (hari)
    'vol_dry_max': 0.7,      # Vol kering threshold
    'max_ca_limit': 8,       # maxCA limit (%)
}

# P2 — Spike Rebound
P2 = {
    'spike_hvp_min': 15,     # Spike H/P minimal (%)
    'spike_close_min': 10,   # Spike close minimal (%)
    'spike_vol_min': 3.0,    # Volume spike minimal × avg
    'vol_dry_max': 0.3,      # Vol hari berikut kering
    'low_open_max': -5,      # Low/Open maksimum (%)
}

# P3 — Momentum
P3 = {
    'spk1_hvp_min': 10,      # Spike 1 H/P minimal (%)
    'spk1_vol_min': 1.5,     # Volume spike 1 minimal
    'spk2_hvp_min': 7,       # Spike 2 H/P minimal (%)
    'vol_dry_max': 0.5,      # Vol kering setelah 2 spike
}

# OL Berturut
OL_SEQ = {
    'tol_ol': 0.5,           # Toleransi Open=Low (%)
    'tol_doji': 0.8,         # Toleransi Open=Close (%)
    'min_days': 2,           # Minimal hari sequence
}

# SV — Spike Valuasi
SV = {
    'spike_hvp_min': 7,      # Spike H/P minimal (%)
    'val_min': 800_000_000,  # Nilai transaksi minimal (Rp)
    'val_max': 5_000_000_000,# Nilai transaksi maksimal (Rp)
    'lookback': 10,          # Lookback hari
    'max_chg15': 13,         # Max close 15H (%)
}

# TT — Time Trading
TT = {
    'spike_min': 10,         # Spike minimal (%)
    'bar_min': 3,            # Bar minimal setelah spike
    'bar_max': 7,            # Bar maksimal setelah spike
    'bar_ideal': [4, 5],     # Bar ideal (zona entry terbaik)
    'low_range_max': 15,     # Low range setelah spike (%)
    'max_ca_limit': 8,       # maxCA limit (%)
    'avg_vol_max': 1.2,      # Avg vol setelah spike
}

# Alert Reversal
ALERT = {
    'acc_drop_min': -8,      # Akumulasi drop 5H minimal (%)
    'med_vol_max': 0.7,      # Median vol kering
    'min_red': 2,            # Minimal candle merah
}

# Scan Bersih
SCAN_BERSIH = {
    'max_chg15': 13,         # Max close change 15H (%)
}

# ── PARAMETER TEKNIS ──────────────────────────────────────────────────────────

# Minimum data bars untuk analisa
MIN_BARS = 8
MIN_BARS_RELAXED = 6  # jika data terbatas

# Avg vol dihitung dari bars[:-3] (exclude 3 hari terakhir)
AVG_VOL_EXCLUDE = 3

# ── YFINANCE ─────────────────────────────────────────────────────────────────
YFINANCE = {
    'suffix': '.JK',         # Suffix IDX di Yahoo Finance
    'period': '3mo',         # Period historis
    'interval': '1d',        # Interval data
}

# ── OUTPUT ───────────────────────────────────────────────────────────────────
OUTPUT = {
    'dir': 'output',
    'wl_top_n': 25,          # Tampilkan top N WL di scan bersih
    'boa_top_n': 30,         # Tampilkan top N BOA
    'save_txt': True,        # Simpan ke file .txt
    'save_csv': True,        # Simpan ringkasan ke .csv
    'print_color': True,     # Warna di terminal
}
