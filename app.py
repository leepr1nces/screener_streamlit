"""
IDX Screener Dashboard — Hadi Lie
Streamlit Web App — Standalone (semua kode dalam 1 file)
"""

import streamlit as st
import pandas as pd
import numpy as np
import os, sys, re, tempfile
from datetime import datetime, timedelta

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IDX Screener — Hadi Lie",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);
    padding:20px 30px; border-radius:12px; margin-bottom:20px; color:white;
}
.main-header h1 { color:#00d4aa; margin:0; font-size:2rem; }
.main-header p  { color:#aaa; margin:5px 0 0 0; font-size:0.9rem; }
.pos { color:#4ade80; font-weight:bold; }
.neg { color:#f87171; font-weight:bold; }
.neu { color:#94a3b8; }
#MainMenu {visibility:hidden;} footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# WATCHLIST
# ══════════════════════════════════════════════════════════════════════════════
ALL_WL = set([
    'CUAN','ADMG','CDIA','AYLS','GZCO','DOOH','DEWA','FAST','BNBR','KJEN','DATA',
    'GRIA','FIRE','BAJA','BOAT','GTSI','BRMS','CENT','INDX','BUMI','CINT','KAQI','HRTA',
    'KOCI','DPUM','BINO','GRPH','ELIT','ESIP','ASLC','APEX','JKON','HUMI','IMJS','AGRO',
    'GEMA','KBLV','LABA','BELL','KOKA','JAWA','CSIS','KLAS','JAYA','JAST','HOPE','HDIT',
    'GULA','FORE','DSFI','CHEM','CGAS','CARS','BWPT','BSBK','BRRC','BKSL','BAPA','BABY',
    'ATLA','AHAP','AGRS','ADCP','ACRO','BIPI','KOBX','CAKK','DGIK','DOSS','BBRM','BGTG',
    'FOLK','AISA','BVIC','HDFA','KIOS','BATR','IKAN','ERTX','DYAN','ISEA','HALO','GTBO',
    'KRYA','DGNS','CRSN','BAIK','GPRA','GTRA','GSMF','KUAS','DIVA','INOV','DNAR','ENRG',
    'CITY','DFAM','BEER','MSKY','SDMU','WAPO','PTMP','LUCK','OPMS','FWCT','STRK','MBTO',
    'WOWS','MPIX','NETV','OKAS','KPIG','DKHH','SWID','DEFI','TRON','NTBK','NCKL','ENZO',
    'NICL','WIFI','ARTO','MBMA','SSMS','EMTK','FILM','SULI','TINS','TOOL','PSDN','ESTA',
    'RICY','SMLE','HERO','IKAN','BBHI',
])

VAL_MIN = 800_000_000
VAL_MAX = 5_000_000_000

# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════
def safe_float(val):
    try:
        v = float(val)
        return None if v != v else v  # NaN check
    except:
        return None

def pct(a, b):
    if not b or b == 0: return 0.0
    return (a - b) / b * 100

def is_ol(b, tol=0.5):
    if not b or not b.get('O') or not b.get('L') or b['O'] == 0: return False
    return abs(b['O'] - b['L']) / b['O'] * 100 < tol

def is_doji(b, tol=0.8):
    if not b or not b.get('O') or b['O'] == 0: return False
    return abs(b['C'] - (b['O'] or b['C'])) / b['O'] * 100 < tol

def ctype(b):
    if b is None: return None
    ol = is_ol(b); dj = is_doji(b)
    if ol and dj: return 'OL+Doji'
    if ol: return 'OL'
    if dj: return 'Doji'
    return None

def get_avg_vol(bars, exclude=2):
    vols = [b['V'] for b in bars if b['V'] > 0]
    if len(vols) > exclude: vols = vols[:-exclude]
    return float(np.mean(vols)) if vols else 1.0

def vol_ratio(b, avg_vol):
    if not avg_vol or avg_vol == 0: return 0.0
    return b.get('V', 0) / avg_vol

# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADER
# ══════════════════════════════════════════════════════════════════════════════
def load_uploaded(uploaded_files):
    all_ohlcv = {}
    for uf in uploaded_files:
        suffix = '.xlsx' if uf.name.endswith('.xlsx') else '.xls'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uf.read())
            tmp_path = tmp.name
        m = re.search(r'(\d{8})', uf.name)
        if m:
            raw = m.group(1)
            date = f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
        else:
            date = datetime.now().strftime('%Y-%m-%d')
        try:
            try: df = pd.read_excel(tmp_path, sheet_name='Trades')
            except: df = pd.read_excel(tmp_path)
        except Exception as e:
            st.warning(f"Gagal baca {uf.name}: {e}")
            os.unlink(tmp_path)
            continue
        for col in ['Open','High','Low','Close','Avg','Volume','Prev','Value','Last']:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce')
        if 'Close' not in df.columns or df['Close'].isna().all():
            if 'Last' in df.columns: df['Close'] = df['Last']
        elif 'Last' in df.columns:
            df['Close'] = df['Close'].fillna(df['Last'])
        df = df.dropna(subset=['Code','Close'])
        df = df[df['Code'].apply(lambda x: str(x).isalpha() and len(str(x)) <= 6)]
        for _, row in df.iterrows():
            code = str(row['Code'])
            if code not in all_ohlcv: all_ohlcv[code] = []
            all_ohlcv[code].append({
                'date': date,
                'O':   safe_float(row.get('Open')),
                'H':   safe_float(row.get('High')),
                'L':   safe_float(row.get('Low')),
                'C':   float(row['Close']),
                'A':   safe_float(row.get('Avg')),
                'V':   float(row.get('Volume') or 0),
                'P':   safe_float(row.get('Prev')),
                'Val': float(row.get('Value') or 0),
            })
        os.unlink(tmp_path)
    for code in all_ohlcv:
        seen = set(); deduped = []
        for b in sorted(all_ohlcv[code], key=lambda x: x['date']):
            if b['date'] not in seen:
                seen.add(b['date']); deduped.append(b)
        all_ohlcv[code] = deduped
    return all_ohlcv

# ══════════════════════════════════════════════════════════════════════════════
# SCAN FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════
def scan_boa(all_ohlcv, avg_vols, target):
    boa_full = []; boa_near = []
    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target or len(bars) < 6: continue
        avg_vol = avg_vols.get(code, 1.0)
        b0 = bars[-1]; vr0 = vol_ratio(b0, avg_vol); in_wl = code in ALL_WL
        chg0 = pct(b0['C'], b0['P']) if b0.get('P') and b0['P'] > 0 else 0
        hvp0 = pct(b0['H'], b0['P']) if b0.get('H') and b0.get('P') and b0['P'] > 0 else 0
        best = None
        for W in [9,8,7,6]:
            if len(bars) < W: continue
            recent = bars[-W:]
            hs = [b['H'] for b in recent if b.get('H')]
            ls = [b['L'] for b in recent if b.get('L')]
            if not hs or not ls: continue
            h_max = max(hs); l_min = min(ls)
            if l_min == 0: continue
            rng  = (h_max - l_min) / l_min * 100
            dist = (b0['C'] - l_min) / l_min * 100
            spk  = [b for b in recent if b.get('H') and b.get('P') and b['P'] > 0
                    and pct(b['H'], b['P']) >= 7]
            n_ol  = sum(1 for b in recent if is_ol(b))
            n_dj  = sum(1 for b in recent if is_doji(b))
            n_ca  = sum(1 for b in recent if b.get('A') and b['C'] < b['A'])
            vols_w = [vol_ratio(b, avg_vol) for b in recent if b.get('V', 0) > 0]
            v_end = vols_w[-1] if vols_w else 0
            v_start = vols_w[0] if vols_w else 0
            c1=rng<=25; c2=len(spk)>0; c3=vr0<0.7
            c4=(n_ol+n_dj)>=3; c5=dist<15; c6=n_ca>=3
            passed = sum([c1,c2,c3,c4,c5,c6])
            sc = 50.0 + (25-rng)*1.5 if c1 else 50.0
            sc += (15-dist)*1.0 if c5 else 0
            sc += (0.7-vr0)*20 if c3 else 0
            sc += (n_ol+n_dj)*5 + n_ca*3
            if spk: sc += len(spk)*10 + max(pct(b['H'],b['P']) for b in spk)*0.5
            if v_end < v_start: sc += (v_start-v_end)*5
            if in_wl: sc += 30
            fails = []
            if not c1: fails.append(f"Range{rng:.1f}%")
            if not c2: fails.append("NoSpike")
            if not c3: fails.append(f"Vol{vr0:.2f}x")
            if not c4: fails.append(f"OL+Dj={n_ol+n_dj}")
            if not c5: fails.append(f"Dist+{dist:.1f}%")
            if not c6: fails.append(f"CAvg={n_ca}")
            spk_info = [{'date':b['date'][5:],'hvp':round(pct(b['H'],b['P']),1),'vr':round(vol_ratio(b,avg_vol),2)} for b in spk[:3]]
            entry = {'code':code,'in_wl':in_wl,'close':int(b0['C']),'chg':round(chg0,2),
                     'hvp':round(hvp0,2),'vol':round(vr0,2),'score':round(sc,1),'window':W,
                     'rng':round(rng,1),'dist_low':round(dist,1),'n_ol':n_ol,'n_doji':n_dj,
                     'n_cavg':n_ca,'n_spike':len(spk),
                     'max_spike':round(max(pct(b['H'],b['P']) for b in spk),1) if spk else 0,
                     'vdown':v_end<v_start,'v_end':round(v_end,2),
                     'spikes':spk_info,'passed':passed,'fails':fails}
            if best is None or passed > best['passed'] or (passed == best['passed'] and sc > best['score']):
                best = entry
        if best:
            if best['passed'] == 6: boa_full.append(best)
            elif best['passed'] >= 4: boa_near.append(best)
    boa_full.sort(key=lambda x: (-int(x['in_wl']), -x['score']))
    boa_near.sort(key=lambda x: (-int(x['in_wl']), -x['score']))
    return boa_full, boa_near


def scan_p1(all_ohlcv, avg_vols, target):
    results = []
    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target or len(bars) < 4: continue
        avg_vol = avg_vols.get(code, 1.0)
        b0 = bars[-1]; vr0 = vol_ratio(b0, avg_vol); in_wl = code in ALL_WL
        if vr0 >= 0.7: continue
        for lag in range(1, 6):
            if len(bars) < lag+2: break
            bs = bars[-(lag+1)]; bp = bars[-(lag+2)]
            if not all([bs.get('H'),bs.get('P'),bs.get('C'),bp.get('H')]): continue
            hvp_s = pct(bs['H'], bs['P']) if bs['P'] > 0 else 0
            if hvp_s < 10: continue
            if bs['C'] < bp['H']: continue
            vr_s = vol_ratio(bs, avg_vol)
            if vr_s < 2.0: continue
            days_after = bars[-lag:]
            max_ca = max((pct(b['C'],b['P']) for b in days_after if b.get('P') and b['P']>0), default=0)
            if max_ca >= 8: continue
            sc = 60.0 + min(hvp_s,40)*0.5 + min(vr_s,20)*1.5 + (0.7-vr0)*20
            if in_wl: sc += 30
            chg0 = pct(b0['C'],b0['P']) if b0.get('P') and b0['P']>0 else 0
            hvp0 = pct(b0['H'],b0['P']) if b0.get('H') and b0.get('P') and b0['P']>0 else 0
            results.append({'code':code,'in_wl':in_wl,'close':int(b0['C']),'chg':round(chg0,2),
                'hvp':round(hvp0,2),'vol':round(vr0,2),'score':round(sc,1),
                'spike_date':bs['date'][5:],'spike_hvp':round(hvp_s,2),'spike_vol':round(vr_s,2),
                'lag':lag,'max_ca':round(max_ca,2)})
            break
    results.sort(key=lambda x: (-int(x['in_wl']), -x['score']))
    return results


def scan_p3(all_ohlcv, avg_vols, target):
    results = []
    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target or len(bars) < 4: continue
        avg_vol = avg_vols.get(code, 1.0)
        b0=bars[-1]; b1=bars[-2] if len(bars)>=2 else None
        b2=bars[-3] if len(bars)>=3 else None; b3=bars[-4] if len(bars)>=4 else None
        in_wl = code in ALL_WL
        vr0 = vol_ratio(b0, avg_vol)
        chg0 = pct(b0['C'],b0['P']) if b0.get('P') and b0['P']>0 else 0
        hvp0 = pct(b0['H'],b0['P']) if b0.get('H') and b0.get('P') and b0['P']>0 else 0
        opv0 = pct(b0['O'],b0['P']) if b0.get('O') and b0.get('P') and b0['P']>0 else 0
        # Signal B
        if b1 and b2 and b3:
            hvp1=pct(b1['H'],b1['P']) if b1.get('H') and b1.get('P') else 0
            open1=pct(b1['O'],b1['P']) if b1.get('O') and b1.get('P') else 0
            vr1=vol_ratio(b1,avg_vol)
            c1b2=pct(b1['C'],b2['C']) if b2.get('C') and b2['C']>0 else 0
            hvp2=pct(b2['H'],b2['P']) if b2.get('H') and b2.get('P') else 0
            vr2=vol_ratio(b2,avg_vol)
            c2b3=pct(b2['C'],b3['C']) if b3.get('C') and b3['C']>0 else 0
            open2=pct(b2['O'],b2['P']) if b2.get('O') and b2.get('P') else 0
            if (hvp2>=10 and c2b3>0 and open2>=0 and vr2>=1.5 and hvp1>=7
                and c1b2>0 and open1>=1.0 and b1['V']>b2['V'] and vr0<=0.5):
                sc = 60.0+hvp2*0.4+hvp1*0.4+(0.5-vr0)*20
                if in_wl: sc+=30
                results.append({'code':code,'in_wl':in_wl,'close':int(b0['C']),'chg':round(chg0,2),
                    'hvp':round(hvp0,2),'vol':round(vr0,2),'score':round(sc,1),
                    'spk1_date':b2['date'][5:],'spk1_hvp':round(hvp2,2),'spk1_vol':round(vr2,2),
                    'spk2_date':b1['date'][5:],'spk2_hvp':round(hvp1,2),'spk2_vol':round(vr1,2),
                    'trigger':'Signal B ✅'})
                continue
        # Spike2 aktif
        if b1 and b2:
            hvp1b=pct(b1['H'],b1['P']) if b1.get('H') and b1.get('P') else 0
            vr1b=vol_ratio(b1,avg_vol)
            open1b=pct(b1['O'],b1['P']) if b1.get('O') and b1.get('P') else 0
            c1b2b=pct(b1['C'],b2['C']) if b2.get('C') and b2['C']>0 else 0
            c0b1=pct(b0['C'],b1['C']) if b1.get('C') and b1['C']>0 else 0
            if (hvp1b>=10 and c1b2b>0 and open1b>=0 and vr1b>=1.5 and hvp0>=7
                and c0b1>0 and opv0>=1.0 and b0['V']>b1['V']
                and not any(r['code']==code for r in results)):
                sc = 60.0+hvp1b*0.4+hvp0*0.4+min(vr0,5)*2
                if in_wl: sc+=30
                results.append({'code':code,'in_wl':in_wl,'close':int(b0['C']),'chg':round(chg0,2),
                    'hvp':round(hvp0,2),'vol':round(vr0,2),'score':round(sc,1),
                    'spk1_date':b1['date'][5:],'spk1_hvp':round(hvp1b,2),'spk1_vol':round(vr1b,2),
                    'spk2_date':b0['date'][5:],'spk2_hvp':round(hvp0,2),'spk2_vol':round(vr0,2),
                    'trigger':'Spike2 Aktif 👀'})
    results.sort(key=lambda x: (-int(x['in_wl']), -x['score']))
    return results


def scan_ol_seq(all_ohlcv, avg_vols, target):
    results = []
    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target or len(bars) < 2: continue
        avg_vol = avg_vols.get(code, 1.0)
        b0=bars[-1]; b1=bars[-2] if len(bars)>=2 else None
        b2=bars[-3] if len(bars)>=3 else None
        in_wl = code in ALL_WL
        vr0 = vol_ratio(b0, avg_vol)
        if vr0 == 0: continue
        ct0=ctype(b0); ct1=ctype(b1); ct2=ctype(b2)
        if not ct0 or ct0 not in ('OL','OL+Doji','Doji'): continue
        if not ct1 or ct1 not in ('OL','OL+Doji','Doji'): continue
        has_3d = ct2 and ct2 in ('OL','OL+Doji','Doji')
        seq = f"{ct2}->{ct1}->{ct0}" if has_3d else f"{ct1}->{ct0}"
        sc = 50.0+(20 if has_3d else 0)+(20 if vr0<0.3 else (10 if vr0<0.7 else 0))
        if 'OL' in ct0: sc+=10
        if 'OL' in ct1: sc+=10
        if in_wl: sc+=30
        chg0 = pct(b0['C'],b0['P']) if b0.get('P') and b0['P']>0 else 0
        hvp0 = pct(b0['H'],b0['P']) if b0.get('H') and b0.get('P') and b0['P']>0 else 0
        results.append({'code':code,'in_wl':in_wl,'close':int(b0['C']),'chg':round(chg0,2),
            'hvp':round(hvp0,2),'vol':round(vr0,2),'seq':seq,
            'days':'3H' if has_3d else '2H','score':round(sc,1)})
    results.sort(key=lambda x: (-int(x['in_wl']), -x['score']))
    return results


def scan_sv(all_ohlcv, avg_vols, target):
    results = []
    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target: continue
        avg_vol = avg_vols.get(code, 1.0)
        b0=bars[-1]; in_wl=code in ALL_WL; vr0=vol_ratio(b0,avg_vol)
        period15=bars[-15:]
        max_chg15=max((pct(b['C'],b['P']) for b in period15 if b.get('P') and b['P']>0),default=0.0)
        if max_chg15>=13: continue
        period10=bars[-10:]; spikes_val=[]
        for b in period10:
            if not b.get('H') or not b.get('P') or b['P']<=0: continue
            hvp=pct(b['H'],b['P'])
            if hvp>=7 and VAL_MIN<=b.get('Val',0)<=VAL_MAX:
                spikes_val.append({'date':b['date'][5:],'hvp':round(hvp,2),'val_b':round(b['Val']/1e9,3)})
        if not spikes_val: continue
        best=max(spikes_val,key=lambda x:x['hvp'])
        sc=50.0+len(spikes_val)*15+min(best['hvp'],30)
        if is_ol(b0): sc+=12
        if is_doji(b0): sc+=10
        if b0.get('A') and b0['C']<b0['A']: sc+=8
        if in_wl: sc+=30
        chg0=pct(b0['C'],b0['P']) if b0.get('P') and b0['P']>0 else 0
        results.append({'code':code,'in_wl':in_wl,'close':int(b0['C']),'chg':round(chg0,2),
            'vol':round(vr0,2),'score':round(sc,1),'n':len(spikes_val),
            'best':best,'spikes':spikes_val[:3],'max_chg15':round(max_chg15,2),
            'ol':is_ol(b0),'doji':is_doji(b0),'cavg':bool(b0.get('A') and b0['C']<b0['A'])})
    results.sort(key=lambda x: (-int(x['in_wl']), -x['score']))
    return results


def scan_alert(all_ohlcv, avg_vols, target):
    results = []
    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target or len(bars) < 5: continue
        avg_vol = avg_vols.get(code, 1.0)
        b0=bars[-1]; in_wl=code in ALL_WL; vr0=vol_ratio(b0,avg_vol)
        last5=bars[-5:]; open5=last5[0].get('O'); close5=last5[-1]['C']
        if not open5 or open5==0: continue
        acc_drop=pct(close5,open5)
        if acc_drop>=-8: continue
        vols5=[vol_ratio(b,avg_vol) for b in last5 if b.get('V',0)>0]
        med_vol=float(np.median(vols5)) if vols5 else 99
        if med_vol>0.7: continue
        red5=sum(1 for b in last5 if b.get('O') and b['C']<b['O'])
        if red5<2: continue
        spk_a=[b for b in bars[-15:] if b.get('P') and b['P']>0 and b.get('H') and pct(b['H'],b['P'])>=10]
        sc=50.0+abs(acc_drop)*1.5+(0.7-med_vol)*40+red5*5
        if spk_a: sc+=20
        if in_wl: sc+=30
        spk_str=f"{spk_a[-1]['date'][5:]}+{pct(spk_a[-1]['H'],spk_a[-1]['P']):.0f}%" if spk_a else '-'
        chg0=pct(b0['C'],b0['P']) if b0.get('P') and b0['P']>0 else 0
        results.append({'code':code,'in_wl':in_wl,'close':int(b0['C']),'chg':round(chg0,2),
            'vol':round(vr0,2),'score':round(sc,1),'acc_drop':round(acc_drop,2),
            'med_vol':round(med_vol,2),'red5':red5,'spk':spk_str})
    results.sort(key=lambda x: (-int(x['in_wl']), -x['score']))
    return results


def scan_bersih(all_ohlcv, avg_vols, target, p1_list, p3_list, boa_full, boa_near, sv_list):
    results = []
    p1_codes  = {r['code'] for r in p1_list}
    p3_codes  = {r['code'] for r in p3_list}
    boa_codes = {r['code'] for r in boa_full}
    near_codes= {r['code'] for r in boa_near}
    sv_codes  = {r['code'] for r in sv_list}

    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target or len(bars) < 6: continue
        avg_vol = avg_vols.get(code, 1.0)
        b0=bars[-1]; b1=bars[-2] if len(bars)>=2 else None
        in_wl=code in ALL_WL; vr0=vol_ratio(b0,avg_vol)
        chg0=pct(b0['C'],b0['P']) if b0.get('P') and b0['P']>0 else 0
        hvp0=pct(b0['H'],b0['P']) if b0.get('H') and b0.get('P') and b0['P']>0 else 0
        period15=bars[-15:]
        max_chg15=max((pct(b['C'],b['P']) for b in period15 if b.get('P') and b['P']>0),default=0.0)
        if max_chg15>13: continue
        last5=bars[-5:]
        n_ol=sum(1 for b in last5 if is_ol(b))
        n_dj=sum(1 for b in last5 if is_doji(b))
        n_ca=sum(1 for b in last5 if b.get('A') and b['C']<b['A'])
        vols5=[vol_ratio(b,avg_vol) for b in bars[-5:] if b.get('V',0)>0]
        vdown=len(vols5)>=3 and all(vols5[i]>vols5[i+1] for i in range(min(3,len(vols5)-1)))
        spikes=[b for b in period15 if b.get('H') and b.get('P') and b['P']>0 and pct(b['H'],b['P'])>=10]
        n_spike=len(spikes)
        max_spike=max((pct(b['H'],b['P']) for b in spikes),default=0)
        rej=bool(hvp0>=5 and chg0<10 and b0.get('H') and b0['C']<b0['H']*0.97 and b0.get('A') and b0['C']<b0['A'])
        inside=bool(b1 and b0.get('H') and b0.get('L') and b0['H']<=b1['H'] and b0['L']>=b1['L']) if b1 else False
        ls10=[b['L'] for b in bars[-10:] if b.get('L')]
        low_rng=(max(ls10)-min(ls10))/min(ls10)*100 if ls10 else 99
        meaningful=n_spike+(n_ol>=1)+(n_dj>=1)+(n_ca>=1)+vdown+rej+inside
        if meaningful<2: continue
        sc=50.0+n_spike*15+min(max_spike,30)*0.8+n_ol*12+n_dj*8+n_ca*6
        sc+=(1-vr0)*15 if vr0<1 else 0
        sc+=vdown*10+rej*12+inside*15
        sc+=(15-low_rng) if low_rng<15 else 0
        if code in sv_codes:  sc+=10
        if code in p1_codes:  sc+=10
        if code in p3_codes:  sc+=12
        if code in boa_codes: sc+=15
        if code in near_codes:sc+=7
        if in_wl: sc+=30
        ex=[]
        if code in boa_codes:  ex.append('BOA!')
        if code in near_codes: ex.append('~BOA')
        if code in p1_codes:   ex.append('P1')
        if code in p3_codes:   ex.append('P3')
        if code in sv_codes:   ex.append('SV')
        if vdown: ex.append('Vdown')
        if inside: ex.append('Inside')
        if low_rng<10: ex.append(f"LR{low_rng:.1f}%")
        ol0=is_ol(b0); dj0=is_doji(b0); gr0=b0['C']>(b0.get('O') or 0) if b0.get('O') else False
        tags=[x for x in ['OL' if ol0 else '','Doji' if dj0 else '','CAvg' if n_ca>0 else '',
                           'Hijau' if gr0 else ''] if x]
        results.append({'code':code,'in_wl':in_wl,'score':round(sc,1),
            'close':int(b0['C']),'chg':round(chg0,2),'hvp':round(hvp0,2),
            'vol':round(vr0,2),'max_chg15':round(max_chg15,2),
            'n_spike':n_spike,'max_spike':round(max_spike,2),
            'n_ol':n_ol,'n_dj':n_dj,'n_ca':n_ca,'tags':tags,'ex':ex})
    results.sort(key=lambda x: (-int(x['in_wl']), -x['score']))
    return results

# ══════════════════════════════════════════════════════════════════════════════
# DATAFRAME HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def style_chg(df, cols):
    def f(v):
        if isinstance(v,(int,float)):
            if v>0: return 'color:#4ade80;font-weight:bold'
            if v<0: return 'color:#f87171;font-weight:bold'
        return ''
    return df.style.map(f, subset=cols)

def style_vol(df, col='Vol'):
    def f(v):
        if isinstance(v,(int,float)):
            if v<0.3: return 'color:#4ade80;font-weight:bold'
            if v<0.7: return 'color:#fbbf24'
        return ''
    return df.style.map(f, subset=[col])

# ══════════════════════════════════════════════════════════════════════════════
# STOCKPICK BUY CLOSE
# ══════════════════════════════════════════════════════════════════════════════
def scan_stockpick(all_ohlcv, avg_vols, target,
                   max_hvp=7.0, min_chg=0.0, max_chg=5.0,
                   lookback=7, max_c7=7.0):
    results = []
    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target or len(bars) < 3:
            continue
        b0 = bars[-1]
        b1 = bars[-2] if len(bars) >= 2 else None
        in_wl = code in ALL_WL
        if not b0.get('P') or b0['P'] <= 0:
            continue
        hvp0 = pct(b0['H'], b0['P']) if b0.get('H') else 0
        chg0 = pct(b0['C'], b0['P'])
        v0   = b0.get('V', 0)
        v1   = b1.get('V', 0) if b1 else 0
        avg_vol = avg_vols.get(code, 1.0)
        vr0  = v0 / avg_vol if avg_vol > 0 else 0
        # Kriteria 1: H/P <= max_hvp
        if hvp0 > max_hvp:
            continue
        # Kriteria 2: Close/Prev antara min_chg dan max_chg
        if chg0 < min_chg or chg0 > max_chg:
            continue
        # Kriteria 3: Volume hari ini > kemarin
        if v1 <= 0 or v0 <= v1:
            continue
        # Kriteria 4: 7H ke belakang tidak ada close >= max_c7
        period7 = bars[-lookback-1:-1]
        spike7  = any(b.get('P') and b['P'] > 0 and pct(b['C'], b['P']) >= max_c7
                      for b in period7)
        if spike7:
            continue
        sc = 50.0 + vr0*10 + chg0*5 + (max_hvp - hvp0)
        if in_wl: sc += 30
        vp = v0/v1 if v1 > 0 else 0
        max_c7h = max((pct(b['C'],b['P']) for b in period7 if b.get('P') and b['P']>0), default=0.0)
        green = b0['C'] > (b0.get('O') or b0['C'])
        ol  = bool(b0.get('O') and b0.get('L') and b0['O']>0 and abs(b0['O']-b0['L'])/b0['O']*100 < 0.5)
        doji= bool(b0.get('O') and b0['O']>0 and abs(b0['C']-b0['O'])/b0['O']*100 < 0.8)
        candle = ('OL+Doji' if ol and doji else 'OL' if ol else
                  'Doji'    if doji else 'Hijau' if green else 'Merah')
        results.append({
            'code': code, 'in_wl': in_wl, 'close': int(b0['C']),
            'chg': round(chg0,2), 'hvp': round(hvp0,2),
            'vol': round(vr0,2), 'vol_vs_prev': round(vp,2),
            'score': round(sc,1), 'max_chg7': round(max_c7h,2),
            'candle': candle,
        })
    results.sort(key=lambda x: (-int(x['in_wl']), -x['score']))
    return results


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
def main():
    now = datetime.now()

    st.markdown("""
    <div class="main-header">
        <h1>📈 IDX Screener</h1>
        <p>Sistem Pola Candlestick Proprietary | Hadi Lie</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚙️ Konfigurasi")
        uploaded_files = st.file_uploader(
            "📂 Upload File XLS dari RTI",
            type=['xls','xlsx'],
            accept_multiple_files=True,
            help="Bisa upload banyak file sekaligus"
        )
        st.divider()
        show_only_wl = st.toggle("★ Hanya WL", value=True)
        st.divider()
        st.markdown("**Pola:**")
        col1,col2 = st.columns(2)
        show_boa   = col1.checkbox("BOA",    value=True)
        show_p1    = col2.checkbox("P1",     value=True)
        show_p3    = col1.checkbox("P3",     value=True)
        show_ol    = col2.checkbox("OLseq",  value=True)
        show_sv    = col1.checkbox("SV",     value=True)
        show_alert = col2.checkbox("Alert",  value=True)
        show_clean = st.checkbox("Scan Bersih", value=True)
        st.divider()
        st.caption(f"🕐 {now.strftime('%d %b %Y %H:%M')}")

    # ── Welcome ───────────────────────────────────────────────────────────────
    if not uploaded_files:
        c1,c2,c3 = st.columns([1,2,1])
        with c2:
            st.markdown("""
            <div style="text-align:center;padding:60px 20px;">
                <div style="font-size:5rem;">📂</div>
                <h2 style="color:#00d4aa;">Upload File XLS untuk Mulai</h2>
                <p style="color:#aaa;">Taruh file <b>.xls</b> dari RTI Screener<br>
                di panel kiri — bisa banyak file sekaligus</p>
            </div>
            """, unsafe_allow_html=True)
            st.info("**Cara pakai:**\n1. Klik Browse files di sidebar\n2. Pilih file .xls dari RTI\n3. Hasil scan muncul otomatis")
        return

    # ── Process ───────────────────────────────────────────────────────────────
    with st.spinner("🔄 Memproses & scan semua pola..."):
        all_ohlcv = load_uploaded(uploaded_files)
        if not all_ohlcv:
            st.error("Tidak ada data yang terbaca. Cek format file."); return

        dates = []
        for bars in all_ohlcv.values():
            if bars: dates.append(bars[-1]['date'])
        target = max(dates) if dates else None
        if not target:
            st.error("Tidak bisa baca tanggal."); return

        avg_vols = {code: get_avg_vol(bars) for code,bars in all_ohlcv.items()}
        data_today = {c:b for c,b in all_ohlcv.items() if b and b[-1]['date']==target}

        dt = datetime.strptime(target,'%Y-%m-%d')
        delta = 3 if dt.weekday()==4 else 1
        next_date = (dt+timedelta(days=delta)).strftime('%Y-%m-%d')

        boa_full, boa_near = scan_boa(all_ohlcv, avg_vols, target)
        p1_list   = scan_p1(all_ohlcv, avg_vols, target)
        p3_list   = scan_p3(all_ohlcv, avg_vols, target)
        ol_list   = scan_ol_seq(all_ohlcv, avg_vols, target)
        sv_list   = scan_sv(all_ohlcv, avg_vols, target)
        alert_list= scan_alert(all_ohlcv, avg_vols, target)
        clean     = scan_bersih(all_ohlcv, avg_vols, target,
                                p1_list, p3_list, boa_full, boa_near, sv_list)
        # Stockpick — ambil parameter dari session state
        sp_hvp  = st.session_state.get('sp_hvp',  7.0)
        sp_min  = st.session_state.get('sp_min',  0.0)
        sp_max  = st.session_state.get('sp_max',  5.0)
        sp_list = scan_stockpick(all_ohlcv, avg_vols, target,
                                 max_hvp=sp_hvp, min_chg=sp_min, max_chg=sp_max)

    # ── Info bar ──────────────────────────────────────────────────────────────
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("📅 Data",   target)
    c2.metric("🎯 Target", next_date)
    c3.metric("📊 File",   f"{len(uploaded_files)} file")
    c4.metric("🏢 Saham",  f"{len(data_today)} saham")

    # ── Summary chips ─────────────────────────────────────────────────────────
    cols = st.columns(9)
    chips = [
        ("BOA ✅",    len([r for r in boa_full   if r['in_wl']]), "#60a5fa"),
        ("~BOA",     len([r for r in boa_near   if r['in_wl']]), "#93c5fd"),
        ("P1",       len([r for r in p1_list    if r['in_wl']]), "#f472b6"),
        ("P3",       len([r for r in p3_list    if r['in_wl']]), "#fbbf24"),
        ("OLseq",    len([r for r in ol_list    if r['in_wl']]), "#fb923c"),
        ("SV",       len([r for r in sv_list    if r['in_wl']]), "#2dd4bf"),
        ("Alert",    len([r for r in alert_list  if r['in_wl']]), "#f87171"),
        ("Bersih",   len([r for r in clean      if r['in_wl']]), "#4ade80"),
        ("Stockpick",len([r for r in sp_list    if r['in_wl']]), "#a78bfa"),
    ]
    for col,(label,val,color) in zip(cols,chips):
        col.markdown(f"""<div style="background:#1e1e2e;border:1px solid #333;border-radius:8px;
            padding:10px;text-align:center;">
            <div style="font-size:1.5rem;font-weight:bold;color:{color};">{val}</div>
            <div style="font-size:0.72rem;color:#aaa;">{label}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_labels = ["🧹 Scan Bersih","🎯 BOA","📉 P1","🔄 P3","🕯️ OLseq","💰 SV","🚨 Alert","🛒 Stockpick"]
    tabs = st.tabs(tab_labels)

    # Tab Scan Bersih
    with tabs[0]:
        lst = [r for r in clean if r['in_wl']] if show_only_wl else clean
        st.markdown(f"**Scan Bersih ≤13% | WL: {len([r for r in clean if r['in_wl']])} | Total: {len(clean)}**")
        if lst:
            rows = [{'★':('★' if r['in_wl'] else ''),'Code':r['code'],'Close':r['close'],
                'Chg%':r['chg'],'H/P%':r['hvp'],'Vol':r['vol'],'mc15%':r['max_chg15'],
                'Spike':(f"{r['n_spike']}x+{r['max_spike']:.0f}%" if r['n_spike'] else '-'),
                'OL':r['n_ol'],'Dj':r['n_dj'],'CA':r['n_ca'],
                'Signal':' '.join(r['ex'][:4]),'Candle':'+'.join(r['tags']) or '-'} for r in lst]
            df = pd.DataFrame(rows)
            st.dataframe(df.style
                .map(lambda v:'color:#4ade80;font-weight:bold' if isinstance(v,float) and v>0
                          else ('color:#f87171;font-weight:bold' if isinstance(v,float) and v<0 else ''),
                          subset=['Chg%','H/P%'])
                .map(lambda v:'color:#4ade80' if isinstance(v,float) and v<0.3
                          else ('color:#fbbf24' if isinstance(v,float) and v<0.7 else ''), subset=['Vol'])
                .format({'Chg%':'{:+.2f}','H/P%':'{:+.2f}','Vol':'{:.2f}','mc15%':'{:+.1f}'}),
                use_container_width=True, height=520)
        else:
            st.info("Tidak ada hasil.")

    # Tab BOA
    with tabs[1]:
        boa_wl  = [r for r in boa_full if r['in_wl']]
        near_wl = [r for r in boa_near if r['in_wl']]
        ca, cb  = st.columns(2)
        with ca:
            lst = boa_wl if show_only_wl else boa_full
            st.markdown(f"**BOA 6/6 | WL: {len(boa_wl)} | Total: {len(boa_full)}**")
            if lst:
                rows = [{'★':('★' if r['in_wl'] else ''),'Code':r['code'],'Close':r['close'],
                    'Chg%':r['chg'],'Vol':r['vol'],'Rng%':r['rng'],'Dist%':r['dist_low'],
                    'OL+Dj':r['n_ol']+r['n_doji'],'CAvg':r['n_cavg'],
                    'Spikes':' | '.join(f"{s['date']}+{s['hvp']:.0f}%" for s in r['spikes'])
                    } for r in lst]
                df=pd.DataFrame(rows)
                st.dataframe(df.style
                    .map(lambda v:'color:#4ade80;font-weight:bold' if isinstance(v,float) and v>0
                              else ('color:#f87171;font-weight:bold' if isinstance(v,float) and v<0 else ''),
                              subset=['Chg%'])
                    .map(lambda v:'color:#4ade80' if isinstance(v,float) and v<0.3
                              else ('color:#fbbf24' if isinstance(v,float) and v<0.7 else ''),subset=['Vol'])
                    .format({'Chg%':'{:+.2f}','Vol':'{:.2f}','Rng%':'{:.1f}','Dist%':'{:.1f}'}),
                    use_container_width=True, height=420)
            else: st.info("Tidak ada BOA.")
        with cb:
            lst2 = near_wl if show_only_wl else boa_near
            st.markdown(f"**Hampir BOA 4-5/6 | WL: {len(near_wl)}**")
            if lst2:
                rows=[{'★':('★' if r['in_wl'] else ''),'Code':r['code'],'Close':r['close'],
                    'Vol':r['vol'],'Rng%':r['rng'],'Dist%':r['dist_low'],
                    'OL+Dj':r['n_ol']+r['n_doji'],'CAvg':r['n_cavg'],
                    'Missing':','.join(r['fails'][:2])} for r in lst2]
                df=pd.DataFrame(rows)
                st.dataframe(df.style
                    .map(lambda v:'color:#4ade80' if isinstance(v,float) and v<0.3
                              else ('color:#fbbf24' if isinstance(v,float) and v<0.7 else ''),subset=['Vol'])
                    .format({'Vol':'{:.2f}','Rng%':'{:.1f}','Dist%':'{:.1f}'}),
                    use_container_width=True, height=420)
            else: st.info("Tidak ada Hampir BOA.")

    # Tab P1
    with tabs[2]:
        lst = [r for r in p1_list if r['in_wl']] if show_only_wl else p1_list
        st.markdown(f"**P1 RCDrop1 | WL: {len([r for r in p1_list if r['in_wl']])} | Total: {len(p1_list)}**")
        if lst:
            rows=[{'★':('★' if r['in_wl'] else ''),'Code':r['code'],'Close':r['close'],
                'Chg%':r['chg'],'Vol':r['vol'],'Spike Date':r['spike_date'],
                'Spk H/P%':r['spike_hvp'],'Spk Vol':r['spike_vol'],
                'Lag (H)':r['lag'],'maxCA%':r['max_ca']} for r in lst]
            df=pd.DataFrame(rows)
            st.dataframe(df.style
                .map(lambda v:'color:#4ade80;font-weight:bold' if isinstance(v,float) and v<=0
                          else ('color:#f87171' if isinstance(v,float) and v>0 else ''),subset=['maxCA%'])
                .map(lambda v:'color:#4ade80' if isinstance(v,float) and v<0.3
                          else ('color:#fbbf24' if isinstance(v,float) and v<0.7 else ''),subset=['Vol'])
                .format({'Chg%':'{:+.2f}','Vol':'{:.2f}','Spk H/P%':'{:.1f}',
                         'Spk Vol':'{:.1f}','maxCA%':'{:+.1f}'}),
                use_container_width=True, height=420)
        else: st.info("Tidak ada P1 saat ini.")

    # Tab P3
    with tabs[3]:
        lst = [r for r in p3_list if r['in_wl']] if show_only_wl else p3_list
        st.markdown(f"**P3 Momentum | WL: {len([r for r in p3_list if r['in_wl']])} | Total: {len(p3_list)}**")
        if lst:
            rows=[{'★':('★' if r['in_wl'] else ''),'Code':r['code'],'Close':r['close'],
                'Chg%':r['chg'],'Vol':r['vol'],
                'Spk1':f"{r['spk1_date']}+{r['spk1_hvp']:.0f}%(x{r['spk1_vol']:.1f})",
                'Spk2':f"{r['spk2_date']}+{r['spk2_hvp']:.0f}%(x{r['spk2_vol']:.1f})",
                'Trigger':r['trigger']} for r in lst]
            df=pd.DataFrame(rows)
            st.dataframe(df.style
                .map(lambda v:'color:#4ade80;font-weight:bold' if isinstance(v,float) and v>0
                          else ('color:#f87171;font-weight:bold' if isinstance(v,float) and v<0 else ''),
                          subset=['Chg%'])
                .format({'Chg%':'{:+.2f}','Vol':'{:.2f}'}),
                use_container_width=True, height=420)
        else: st.info("Tidak ada P3 saat ini.")

    # Tab OLseq
    with tabs[4]:
        lst = [r for r in ol_list if r['in_wl'] and r['vol']>0] if show_only_wl else [r for r in ol_list if r['vol']>0]
        st.markdown(f"**OL Berturut | WL: {len([r for r in ol_list if r['in_wl']])} | Total: {len(ol_list)}**")
        if lst:
            rows=[{'★':('★' if r['in_wl'] else ''),'Code':r['code'],'Close':r['close'],
                'Chg%':r['chg'],'H/P%':r['hvp'],'Vol':r['vol'],
                'Hari':r['days'],'Sequence':r['seq']} for r in lst]
            df=pd.DataFrame(rows)
            st.dataframe(df.style
                .map(lambda v:'color:#4ade80;font-weight:bold' if isinstance(v,float) and v>0
                          else ('color:#f87171;font-weight:bold' if isinstance(v,float) and v<0 else ''),
                          subset=['Chg%','H/P%'])
                .map(lambda v:'color:#4ade80' if isinstance(v,float) and v<0.3
                          else ('color:#fbbf24' if isinstance(v,float) and v<0.7 else ''),subset=['Vol'])
                .format({'Chg%':'{:+.2f}','H/P%':'{:+.2f}','Vol':'{:.2f}'}),
                use_container_width=True, height=520)
        else: st.info("Tidak ada OL Berturut saat ini.")

    # Tab SV
    with tabs[5]:
        lst = [r for r in sv_list if r['in_wl']] if show_only_wl else sv_list
        st.markdown(f"**Spike Valuasi Rp800Jt-5M | WL: {len([r for r in sv_list if r['in_wl']])} | Total: {len(sv_list)}**")
        if lst:
            rows=[{'★':('★' if r['in_wl'] else ''),'Code':r['code'],'Close':r['close'],
                'Chg%':r['chg'],'Vol':r['vol'],'Jml Spk':r['n'],
                'Best':f"{r['best']['date']}+{r['best']['hvp']:.0f}%(Rp{r['best']['val_b']:.2f}M)",
                'mc15%':r['max_chg15'],
                'Candle':('+'.join(x for x in ['OL' if r['ol'] else '','Doji' if r['doji'] else '','CAvg' if r['cavg'] else ''] if x) or '-')
                } for r in lst]
            df=pd.DataFrame(rows)
            st.dataframe(df.style
                .map(lambda v:'color:#4ade80;font-weight:bold' if isinstance(v,float) and v>0
                          else ('color:#f87171;font-weight:bold' if isinstance(v,float) and v<0 else ''),
                          subset=['Chg%'])
                .format({'Chg%':'{:+.2f}','Vol':'{:.2f}','mc15%':'{:+.1f}'}),
                use_container_width=True, height=520)
        else: st.info("Tidak ada SV saat ini.")

    # Tab Alert
    with tabs[6]:
        lst = [r for r in alert_list if r['in_wl']] if show_only_wl else alert_list
        st.markdown(f"**Alert Reversal | WL: {len([r for r in alert_list if r['in_wl']])} | Total: {len(alert_list)}**")
        if lst:
            rows=[{'★':('★' if r['in_wl'] else ''),'Code':r['code'],'Close':r['close'],
                'Chg%':r['chg'],'Vol':r['vol'],'Drop 5H%':r['acc_drop'],
                'Med Vol':r['med_vol'],'Merah/5':r['red5'],'Last Spk':r['spk']} for r in lst]
            df=pd.DataFrame(rows)
            st.dataframe(df.style
                .map(lambda v:'color:#f87171;font-weight:bold' if isinstance(v,float) and v<0 else '',
                          subset=['Drop 5H%','Chg%'])
                .map(lambda v:'color:#4ade80' if isinstance(v,float) and v<0.3 else '',
                          subset=['Med Vol','Vol'])
                .format({'Chg%':'{:+.2f}','Vol':'{:.2f}','Drop 5H%':'{:.1f}','Med Vol':'{:.2f}'}),
                use_container_width=True, height=420)
        else:
            st.success("✅ Tidak ada Alert WL saat ini — pasar sehat!")

    # Tab Stockpick
    with tabs[7]:
        st.markdown("### 🛒 Stockpick Buy Close")

        # Parameter
        with st.expander("⚙️ Sesuaikan Parameter", expanded=False):
            c1, c2, c3 = st.columns(3)
            new_hvp = c1.slider("Max H/P%",     1.0, 15.0, 7.0, 0.5)
            new_min = c2.slider("Min Close/P%", -5.0,  5.0, 0.0, 0.5)
            new_max = c3.slider("Max Close/P%",  0.0, 15.0, 5.0, 0.5)
            if st.button("🔄 Rescan"):
                st.session_state['sp_hvp'] = new_hvp
                st.session_state['sp_min'] = new_min
                st.session_state['sp_max'] = new_max
                sp_list = scan_stockpick(all_ohlcv, avg_vols, target,
                                         max_hvp=new_hvp, min_chg=new_min, max_chg=new_max)
                sp_wl_new = [r for r in sp_list if r['in_wl']]
                st.success(f"Rescan selesai: {len(sp_wl_new)} WL")

        sp_wl  = [r for r in sp_list if r['in_wl']]
        sp_nwl = [r for r in sp_list if not r['in_wl']]
        st.markdown(
            f"**Kriteria: H/P≤{sp_hvp:.0f}% | C/P={sp_min:.0f}~{sp_max:.0f}% | "
            f"Vol>PrevVol | 7H bersih** — "
            f"WL: **{len(sp_wl)}** | Non-WL: {len(sp_nwl)}"
        )

        lst = sp_wl if show_only_wl else sp_list
        if lst:
            rows = []
            for r in lst:
                rows.append({
                    '★':        '★' if r['in_wl'] else '',
                    'Code':     r['code'],
                    'Close':    r['close'],
                    'Chg%':     r['chg'],
                    'H/P%':     r['hvp'],
                    'Vol/avg':  r['vol'],
                    'Vol/Prev': r['vol_vs_prev'],
                    'mc7%':     r['max_chg7'],
                    'Candle':   r['candle'],
                })
            df = pd.DataFrame(rows)
            st.dataframe(
                df.style
                  .map(lambda v: 'color:#4ade80;font-weight:bold' if isinstance(v,float) and v>0
                                 else ('color:#f87171;font-weight:bold' if isinstance(v,float) and v<0 else ''),
                       subset=['Chg%','H/P%'])
                  .map(lambda v: 'color:#4ade80' if isinstance(v,float) and v<0.3
                                 else ('color:#fbbf24' if isinstance(v,float) and v<0.7 else ''),
                       subset=['Vol/avg'])
                  .map(lambda v: 'color:#a78bfa;font-weight:bold' if isinstance(v,float) and v>1.5
                                 else ('color:#fbbf24' if isinstance(v,float) and v>1.0 else ''),
                       subset=['Vol/Prev'])
                  .format({'Chg%':'{:+.2f}','H/P%':'{:+.2f}',
                           'Vol/avg':'{:.2f}','Vol/Prev':'{:.2f}x','mc7%':'{:+.2f}'}),
                use_container_width=True, height=520,
            )
            st.info(
                "**Cara baca:** Chg% = kenaikan close dari kemarin | "
                "H/P% = high dari kemarin (≤7% = tidak overbought) | "
                "Vol/Prev = volume hari ini vs kemarin (>1.0 = naik) | "
                "mc7% = max close 7H terakhir (harus <7%)"
            )
        else:
            st.info("Tidak ada saham yang memenuhi kriteria Stockpick saat ini.")

    st.divider()
    st.caption(f"IDX Screener v1.0 | Hadi Lie | {now.strftime('%d %b %Y %H:%M')}")


if __name__ == "__main__":
    main()
