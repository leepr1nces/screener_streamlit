# utils/validator.py — Validasi sinyal hari sebelumnya
from utils import pct


def validate_signals(all_ohlcv, prev_date, curr_date, watch_codes):
    """
    Validasi sinyal dari prev_date terhadap pergerakan di curr_date.
    
    Returns dict:
    {
        'naik_c':  int,   # jumlah naik close
        'naik_h':  int,   # jumlah naik high
        'total':   int,
        'pct_c':   float,
        'pct_h':   float,
        'details': list of dict,
    }
    """
    naik_c = 0; naik_h = 0; total = 0
    details = []

    for code in watch_codes:
        bars = all_ohlcv.get(code, [])
        # Cari bar prev dan curr
        b_prev = next((b for b in bars if b['date'] == prev_date), None)
        b_curr = next((b for b in bars if b['date'] == curr_date), None)
        if not b_prev or not b_curr:
            continue

        prev  = b_prev['C']
        close = b_curr['C']
        high  = b_curr.get('H') or close

        chg_c = pct(close, prev)
        chg_h = pct(high, prev)
        total += 1

        hit_c = chg_c > 0.5
        hit_h = chg_h > 0.5
        if hit_c: naik_c += 1
        if hit_h: naik_h += 1

        details.append({
            'code':   code,
            'prev':   int(prev),
            'close':  int(close),
            'high':   int(high),
            'chg_c':  round(chg_c, 2),
            'chg_h':  round(chg_h, 2),
            'hit_c':  hit_c,
            'hit_h':  hit_h,
            'gap':    round(chg_h - chg_c, 2),
        })

    return {
        'naik_c': naik_c,
        'naik_h': naik_h,
        'total':  total,
        'pct_c':  round(naik_c / total * 100, 1) if total > 0 else 0,
        'pct_h':  round(naik_h / total * 100, 1) if total > 0 else 0,
        'details': sorted(details, key=lambda x: -x['chg_h']),
    }
