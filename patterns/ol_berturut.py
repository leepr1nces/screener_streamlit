# patterns/ol_berturut.py — OL Berturut & Alert Reversal & SV & TT
import numpy as np
from utils import is_ol, is_doji, vol_ratio, pct, candle_type
from config import OL_SEQ, SV as CFG_SV, TT as CFG_TT, ALERT as CFG_AL, ALL_WL


def scan_ol_berturut(all_ohlcv, avg_vols, target_date):
    """
    OL Berturut: 2-3 hari kombinasi OL/Doji berturut
    """
    results = []
    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target_date or len(bars) < 2:
            continue
        avg_vol = avg_vols.get(code, 1.0)
        b0 = bars[-1]; b1 = bars[-2] if len(bars) >= 2 else None
        b2 = bars[-3] if len(bars) >= 3 else None
        in_wl = code in ALL_WL
        vr0 = vol_ratio(b0, avg_vol)
        if vr0 == 0: continue

        ct0 = candle_type(b0); ct1 = candle_type(b1); ct2 = candle_type(b2)
        if not ct0 or ct0 not in ('OL', 'OL+Doji', 'Doji'): continue
        if not ct1 or ct1 not in ('OL', 'OL+Doji', 'Doji'): continue

        has_3d = ct2 and ct2 in ('OL', 'OL+Doji', 'Doji')
        seq = f"{ct2}->{ct1}->{ct0}" if has_3d else f"{ct1}->{ct0}"

        sc = 50.0 + (20 if has_3d else 0)
        sc += 20 if vr0 < 0.3 else (10 if vr0 < 0.7 else 0)
        if 'OL' in ct0: sc += 10
        if 'OL' in ct1: sc += 10
        if in_wl: sc += 30

        hvp0 = pct(b0.get('H', 0), b0.get('P', 0)) if b0.get('H') and b0.get('P') else 0
        chg0 = pct(b0['C'], b0.get('P', 0)) if b0.get('P') else 0

        results.append({
            'code': code, 'in_wl': in_wl, 'close': int(b0['C']),
            'chg': round(chg0, 2), 'hvp': round(hvp0, 2), 'vol': round(vr0, 2),
            'seq': seq, 'days': '3H' if has_3d else '2H', 'score': round(sc, 1),
        })

    results.sort(key=lambda x: (-int(x['in_wl']), -x['score']))
    return results


def scan_sv(all_ohlcv, avg_vols, target_date):
    """
    SV Spike Valuasi: Spike H/P >= 7% dengan Value Rp800Jt-5M dalam 10H terakhir
    + max_chg15 <= 13%
    """
    results = []
    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target_date:
            continue
        avg_vol = avg_vols.get(code, 1.0)
        b0 = bars[-1]; in_wl = code in ALL_WL
        vr0 = vol_ratio(b0, avg_vol)

        period15 = bars[-15:]
        max_chg15 = max(
            (pct(b['C'], b['P']) for b in period15 if b.get('P') and b['P'] > 0),
            default=0.0
        )
        if max_chg15 >= CFG_SV['max_chg15']: continue

        period10 = bars[-10:]
        spikes_val = []
        for b in period10:
            if not b.get('H') or not b.get('P') or b['P'] <= 0: continue
            hvp = pct(b['H'], b['P'])
            if hvp >= CFG_SV['spike_hvp_min'] and CFG_SV['val_min'] <= b.get('Val', 0) <= CFG_SV['val_max']:
                spikes_val.append({'date': b['date'][5:], 'hvp': round(hvp, 2),
                                   'val_b': round(b['Val'] / 1e9, 3)})
        if not spikes_val: continue

        best = max(spikes_val, key=lambda x: x['hvp'])
        sc = 50.0 + len(spikes_val) * 15 + min(best['hvp'], 30)
        if is_ol(b0): sc += 12
        if is_doji(b0): sc += 10
        if b0.get('A') and b0['C'] < b0['A']: sc += 8
        if in_wl: sc += 30

        chg0 = pct(b0['C'], b0.get('P', 0)) if b0.get('P') else 0
        results.append({
            'code': code, 'in_wl': in_wl, 'close': int(b0['C']),
            'chg': round(chg0, 2), 'vol': round(vr0, 2), 'score': round(sc, 1),
            'n': len(spikes_val), 'best': best, 'spikes': spikes_val[:3],
            'max_chg15': round(max_chg15, 2),
            'ol': is_ol(b0), 'doji': is_doji(b0),
            'cavg': bool(b0.get('A') and b0['C'] < b0['A']),
        })

    results.sort(key=lambda x: (-int(x['in_wl']), -x['score']))
    return results


def scan_tt(all_ohlcv, avg_vols, target_date):
    """
    TT Time Trading: bar ke-4/5 (IDEAL) setelah spike = zona entry
    """
    results = []
    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target_date or len(bars) < 5:
            continue
        avg_vol = avg_vols.get(code, 1.0)
        b0 = bars[-1]; in_wl = code in ALL_WL
        vr0 = vol_ratio(b0, avg_vol)

        tt_info = None
        for i in range(len(bars) - 2, max(len(bars) - 16, -1), -1):
            bs = bars[i]
            if not all([bs.get('H'), bs.get('P'), bs.get('C')]): continue
            hvp_s = pct(bs['H'], bs['P'])
            if hvp_s < CFG_TT['spike_min']: continue
            bars_after = bars[i + 1:]
            n_after = len(bars_after)
            if n_after < CFG_TT['bar_min'] or n_after > CFG_TT['bar_max']: continue
            lows_after = [b['L'] for b in bars_after if b.get('L')]
            if not lows_after: continue
            lr = (max(lows_after) - min(lows_after)) / min(lows_after) * 100 if min(lows_after) > 0 else 99
            if lr > CFG_TT['low_range_max']: continue
            max_ca = max(
                (pct(b['C'], b['P']) for b in bars_after if b.get('P') and b['P'] > 0),
                default=0.0
            )
            if max_ca >= CFG_TT['max_ca_limit']: continue
            vols_a = [vol_ratio(b, avg_vol) for b in bars_after if b.get('V', 0) > 0]
            if (np.mean(vols_a) if vols_a else 99) > CFG_TT['avg_vol_max']: continue
            ideal = ' IDEAL!' if n_after in CFG_TT['bar_ideal'] else ''
            tt_info = {
                'label': f"TT-bar{n_after}{ideal}",
                'spike_date': bs['date'][5:],
                'spike_hvp': round(hvp_s, 1),
                'n_after': n_after,
                'ideal': n_after in CFG_TT['bar_ideal'],
            }
            break

        if not tt_info: continue

        sc = 50.0 + (20 if tt_info['ideal'] else 0) + (CFG_TT['avg_vol_max'] - vr0) * 10
        if in_wl: sc += 30

        chg0 = pct(b0['C'], b0.get('P', 0)) if b0.get('P') else 0
        hvp0 = pct(b0.get('H', 0), b0.get('P', 0)) if b0.get('H') and b0.get('P') else 0
        results.append({
            'code': code, 'in_wl': in_wl, 'close': int(b0['C']),
            'chg': round(chg0, 2), 'hvp': round(hvp0, 2), 'vol': round(vr0, 2),
            'score': round(sc, 1), 'tt': tt_info,
        })

    results.sort(key=lambda x: (-int(x['in_wl']), -x['score']))
    return results


def scan_alert(all_ohlcv, avg_vols, target_date):
    """
    Alert Reversal: drop >= 8% dalam 5H, med vol <= 0.7x, >= 2 merah
    """
    results = []
    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target_date or len(bars) < 5:
            continue
        avg_vol = avg_vols.get(code, 1.0)
        b0 = bars[-1]; in_wl = code in ALL_WL
        vr0 = vol_ratio(b0, avg_vol)

        last5 = bars[-5:]
        open5 = last5[0].get('O'); close5 = last5[-1]['C']
        if not open5 or open5 == 0: continue

        acc_drop = pct(close5, open5)
        if acc_drop >= CFG_AL['acc_drop_min']: continue

        vols5 = [vol_ratio(b, avg_vol) for b in last5 if b.get('V', 0) > 0]
        med_vol = float(np.median(vols5)) if vols5 else 99
        if med_vol > CFG_AL['med_vol_max']: continue

        red5 = sum(1 for b in last5 if b.get('O') and b['C'] < b['O'])
        if red5 < CFG_AL['min_red']: continue

        spikes_a = [b for b in bars[-15:] if b.get('P') and b['P'] > 0 and b.get('H')
                    and pct(b['H'], b['P']) >= 10]
        n_ol5  = sum(1 for b in last5 if is_ol(b))
        n_dj5  = sum(1 for b in last5 if is_doji(b))

        sc = 50.0 + abs(acc_drop) * 1.5 + (CFG_AL['med_vol_max'] - med_vol) * 40
        sc += red5 * 5 + n_ol5 * 10 + n_dj5 * 8
        if spikes_a: sc += 20
        if in_wl: sc += 30

        spk_str = (f"{spikes_a[-1]['date'][5:]}+{pct(spikes_a[-1]['H'], spikes_a[-1]['P']):.0f}%"
                   if spikes_a else '-')
        chg0 = pct(b0['C'], b0.get('P', 0)) if b0.get('P') else 0
        results.append({
            'code': code, 'in_wl': in_wl, 'close': int(b0['C']),
            'chg': round(chg0, 2), 'vol': round(vr0, 2), 'score': round(sc, 1),
            'acc_drop': round(acc_drop, 2), 'med_vol': round(med_vol, 2),
            'red5': red5, 'ol': n_ol5, 'doji': n_dj5, 'spk': spk_str,
            'vols5': [round(v, 2) for v in vols5],
        })

    results.sort(key=lambda x: (-int(x['in_wl']), -x['score']))
    return results
