# utils/reporter.py — Format & cetak hasil scan
import os
from datetime import datetime
from config import OUTPUT, ALL_WL
from utils import is_ol, is_doji, vol_ratio, pct, candle_type


def scan_bersih(all_ohlcv, avg_vols, target_date,
                p1_list, p2_list, p3_list, boa_full, boa_near, sv_list, tt_list):
    """
    Scan Bersih: max_chg15 <= 13%, meaningful signals >= 2
    """
    from utils import vol_ratio, is_ol, is_doji, pct, candle_type
    import numpy as np

    results = []
    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target_date or len(bars) < 6:
            continue

        avg_vol = avg_vols.get(code, 1.0)
        b0 = bars[-1]; b1 = bars[-2] if len(bars) >= 2 else None
        in_wl = code in ALL_WL
        vr0 = vol_ratio(b0, avg_vol)

        chg0 = pct(b0['C'], b0.get('P', 0)) if b0.get('P') else 0
        hvp0 = pct(b0.get('H', 0), b0.get('P', 0)) if b0.get('H') and b0.get('P') else 0

        period15 = bars[-15:]
        max_chg15 = max(
            (pct(b['C'], b['P']) for b in period15 if b.get('P') and b['P'] > 0),
            default=0.0
        )
        if max_chg15 > 13: continue

        last5 = bars[-5:]
        n_ol  = sum(1 for b in last5 if is_ol(b))
        n_dj  = sum(1 for b in last5 if is_doji(b))
        n_ca  = sum(1 for b in last5 if b.get('A') and b['C'] < b['A'])
        vols5 = [vol_ratio(b, avg_vol) for b in bars[-5:] if b.get('V', 0) > 0]
        vdown = len(vols5) >= 3 and all(vols5[i] > vols5[i+1] for i in range(min(3, len(vols5)-1)))

        spikes = [b for b in period15 if b.get('H') and b.get('P') and b['P'] > 0
                  and pct(b['H'], b['P']) >= 10]
        n_spike   = len(spikes)
        max_spike = max((pct(b['H'], b['P']) for b in spikes), default=0)

        rej_today = bool(hvp0 >= 5 and chg0 < 10 and b0.get('H') and
                         b0['C'] < b0['H'] * 0.97 and b0.get('A') and b0['C'] < b0['A'])
        inside = bool(b1 and b0.get('H') and b0.get('L') and
                      b0['H'] <= b1['H'] and b0['L'] >= b1['L']) if b1 else False

        ls10    = [b['L'] for b in bars[-10:] if b.get('L')]
        low_rng = (max(ls10) - min(ls10)) / min(ls10) * 100 if ls10 else 99

        has_p1   = any(r['code'] == code for r in p1_list)
        has_p2   = any(r['code'] == code for r in p2_list)
        has_p3   = any(r['code'] == code for r in p3_list)
        has_boa  = any(r['code'] == code for r in boa_full)
        has_near = any(r['code'] == code for r in boa_near)
        has_sv   = any(r['code'] == code for r in sv_list)
        has_tt   = any(r['code'] == code for r in tt_list)

        meaningful = n_spike + (n_ol >= 1) + (n_dj >= 1) + (n_ca >= 1) + vdown + rej_today + inside
        if meaningful < 2: continue

        sc = 50.0 + n_spike*15 + min(max_spike,30)*0.8 + n_ol*12 + n_dj*8 + n_ca*6
        sc += (1 - vr0) * 15 if vr0 < 1 else 0
        sc += vdown*10 + rej_today*12 + inside*15
        sc += (15 - low_rng) if low_rng < 15 else 0
        if has_sv: sc += 10
        if has_tt: sc += 8
        if has_p1: sc += 10
        if has_p2: sc += 15
        if has_p3: sc += 12
        if has_boa: sc += 15
        if has_near: sc += 7
        if in_wl: sc += 30

        ol0    = is_ol(b0); doji0 = is_doji(b0)
        green0 = b0['C'] > (b0.get('O') or 0) if b0.get('O') else False
        tags = [x for x in ['OL' if ol0 else '', 'Doji' if doji0 else '',
                             'CAvg' if n_ca > 0 else '', 'Hijau' if green0 else '',
                             'REJ' if rej_today else '', 'Inside' if inside else ''] if x]
        ex = []
        if vdown: ex.append('Vdown')
        if inside: ex.append('Inside')
        if low_rng < 10: ex.append(f"LR{low_rng:.1f}%")
        if has_sv:  ex.append('SV')
        if has_tt:  ex.append('TT')
        if has_p1:  ex.append('P1')
        if has_p2:  ex.append('P2')
        if has_p3:  ex.append('P3')
        if has_boa: ex.append('BOA!')
        if has_near: ex.append('~BOA')

        results.append({
            'code': code, 'in_wl': in_wl, 'score': round(sc, 1),
            'close': int(b0['C']), 'chg': round(chg0, 2), 'hvp': round(hvp0, 2),
            'vol': round(vr0, 2), 'max_chg15': round(max_chg15, 2),
            'n_spike': n_spike, 'max_spike': round(max_spike, 2),
            'n_ol': n_ol, 'n_dj': n_dj, 'n_ca': n_ca,
            'tags': tags, 'ex': ex,
        })

    results.sort(key=lambda x: (-int(x['in_wl']), -x['score']))
    return results


def print_dashboard(target_date, next_date,
                    clean, boa_full, boa_near, alert_list,
                    ol_seq, p1_list, p2_list, p3_list, sv_list,
                    validation=None):
    """Cetak dashboard lengkap ke terminal"""
    sep = "=" * 72
    print(f"\n{sep}")
    print(f"  DASHBOARD SCREENER IDX | {target_date} | Target: {next_date}")
    print(sep)

    # Validasi
    if validation:
        print(f"\n{'='*72}")
        print("VALIDASI SINYAL KEMARIN")
        print(f"  Naik Close: {validation['naik_c']}/{validation['total']} = {validation['pct_c']:.1f}%")
        print(f"  Naik High : {validation['naik_h']}/{validation['total']} = {validation['pct_h']:.1f}%")
        if validation.get('details'):
            for d in validation['details']:
                icon = '✓' if d['hit_c'] else ('○' if abs(d['chg_c']) < 0.5 else '✗')
                print(f"  {icon} {d['code']:<6} {d['prev']:>6}->{d['close']:>6} H={d['high']:>6} "
                      f"| C={d['chg_c']:+.2f}% H={d['chg_h']:+.1f}%"
                      f"{'🔥' if d['chg_h']>=10 else ''}")

    # Scan Bersih
    wl_c   = [r for r in clean if r['in_wl']]
    nwl_c  = [r for r in clean if not r['in_wl']]
    print(f"\n{'='*72}")
    print(f"SCAN BERSIH <=13% | Total={len(clean)} | WL={len(wl_c)}")
    print(f"{'='*72}")
    print(f"  {'Code':<6} {'C':>6} {'Chg%':>6} {'H/P%':>7} {'Vol':>6} {'mc15':>6} | Spike    OL Dj CA | Extra")
    print("  " + "-" * 70)
    for r in wl_c[:OUTPUT['wl_top_n']]:
        spk = f"{r['n_spike']}s+{r['max_spike']:.0f}%" if r['n_spike'] else "    -  "
        ex  = ' '.join(r['ex'][:5])
        t   = '+'.join(r['tags']) or '-'
        print(f"  ★ {r['code']:<6} {r['close']:>6} {r['chg']:>+6.2f}% {r['hvp']:>+7.2f}% "
              f"{r['vol']:>5.2f}x {r['max_chg15']:>+6.1f}% | {spk:<8} {r['n_ol']:>2} {r['n_dj']:>2} {r['n_ca']:>2} | {ex}")
    if nwl_c:
        print(f"  -- Non-WL top 6 --")
        for r in nwl_c[:6]:
            ex = ' '.join(r['ex'][:4])
            print(f"    {r['code']:<6} {r['close']:>6} {r['chg']:>+6.2f}% {r['hvp']:>+7.2f}% {r['vol']:>5.2f}x | {ex}")

    # BOA
    boa_wl  = [r for r in boa_full if r['in_wl']]
    boa_nwl = [r for r in boa_full if not r['in_wl']]
    near_wl = [r for r in boa_near if r['in_wl']]
    print(f"\nBOA (6/6) WL={len(boa_wl)} | Non-WL={len(boa_nwl)}")
    for r in boa_wl[:OUTPUT['boa_top_n']]:
        spk = ' | '.join(f"{s['date']}+{s['hvp']:.0f}%({s['vr']:.1f}x)" for s in r['spikes'])
        vmark = f"↓{r['v_end']:.2f}x" if r['vdown'] else f"{r['v_end']:.2f}x"
        fails = f" [{','.join(r['fails'])}]" if r['fails'] else ''
        print(f"  ★ {r['code']:<6} [{r['window']}H] C={r['close']:>5} {r['chg']:>+5.2f}% vol={vmark} | "
              f"Rng={r['rng']:.1f}% Dist=+{r['dist_low']:.1f}% | "
              f"OL{r['n_ol']} Dj{r['n_doji']} CA{r['n_cavg']} {r['n_spike']}spk | {spk}{fails}")
    print(f"  Hampir BOA WL={len(near_wl)}")
    for r in near_wl[:12]:
        fails = ','.join(r['fails']) if r['fails'] else ''
        print(f"  ★ {r['code']:<6} [{r['window']}H] Rng={r['rng']:.1f}% Dist=+{r['dist_low']:.1f}% "
              f"OL{r['n_ol']} Dj{r['n_doji']} CA{r['n_cavg']} vol={r['vol']:.2f}x [{fails}]")

    # Alert
    al_wl = [r for r in alert_list if r['in_wl']]
    print(f"\nALERT WL={len(al_wl)}")
    if al_wl:
        for r in al_wl:
            vstr = '->'.join(f"{v:.2f}" for v in r['vols5'])
            print(f"  ★ {r['code']:<6} C={r['close']:>5} | Drop={r['acc_drop']:+.1f}% "
                  f"med={r['med_vol']:.2f}x merah={r['red5']}/5 | {r['spk']} | {vstr}")
    else:
        print("  — tidak ada —")

    # OL Berturut
    ol_wl = [r for r in ol_seq if r['in_wl'] and r['vol'] > 0]
    print(f"\nOL BERTURUT WL={len(ol_wl)}")
    for r in ol_wl:
        print(f"  ★ {r['code']:<6} C={r['close']:>5} {r['chg']:>+.2f}% H/P={r['hvp']:>+.1f}% "
              f"vol={r['vol']:.2f}x | [{r['days']}] {r['seq']}")

    # P1
    p1_wl = [r for r in p1_list if r['in_wl']]
    print(f"\nP1 RCDrop1 WL={len(p1_wl)}")
    for r in p1_wl:
        print(f"  ★ {r['code']:<6} C={r['close']:>5} {r['chg']:>+.2f}% vol={r['vol']:.2f}x | "
              f"{r['spike_date']}(+{r['spike_hvp']:.1f}% vol={r['spike_vol']:.1f}x) "
              f"lag={r['lag']}H maxCA={r['max_ca']:.1f}%")

    # P2
    p2_wl = [r for r in p2_list if r['in_wl']]
    print(f"\nP2 Spike Rebound WL={len(p2_wl)}")
    if p2_wl:
        for r in p2_wl:
            print(f"  ★ {r['code']:<6} {r['chg']:>+.2f}% vol={r['vol']:.2f}x Low/O={r['low_o']:+.1f}% | "
                  f"{r['spike_date']}(+{r['spike_hvp']:.1f}% C+{r['spike_close']:.1f}% vol={r['spike_vol']:.1f}x)")
    else: print("  — tidak ada —")

    # P3
    p3_wl = [r for r in p3_list if r['in_wl']]
    print(f"\nP3 Momentum WL={len(p3_wl)}")
    if p3_wl:
        for r in p3_wl:
            print(f"  ★ {r['code']:<6} C={r['close']:>5} {r['chg']:>+.2f}% vol={r['vol']:.2f}x | "
                  f"Spk1:{r['spk1_date']}(+{r['spk1_hvp']:.0f}%,{r['spk1_vol']:.1f}x) "
                  f"Spk2:{r['spk2_date']}(+{r['spk2_hvp']:.0f}%,{r['spk2_vol']:.1f}x) "
                  f"[{r['trigger']}]")
    else: print("  — tidak ada —")

    # SV
    sv_wl = [r for r in sv_list if r['in_wl']]
    print(f"\nSV WL={len(sv_wl)}")
    for r in sv_wl:
        sig = '+'.join(x for x in ['OL' if r['ol'] else '', 'Doji' if r['doji'] else '',
                                    'CAvg' if r['cavg'] else ''] if x) or '-'
        spk = ', '.join(f"{s['date']}(+{s['hvp']:.0f}%,Rp{s['val_b']:.2f}M)" for s in r['spikes'][:3])
        print(f"  ★ {r['code']:<6} {r['chg']:>+.2f}% mc15={r['max_chg15']:>+.1f}% | "
              f"{r['n']}x: {spk} | {sig}")

    print(f"\n{'='*72}")
    print(f"  Selesai. Target: {next_date}")
    print(f"{'='*72}\n")


def save_output(text, target_date, output_dir='output'):
    """Simpan output ke file .txt"""
    os.makedirs(output_dir, exist_ok=True)
    fname = os.path.join(output_dir, f"{target_date.replace('-','')}_hasil.txt")
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"  >> Disimpan ke: {fname}")
    return fname
