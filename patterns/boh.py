"""
BOH — Breakout High
Trigger Hari T: event harga signifikan (ARA atau lainnya), default Close/Prev >= 20%
Konfirmasi T+1: Gap Open >5% dari Close hari T
Entry: Vol sangat kering setelah gap (Vol < 0.5x avg 4H sebelumnya)
"""
import numpy as np

def scan_boh(all_ohlcv, avg_vols, target, ALL_WL,
             min_trigger=20.0, min_gap=5.0, vol_kering_ratio=0.5,
             max_days_after_gap=10):
    results = []
    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target: continue
        if len(bars) < 3: continue
        in_wl = code in ALL_WL

        # Cari trigger + gap dalam histori
        found = None
        for i in range(1, len(bars)-1):
            bt = bars[i]      # hari T (trigger)
            bg = bars[i+1]    # hari T+1 (gap)
            if not bt.get('C') or not bt.get('P') or bt['P'] <= 0: continue
            if not bg.get('O') or not bt.get('C') or bt['C'] <= 0: continue

            # Trigger: Close/Prev >= min_trigger%
            chg_t = (bt['C'] - bt['P']) / bt['P'] * 100
            if chg_t < min_trigger: continue

            # Gap: Open T+1 / Close T > min_gap%
            gap = (bg['O'] - bt['C']) / bt['C'] * 100
            if gap < min_gap: continue

            found = {'trigger_date': bt['date'][5:], 'trigger_chg': round(chg_t, 1),
                     'gap_date': bg['date'][5:], 'gap_pct': round(gap, 1),
                     'gap_idx': i+1}
            # Ambil yang terbaru
        
        if not found: continue

        # Cek apakah hari ini masih dalam window setelah gap
        gap_idx = found['gap_idx']
        days_after = len(bars) - 1 - gap_idx
        if days_after < 0 or days_after > max_days_after_gap: continue

        # Cek entry: vol kering di hari ini
        today = bars[-1]
        bars_after_gap = bars[gap_idx+1:]
        prev4 = bars[max(0, len(bars)-5):-1]
        prev4_vols = [b['V'] for b in prev4 if b.get('V', 0) > 0]
        vol_kering = False
        if prev4_vols:
            vol_kering = today['V'] < np.mean(prev4_vols) * vol_kering_ratio

        chg0 = (today['C'] - today['P']) / today['P'] * 100 if today.get('P') and today['P'] > 0 else 0
        hvp0 = (today['H'] - today['P']) / today['P'] * 100 if today.get('H') and today.get('P') and today['P'] > 0 else 0

        entry = "🎯 Vol Kering — ENTRY" if vol_kering else f"⏳ H+{days_after} stlh gap"
        score = (80 if vol_kering else 50) + (30 if in_wl else 0)

        results.append({
            'code': code, 'in_wl': in_wl,
            'close': int(today['C']), 'chg': round(chg0, 2), 'hvp': round(hvp0, 2),
            'trigger_date': found['trigger_date'], 'trigger_chg': found['trigger_chg'],
            'gap_date': found['gap_date'], 'gap_pct': found['gap_pct'],
            'days_after': days_after, 'vol_kering': vol_kering,
            'entry': entry, 'score': score,
        })

    results.sort(key=lambda x: (-int(x['in_wl']), -x['score']))
    return results
