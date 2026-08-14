"""
BOS — Break Out Soon
Window: 7 hari trading ke belakang
Syarat: ≥2 hari dengan High/Prev >10% + Vol > MA20
Entry: CAVG (Close < High AND Close < Avg) atau Vol Kering (<0.7x avg 4H)
"""
import numpy as np

def scan_bos(all_ohlcv, avg_vols, target, ALL_WL, window=7):
    results = []
    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target: continue
        if len(bars) < window + 2: continue
        in_wl = code in ALL_WL

        today = bars[-1]
        win = bars[-(window+1):-1]  # 7 hari trading sebelum hari ini

        spike_days = []
        for w_idx, wb in enumerate(win):
            pos = len(bars) - (window+1) + w_idx
            prev20 = bars[max(0, pos-20):pos]
            vols = [b['V'] for b in prev20 if b.get('V', 0) > 0]
            ma_vol = np.mean(vols) if vols else 0
            if not wb.get('H') or not wb.get('P') or wb['P'] <= 0: continue
            hvp = (wb['H'] - wb['P']) / wb['P'] * 100
            vol_ok = wb['V'] > ma_vol if ma_vol > 0 else wb['V'] > 0
            if hvp > 10 and vol_ok:
                spike_days.append({
                    'date': wb['date'][5:],
                    'hvp': round(hvp, 1),
                    'vol': wb['V'],
                    'ma_vol': round(ma_vol)
                })

        if len(spike_days) < 2: continue

        # Entry signal
        cavg = False
        vol_kering = False
        if today.get('H') and today.get('C') and today.get('A'):
            cavg = (today['C'] < today['H']) and (today['C'] < today['A'])
        prev4_vols = [b['V'] for b in bars[-5:-1] if b.get('V', 0) > 0]
        if prev4_vols:
            vol_kering = today['V'] < np.mean(prev4_vols) * 0.7

        if cavg and vol_kering:
            entry = "CAVG+VolKering"
            score = 100
        elif cavg:
            entry = "CAVG"
            score = 70
        elif vol_kering:
            entry = "VolKering"
            score = 70
        else:
            entry = "Tunggu"
            score = 40

        score += len(spike_days) * 10
        if in_wl: score += 30

        chg0 = (today['C'] - today['P']) / today['P'] * 100 if today.get('P') and today['P'] > 0 else 0
        hvp0 = (today['H'] - today['P']) / today['P'] * 100 if today.get('H') and today.get('P') and today['P'] > 0 else 0

        results.append({
            'code': code, 'in_wl': in_wl,
            'close': int(today['C']), 'chg': round(chg0, 2), 'hvp': round(hvp0, 2),
            'spikes': spike_days, 'n_spike': len(spike_days),
            'entry': entry, 'score': score,
            'cavg': cavg, 'vol_kering': vol_kering,
        })

    results.sort(key=lambda x: (-int(x['in_wl']), -x['score']))
    return results
