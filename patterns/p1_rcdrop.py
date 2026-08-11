# patterns/p1_rcdrop.py — P1 RCDrop1
from utils import vol_ratio
from config import P1 as CFG, ALL_WL


def scan_p1(all_ohlcv, avg_vols, target_date):
    """
    P1 RCDrop1:
    - Spike H/P >= 10% dengan Close >= Prev High (konfirmasi kuat) + volume >= 2x avg
    - Lalu 1-5 hari berikutnya: vol kering < 0.7x avg, maxCA < 8%
    - Signal aktif saat hari vol kering setelah spike

    Return: list of dict
    """
    results = []

    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target_date:
            continue

        avg_vol = avg_vols.get(code, 1.0)
        b0 = bars[-1]
        vr0 = vol_ratio(b0, avg_vol)
        in_wl = code in ALL_WL

        if vr0 >= CFG['vol_dry_max']:
            continue  # Hari ini vol tidak kering

        for lag in range(1, CFG['lag_max'] + 1):
            if len(bars) < lag + 2:
                break

            bs = bars[-(lag + 1)]   # Hari spike
            bp = bars[-(lag + 2)]   # Hari sebelum spike

            if not all([bs.get('H'), bs.get('P'), bs.get('C'), bp.get('H')]):
                continue

            hvp_s = (bs['H'] - bs['P']) / bs['P'] * 100 if bs['P'] > 0 else 0
            if hvp_s < CFG['spike_hvp_min']:
                continue

            # Close spike harus >= High hari sebelumnya (konfirmasi kuat)
            if bs['C'] < bp['H']:
                continue

            vr_s = vol_ratio(bs, avg_vol)
            if vr_s < CFG['spike_vol_min']:
                continue

            # Cek maxCA (max close change) selama periode setelah spike
            days_after = bars[-lag:]
            max_ca = max(
                ((b['C'] - b['P']) / b['P'] * 100 for b in days_after if b.get('P') and b['P'] > 0),
                default=0
            )
            if max_ca >= CFG['max_ca_limit']:
                continue

            # Lolos!
            sc = 60.0
            sc += min(hvp_s, 40) * 0.5
            sc += min(vr_s, 20) * 1.5
            sc += (CFG['vol_dry_max'] - vr0) * 20
            if in_wl: sc += 30

            results.append({
                'code':       code,
                'in_wl':      in_wl,
                'close':      int(b0['C']),
                'chg':        round((b0['C'] - b0['P']) / b0['P'] * 100, 2) if b0.get('P') and b0['P'] > 0 else 0,
                'hvp':        round((b0['H'] - b0['P']) / b0['P'] * 100, 2) if b0.get('H') and b0.get('P') and b0['P'] > 0 else 0,
                'vol':        round(vr0, 2),
                'score':      round(sc, 1),
                'spike_date': bs['date'][5:],
                'spike_hvp':  round(hvp_s, 2),
                'spike_vol':  round(vr_s, 2),
                'lag':        lag,
                'max_ca':     round(max_ca, 2),
            })
            break  # Ambil lag terpendek

    results.sort(key=lambda x: (-int(x['in_wl']), -x['score']))
    return results
