# patterns/boa.py — BOA BreakOut Anticipation
import numpy as np
from utils import is_ol, is_doji, vol_ratio
from config import BOA as CFG, ALL_WL


def scan_boa(all_ohlcv, avg_vols, target_date, verbose=False):
    """
    Scan BOA (6/6) dan Hampir BOA (4-5/6) untuk semua saham.
    
    Kriteria BOA (dalam window 6-9H):
    1. Range High-Low <= 25%
    2. Ada spike H/P >= 7% sebagai pemantik
    3. Vol hari ini < 0.7x avg (mengering)
    4. OL+Doji minimal 3 hari dalam window
    5. Close dekat Low: DistLow < 15%
    6. CAvg >= 3 hari dalam window
    
    Return: (boa_full, boa_near) — list of dict
    """
    boa_full = []
    boa_near = []

    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target_date:
            continue

        avg_vol = avg_vols.get(code, 1.0)
        b0 = bars[-1]
        vr0 = vol_ratio(b0, avg_vol)
        in_wl = code in ALL_WL

        best_entry = None
        best_passed = 0

        for W in range(CFG['window_max'], CFG['window_min'] - 1, -1):
            if len(bars) < W:
                continue

            recent = bars[-W:]
            hs = [b['H'] for b in recent if b.get('H')]
            ls = [b['L'] for b in recent if b.get('L')]
            if not hs or not ls:
                continue

            h_max = max(hs)
            l_min = min(ls)
            if l_min == 0:
                continue

            rng  = (h_max - l_min) / l_min * 100
            dist = (b0['C'] - l_min) / l_min * 100

            # Spike dalam window
            spikes = []
            for b in recent:
                if not b.get('H') or not b.get('P') or b['P'] <= 0:
                    continue
                hvp = (b['H'] - b['P']) / b['P'] * 100
                if hvp >= CFG['spike_min']:
                    spikes.append({
                        'date': b['date'][5:],
                        'hvp':  round(hvp, 1),
                        'vr':   round(vol_ratio(b, avg_vol), 2),
                    })

            n_ol   = sum(1 for b in recent if is_ol(b))
            n_doji = sum(1 for b in recent if is_doji(b))
            n_ca   = sum(1 for b in recent if b.get('A') and b['C'] < b['A'])

            vols_w = [vol_ratio(b, avg_vol) for b in recent if b.get('V', 0) > 0]
            v_start = vols_w[0] if vols_w else 0
            v_end   = vols_w[-1] if vols_w else 0

            # 6 kriteria
            c1 = rng <= CFG['range_max']
            c2 = len(spikes) > 0
            c3 = vr0 < CFG['vol_threshold']
            c4 = (n_ol + n_doji) >= CFG['ol_doji_min']
            c5 = dist < CFG['dist_low_max']
            c6 = n_ca >= CFG['cavg_min']

            passed = sum([c1, c2, c3, c4, c5, c6])

            # Scoring
            sc = 50.0
            if c1: sc += (25 - rng) * 1.5
            if c5: sc += (15 - dist) * 1.0
            if c3: sc += (CFG['vol_threshold'] - vr0) * 20
            sc += (n_ol + n_doji) * 5 + n_ca * 3
            sc += len(spikes) * 10
            if spikes: sc += max(s['hvp'] for s in spikes) * 0.5
            if v_end < v_start: sc += (v_start - v_end) * 5
            if in_wl: sc += 30

            fails = []
            if not c1: fails.append(f"Range{rng:.1f}%")
            if not c2: fails.append("NoSpike")
            if not c3: fails.append(f"Vol{vr0:.2f}x")
            if not c4: fails.append(f"OL+Dj={n_ol+n_doji}")
            if not c5: fails.append(f"DistLow+{dist:.1f}%")
            if not c6: fails.append(f"CAvg={n_ca}")

            entry = {
                'code':      code,
                'in_wl':     in_wl,
                'close':     int(b0['C']),
                'chg':       round((b0['C'] - b0['P']) / b0['P'] * 100, 2) if b0.get('P') and b0['P'] > 0 else 0,
                'hvp':       round((b0['H'] - b0['P']) / b0['P'] * 100, 2) if b0.get('H') and b0.get('P') and b0['P'] > 0 else 0,
                'vol':       round(vr0, 2),
                'score':     round(sc, 1),
                'window':    W,
                'rng':       round(rng, 1),
                'dist_low':  round(dist, 1),
                'n_ol':      n_ol,
                'n_doji':    n_doji,
                'n_cavg':    n_ca,
                'n_spike':   len(spikes),
                'max_spike': round(max(s['hvp'] for s in spikes), 1) if spikes else 0,
                'vdown':     v_end < v_start,
                'v_start':   round(v_start, 2),
                'v_end':     round(v_end, 2),
                'spikes':    spikes[:3],
                'passed':    passed,
                'fails':     fails,
            }

            if passed > best_passed or (passed == best_passed and sc > (best_entry['score'] if best_entry else 0)):
                best_passed = passed
                best_entry = entry

        if best_entry:
            if best_entry['passed'] == 6:
                boa_full.append(best_entry)
            elif best_entry['passed'] >= 4:
                boa_near.append(best_entry)

    # Sort: WL first, score descending
    boa_full.sort(key=lambda x: (-int(x['in_wl']), -x['score']))
    boa_near.sort(key=lambda x: (-int(x['in_wl']), -x['score']))

    return boa_full, boa_near
