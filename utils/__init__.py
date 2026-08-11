# utils/__init__.py
from .loader import load_xls_folder, load_yfinance, get_avg_vol, get_latest_date, filter_target_date

def is_ol(b, tol=0.5):
    """Open = Low (toleransi tol%)"""
    if not b or not b.get('O') or not b.get('L') or b['O'] == 0:
        return False
    return abs(b['O'] - b['L']) / b['O'] * 100 < tol

def is_doji(b, tol=0.8):
    """Open = Close (toleransi tol%)"""
    if not b or not b.get('O') or b['O'] == 0:
        return False
    c = b['C'] or b['O']
    return abs(c - b['O']) / b['O'] * 100 < tol

def candle_type(b):
    """Return tipe candle: OL+Doji, OL, Doji, Hijau, Merah, None"""
    if b is None:
        return None
    ol = is_ol(b)
    dj = is_doji(b)
    if ol and dj: return 'OL+Doji'
    if ol: return 'OL'
    if dj: return 'Doji'
    if b.get('O') and b['C'] > b['O']: return 'Hijau'
    if b.get('O') and b['C'] < b['O']: return 'Merah'
    return None

def pct(a, b):
    """Hitung persentase (a-b)/b*100"""
    if not b or b == 0:
        return 0.0
    return (a - b) / b * 100

def vol_ratio(b, avg_vol):
    """Hitung rasio volume terhadap avg"""
    if not avg_vol or avg_vol == 0:
        return 0.0
    return b.get('V', 0) / avg_vol
