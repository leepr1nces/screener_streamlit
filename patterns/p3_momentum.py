# patterns/p3_momentum.py — P2 Spike Rebound & P3 Momentum
from utils import vol_ratio, pct
from config import P2 as CFG2, P3 as CFG3, ALL_WL


def scan_p2(all_ohlcv, avg_vols, target_date):
    """
    P2 Spike Rebound:
    - Kemarin: spike H/P >= 15%, Close >= +10%, Vol >= 3x avg
    - Hari ini: vol <= 0.3x avg DAN Low/Open <= -5% (candle turun dalam)
    """
    results = []

    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target_date or len(bars) < 2:
            continue

        avg_vol = avg_vols.get(code, 1.0)
        b0 = bars[-1]
        b1 = bars[-2]
        in_wl = code in ALL_WL

        if not all([b1.get('H'), b1.get('P'), b1.get('C')]):
            continue

        hvp1  = pct(b1['H'], b1['P'])
        chg1  = pct(b1['C'], b1['P'])
        vr1   = vol_ratio(b1, avg_vol)
        vr0   = vol_ratio(b0, avg_vol)
        low_o = pct(b0['L'], b0['O']) if b0.get('O') and b0.get('L') and b0['O'] > 0 else 0

        if (hvp1 >= CFG2['spike_hvp_min'] and
            chg1 >= CFG2['spike_close_min'] and
            vr1 >= CFG2['spike_vol_min'] and
            vr0 <= CFG2['vol_dry_max'] and
            low_o <= CFG2['low_open_max']):

            sc = 60.0
            sc += min(hvp1, 50) * 0.5
            sc += chg1 * 0.3
            sc += abs(low_o) * 1.5
            sc += (CFG2['vol_dry_max'] - vr0) * 20
            if in_wl: sc += 30

            results.append({
                'code':        code,
                'in_wl':       in_wl,
                'close':       int(b0['C']),
                'chg':         round(pct(b0['C'], b0['P']), 2) if b0.get('P') else 0,
                'vol':         round(vr0, 2),
                'score':       round(sc, 1),
                'spike_date':  b1['date'][5:],
                'spike_hvp':   round(hvp1, 2),
                'spike_close': round(chg1, 2),
                'spike_vol':   round(vr1, 2),
                'low_o':       round(low_o, 2),
            })

    results.sort(key=lambda x: (-int(x['in_wl']), -x['score']))
    return results


def scan_p3(all_ohlcv, avg_vols, target_date):
    """
    P3 Momentum — 2 spike berturut kemudian vol kering.
    
    Signal B: vol kering setelah 2 spike = entry
    Signal spike2_aktif: hari ini adalah spike ke-2
    """
    results = []

    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target_date or len(bars) < 3:
            continue

        avg_vol = avg_vols.get(code, 1.0)
        b0 = bars[-1]
        b1 = bars[-2] if len(bars) >= 2 else None
        b2 = bars[-3] if len(bars) >= 3 else None
        b3 = bars[-4] if len(bars) >= 4 else None
        in_wl = code in ALL_WL

        vr0 = vol_ratio(b0, avg_vol)
        open_vs_prev0 = pct(b0.get('O', 0), b0.get('P', 0)) if b0.get('O') and b0.get('P') else 0
        hvp0 = pct(b0.get('H', 0), b0.get('P', 0)) if b0.get('H') and b0.get('P') else 0

        # === SIGNAL B: vol kering setelah 2 spike (b1=spk2, b2=spk1) ===
        if b1 and b2 and b3:
            hvp1  = pct(b1['H'], b1['P']) if b1.get('H') and b1.get('P') else 0
            open1 = pct(b1.get('O', 0), b1.get('P', 0)) if b1.get('O') and b1.get('P') else 0
            vr1   = vol_ratio(b1, avg_vol)
            c1_b2 = pct(b1['C'], b2['C']) if b2.get('C') else 0
            hvp2  = pct(b2['H'], b2['P']) if b2.get('H') and b2.get('P') else 0
            vr2   = vol_ratio(b2, avg_vol)
            c2_b3 = pct(b2['C'], b3['C']) if b3.get('C') else 0
            open2 = pct(b2.get('O', 0), b2.get('P', 0)) if b2.get('O') and b2.get('P') else 0

            if (hvp2 >= CFG3['spk1_hvp_min'] and c2_b3 > 0 and open2 >= 0 and
                vr2 >= CFG3['spk1_vol_min'] and hvp1 >= CFG3['spk2_hvp_min'] and
                c1_b2 > 0 and open1 >= 1.0 and b1['V'] > b2['V'] and
                vr0 <= CFG3['vol_dry_max']):

                sc = 60.0 + hvp2 * 0.4 + hvp1 * 0.4 + (CFG3['vol_dry_max'] - vr0) * 20
                if in_wl: sc += 30

                results.append({
                    'code':      code,
                    'in_wl':     in_wl,
                    'close':     int(b0['C']),
                    'chg':       round(pct(b0['C'], b0['P']), 2) if b0.get('P') else 0,
                    'hvp':       round(hvp0, 2),
                    'vol':       round(vr0, 2),
                    'score':     round(sc, 1),
                    'spk1_date': b2['date'][5:],
                    'spk1_hvp':  round(hvp2, 2),
                    'spk1_vol':  round(vr2, 2),
                    'spk2_date': b1['date'][5:],
                    'spk2_hvp':  round(hvp1, 2),
                    'spk2_vol':  round(vr1, 2),
                    'trigger':   'vol_kering (Signal B)',
                })
                continue

        # === Spike ke-2 aktif hari ini (b0=spk2, b1=spk1) ===
        if b1 and b2:
            hvp1b  = pct(b1['H'], b1['P']) if b1.get('H') and b1.get('P') else 0
            vr1b   = vol_ratio(b1, avg_vol)
            open1b = pct(b1.get('O', 0), b1.get('P', 0)) if b1.get('O') and b1.get('P') else 0
            c1_b2b = pct(b1['C'], b2['C']) if b2.get('C') else 0
            c0_b1  = pct(b0['C'], b1['C']) if b1.get('C') else 0

            if (hvp1b >= CFG3['spk1_hvp_min'] and c1_b2b > 0 and open1b >= 0 and
                vr1b >= CFG3['spk1_vol_min'] and hvp0 >= CFG3['spk2_hvp_min'] and
                c0_b1 > 0 and open_vs_prev0 >= 1.0 and b0['V'] > b1['V'] and
                not any(r['code'] == code for r in results)):

                sc = 60.0 + hvp1b * 0.4 + hvp0 * 0.4 + min(vr0, 5) * 2
                if in_wl: sc += 30

                results.append({
                    'code':      code,
                    'in_wl':     in_wl,
                    'close':     int(b0['C']),
                    'chg':       round(pct(b0['C'], b0['P']), 2) if b0.get('P') else 0,
                    'hvp':       round(hvp0, 2),
                    'vol':       round(vr0, 2),
                    'score':     round(sc, 1),
                    'spk1_date': b1['date'][5:],
                    'spk1_hvp':  round(hvp1b, 2),
                    'spk1_vol':  round(vr1b, 2),
                    'spk2_date': b0['date'][5:],
                    'spk2_hvp':  round(hvp0, 2),
                    'spk2_vol':  round(vr0, 2),
                    'trigger':   'spike2_aktif (pantau besok vol kering)',
                })

    results.sort(key=lambda x: (-int(x['in_wl']), -x['score']))
    return results
