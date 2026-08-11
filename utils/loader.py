# utils/loader.py — Load data OHLCV dari berbagai sumber
import os, glob, re
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def load_xls_folder(folder='data', verbose=True):
    """
    Load semua file .xls/.xlsx dari folder ke dict {code: [bars]}
    bars = list of dict {date, O, H, L, C, A, V, P, Val}
    """
    patterns = [
        os.path.join(folder, '*.xlsx'),
        os.path.join(folder, '*.xls'),
        os.path.join(folder, '*.csv'),
    ]
    all_files = []
    for pat in patterns:
        all_files.extend(glob.glob(pat))
    all_files = sorted(set(all_files))

    if verbose:
        print(f"  Ditemukan {len(all_files)} file di folder '{folder}'")

    all_ohlcv = {}
    for path in all_files:
        date = _extract_date(path)
        if date is None:
            if verbose: print(f"  [SKIP] {os.path.basename(path)} — tanggal tidak terbaca")
            continue
        try:
            df = _read_file(path)
        except Exception as e:
            if verbose: print(f"  [ERROR] {os.path.basename(path)}: {e}")
            continue

        count = 0
        for _, row in df.iterrows():
            code = str(row.get('Code', '')).strip()
            if not code or not code.isalpha() or len(code) > 6:
                continue
            close = _safe_float(row.get('Close'))
            if close is None or close == 0:
                continue
            bar = {
                'date': date,
                'O': _safe_float(row.get('Open')),
                'H': _safe_float(row.get('High')),
                'L': _safe_float(row.get('Low')),
                'C': close,
                'A': _safe_float(row.get('Avg')),
                'V': _safe_float(row.get('Volume')) or 0.0,
                'P': _safe_float(row.get('Prev')),
                'Val': _safe_float(row.get('Value')) or 0.0,
            }
            all_ohlcv.setdefault(code, []).append(bar)
            count += 1

        if verbose:
            print(f"  [{date}] {os.path.basename(path)}: {count} saham")

    # Sort dan deduplicate tiap code
    for code in all_ohlcv:
        seen = set()
        deduped = []
        for b in sorted(all_ohlcv[code], key=lambda x: x['date']):
            if b['date'] not in seen:
                seen.add(b['date'])
                deduped.append(b)
        all_ohlcv[code] = deduped

    if verbose:
        print(f"  Total: {len(all_ohlcv)} saham unik\n")

    return all_ohlcv


def load_yfinance(codes, period='3mo', suffix='.JK', verbose=True):
    """
    Load data dari yfinance untuk list kode saham IDX
    Membutuhkan: pip install yfinance
    Data delay ~15 menit dari pasar
    """
    try:
        import yfinance as yf
    except ImportError:
        print("ERROR: yfinance belum diinstall. Jalankan: pip install yfinance")
        return {}

    tickers = [f"{c}{suffix}" for c in codes]
    if verbose:
        print(f"  Mengambil data {len(tickers)} saham dari Yahoo Finance...")
        print(f"  Period: {period} | Suffix: {suffix}")

    all_ohlcv = {}
    batch_size = 20  # yfinance lebih stabil dengan batch kecil

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        try:
            raw = yf.download(
                batch,
                period=period,
                interval='1d',
                auto_adjust=True,
                progress=False,
                group_by='ticker',
            )
        except Exception as e:
            if verbose: print(f"  [ERROR] batch {i//batch_size+1}: {e}")
            continue

        for ticker in batch:
            code = ticker.replace(suffix, '')
            try:
                if len(batch) == 1:
                    df = raw
                else:
                    df = raw[ticker] if ticker in raw.columns.get_level_values(0) else pd.DataFrame()

                if df.empty:
                    continue

                bars = []
                prev_close = None
                for dt, row in df.iterrows():
                    date_str = dt.strftime('%Y-%m-%d')
                    bar = {
                        'date': date_str,
                        'O': float(row.get('Open', 0) or 0),
                        'H': float(row.get('High', 0) or 0),
                        'L': float(row.get('Low', 0) or 0),
                        'C': float(row.get('Close', 0) or 0),
                        'A': float(row.get('Close', 0) or 0),  # yfinance tidak punya Avg
                        'V': float(row.get('Volume', 0) or 0),
                        'P': prev_close,
                        'Val': 0.0,  # yfinance tidak punya Value
                    }
                    if bar['C'] > 0:
                        bars.append(bar)
                        prev_close = bar['C']

                if bars:
                    all_ohlcv[code] = bars
                    if verbose and i == 0:
                        print(f"  {code}: {len(bars)} bars ({bars[0]['date']} s/d {bars[-1]['date']})")

            except Exception as e:
                if verbose: print(f"  [SKIP] {code}: {e}")
                continue

    if verbose:
        print(f"  Berhasil load {len(all_ohlcv)} saham dari yfinance\n")

    return all_ohlcv


def _read_file(path):
    """Baca file ke DataFrame, normalisasi kolom"""
    ext = os.path.splitext(path)[1].lower()
    if ext == '.csv':
        df = pd.read_csv(path)
    elif ext in ['.xlsx', '.xls']:
        try:
            df = pd.read_excel(path, sheet_name='Trades')
        except Exception:
            df = pd.read_excel(path)

    # Normalisasi nama kolom
    df.columns = [str(c).strip() for c in df.columns]

    # Handle kolom Close yang mungkin bernama 'Last'
    if 'Close' not in df.columns and 'Last' in df.columns:
        df['Close'] = df['Last']
    elif 'Close' in df.columns and 'Last' in df.columns:
        df['Close'] = df['Close'].fillna(df['Last'])

    # Konversi numerik
    for col in ['Open', 'High', 'Low', 'Close', 'Avg', 'Volume', 'Prev', 'Value', 'Last']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def _extract_date(path):
    """Ekstrak tanggal dari nama file"""
    fname = os.path.basename(path)
    # Format: Screener_Saham_YYYYMMDD_...
    m = re.search(r'(\d{8})', fname)
    if m:
        raw = m.group(1)
        try:
            dt = datetime.strptime(raw, '%Y%m%d')
            return dt.strftime('%Y-%m-%d')
        except:
            return None
    # Format: DDMMYYYY atau tanggal lain
    m2 = re.search(r'(\d{4}-\d{2}-\d{2})', fname)
    if m2:
        return m2.group(1)
    return None


def _safe_float(val):
    try:
        v = float(val)
        return v if not (v != v) else None  # NaN check
    except:
        return None


def get_latest_date(all_ohlcv):
    """Dapatkan tanggal terbaru dari data"""
    dates = []
    for bars in all_ohlcv.values():
        if bars:
            dates.append(bars[-1]['date'])
    return max(dates) if dates else None


def get_avg_vol(bars, exclude_last=3):
    """Hitung avg volume dari bars, exclude N hari terakhir"""
    vols = [b['V'] for b in bars if b['V'] > 0]
    if len(vols) > exclude_last:
        vols = vols[:-exclude_last]
    return float(np.mean(vols)) if vols else 1.0


def filter_target_date(all_ohlcv, target_date):
    """Filter hanya saham yang ada di target_date"""
    return {
        code: bars for code, bars in all_ohlcv.items()
        if bars and bars[-1]['date'] == target_date
    }
