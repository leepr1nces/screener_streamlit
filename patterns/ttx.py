"""
TTx — Time Trading eXtended
Pola siklus spike berulang dengan jarak konsisten.
Spike = High/Prev >8% + Vol > avg Vol 4 hari sebelumnya
Minimal 2 spike (1 jarak) untuk tracking.
Toleransi ±2 hari dari jarak N.
"""
import numpy as np

def scan_ttx(all_ohlcv, avg_vols, target, ALL_WL,
             hvp_thresh=8.0, vol_window=4, gap_min=3, gap_max=15, tol=2):
    def is_spike(bar, prev4):
        if not bar.get('H') or not bar.get('P') or bar['P'] <= 0: return False
        if (bar['H'] - bar['P']) / bar['P'] * 100 <= hvp_thresh: return False
        vols = [b['V'] for b in prev4 if b.get('V', 0) > 0]
        if not vols: return False
        return bar['V'] > np.mean(vols)

    results = []
    for code, bars in all_ohlcv.items():
        if code not in ALL_WL: continue
        if len(bars) < 6: continue

        # Cari semua spike
        spikes = []
        for i in range(vol_window, len(bars)):
            b = bars[i]
            prev4 = bars[i-vol_window:i]
            if is_spike(b, prev4):
                hvp = (b['H'] - b['P']) / b['P'] * 100
                spikes.append({'idx': i, 'date': b['date'][5:], 'hvp': round(hvp, 1)})

        if len(spikes) < 2: continue

        last_idx = len(bars) - 1

        # Ambil pasangan spike terbaru
        for i in range(len(spikes)-1, 0, -1):
            s2 = spikes[i]
            s1 = spikes[i-1]
            gap = s2['idx'] - s1['idx']
            if gap_min <= gap <= gap_max:
                pred_idx = s2['idx'] + gap
                pred_low = pred_idx - tol
                pred_high = pred_idx + tol

                # Cek spike ke-3 sudah terjadi?
                s3 = next((s for s in spikes[i+1:] if pred_low <= s['idx'] <= pred_high), None)

                upcoming = pred_low > last_idx
                reminder = upcoming and (pred_low - last_idx) <= 2

                if pred_idx < len(bars):
                    pred_date = bars[pred_idx]['date'][5:]
                elif pred_idx == last_idx + 1:
                    pred_date = "Besok"
                else:
                    pred_date = f"~{pred_idx - last_idx}H lagi"

                if s3:
                    status = f"✅ Spike3 {s3['date']} +{s3['hvp']}%"
                    priority = 1
                elif reminder:
                    status = f"🔔 REMINDER — prediksi {pred_date}"
                    priority = 0
                elif upcoming:
                    status = f"⏳ Upcoming {pred_date}"
                    priority = 2
                else:
                    status = f"❓ Lewat — prediksi {pred_date}"
                    priority = 3

                today = bars[last_idx]
                chg0 = (today['C'] - today['P']) / today['P'] * 100 if today.get('P') and today['P'] > 0 else 0

                results.append({
                    'code': code, 'in_wl': True,
                    'gap': gap, 'priority': priority,
                    'spk1_date': s1['date'], 'spk1_hvp': s1['hvp'],
                    'spk2_date': s2['date'], 'spk2_hvp': s2['hvp'],
                    's3': s3, 'pred_date': pred_date,
                    'status': status, 'chg': round(chg0, 2),
                    'close': int(today['C']),
                })
                break

    results.sort(key=lambda x: (x['priority'], x['gap']))
    return results
