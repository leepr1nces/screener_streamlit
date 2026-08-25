"""
IDX Screener Dashboard — Hadi Lie
Streamlit Web App — Standalone (semua kode dalam 1 file)
"""

import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import glob
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
    'CUAN','DSSA','TINS','BUMI','BBRI','PTRO','AMMN','VKTR','BREN','BRPT',
    'SLIS','BRMS','DEWA','MDKA','ENRG','IATA','DOOH','AADI','RAJA','EMAS',
    'BAIK','INDY','KOTA','ADMR','BUVA','INET','TMPO','EXCL','BIPI','JARR',
    'MBMA','TEBE','MEDC','NCKL','CDIA','PSAB','GULA','ESSA','FAST','WIFI',
    'BRIS','RATU','PGEO','INKP','RMKE','EMTK','PANI','FUTR','MMIX','ARCI',
    'IOTF','BABY','HRTA','ARKO','COCO','SSIA','NICL','ICON','MSIN','BEER',
    'KPIG','UNTD','TOBA','ELSA','FILM','ASPR','SGER','SURI','LPKR','MAPI',
    'AHAP','BBHI','DEWI','ASLI','OASA','FORE','DATA','WEGE','SMIL','MBSS',
    'UVCR','SMLE','WIRG','KOKA','SOCI','GTSI','NETV','BBYB','ARTO','YELO',
    'DKFT','ZATA','HALO','GJTL','LIVE','CSIS','HUMI','KBLV','VTNY','REAL',
    'KRYA','CBDK','BNGA','ASHA','MEDS','KAQI','CITY','NTBK','SWID','BOBA',
    'GZCO','BELL','EURO','PPRE','APLN','KJEN','NEST','NIKL','RGAS','SMDR',
    'FOLK','MBTO','FORU','ESIP','TRUK','LEAD','SRSN','TRIN','RLCO','APEX',
    'JKON','DNAR','DOSS','BAPA','DGIK','LAJU','ADHI','TOOL','TOSK','GPSO',
    'PRIM','SQMI','DSFI','BRRC','TRJA','DEFI','KLAS','SULI','BSBK','ESTI',
    'OKAS','TGUK','ISEA','KIOS','DPUM','HAJJ','WOWS','BOAT','RBMS','JATI',
    'KRAS','SMGA','WTON','OILS','DAAZ','GOTO','PTMP','SMBR','RMKO','KUAS',
    'CHEM','HDIT','NZIA','GSMF','KOCI','DYAN','BANK','SOLA','PSDN','MERI',
    'ATAP','IRRA','TPMA','MSKY','WAPO','MAYA','HELI','TNCA','KKES','AISA',
    'FIRE','AGRO','KICI','PAMG','JAST','LABA','WINE','BEST','PNBS','GOLF',
    'HOKI','CRSN','BBRM','OPMS','DMMX','JAYA','BCIP','SAME','NOBU','ACRO',
    'PPRI','MOLI','AXIO','KAEF','DKHH','BOLA','PART','MPIX','SDMU','AGRS',
    'ADMG','UFOE','GRPH','CARS','MHKI','MCOR','CGAS','DIVA','ERTX','GRIA',
    'MPPA','MSIE','FWCT','ASLC','ELIT','MDLA','INOV','ZYRX','MITI','DFAM',
    'PJHB','FITT','OBMD','INPC','PTPS','RCCC','BBSS','MUTU','TMAS','BGTG',
    'CENT','MDLN','RICY','LUCK','MPXL','SICO','BKSW','BACA','CAKK','AYLS',
    'GTRA','ATLA','MPOW','NICE','ARII','INAI','KSIX','PURI','AKSI','RAAM',
    'JAWA','FUJI','SEMA','RUIS','LPPS','NASI','BVIC','EAST','AMAN','CINT',
    'PMJS','GEMA','DGNS','HDFA','ESTA','BATR','SMMT','SDPC','BABP','AMIN',
    'MKTR','ITMA','TRIS','HAIS','PICO','BNII','AMAR','MAXI','VICO','ACST',
    'BCAP','MTWI','BKDP','GTBO','ZBRA','JMAS','TRUE','TAYS','ADCP','BIMA',
    'INAF','INDX','BAJA',
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
    uploaded_files = sorted(uploaded_files, key=lambda f: f.name)  # urut kronologis by nama file
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
                'T':   str(row.get('Time', '') or ''),
            })
        os.unlink(tmp_path)
    for code in all_ohlcv:
        latest_per_date = {}
        for b in sorted(all_ohlcv[code], key=lambda x: x['date']):
            latest_per_date[b['date']] = b  # overwrite -> snapshot terakhir hari itu yang dipakai
        all_ohlcv[code] = [latest_per_date[d] for d in sorted(latest_per_date.keys())]
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
    results.sort(key=lambda x: (-int(x['in_wl']), -x.get('chg',0), -x.get('hvp',0)))
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
    results.sort(key=lambda x: (-int(x['in_wl']), -x.get('chg',0), -x.get('hvp',0)))
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
    results.sort(key=lambda x: (-int(x['in_wl']), -x.get('chg',0), -x.get('hvp',0)))
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
        prev4_vols=[b['V'] for b in bars[-5:-1] if b.get('V',0)>0]
        low_v = (b0.get('V',0) < np.mean(prev4_vols)*0.7) if prev4_vols else False
        if low_v: sc+=15
        results.append({'code':code,'in_wl':in_wl,'close':int(b0['C']),'chg':round(chg0,2),
            'vol':round(vr0,2),'score':round(sc,1),'n':len(spikes_val),
            'best':best,'spikes':spikes_val[:3],'max_chg15':round(max_chg15,2),
            'ol':is_ol(b0),'doji':is_doji(b0),'cavg':bool(b0.get('A') and b0['C']<b0['A']),
            'low_v':low_v})
    results.sort(key=lambda x: (-int(x['in_wl']), -x.get('chg',0), -x.get('hvp',0)))
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
    results.sort(key=lambda x: (-int(x['in_wl']), -x.get('chg',0), -x.get('hvp',0)))
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
    results.sort(key=lambda x: (-int(x['in_wl']), -x.get('chg',0), -x.get('hvp',0)))
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
                   min_chg=2.0, max_chg=12.0,
                   lookback=8, max_close=10.0):
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
        # Kriteria 1: Chg% (Close/Prev) >= min_chg DAN <= max_chg
        if chg0 < min_chg or chg0 > max_chg:
            continue
        # Kriteria 2: Volume hari ini > kemarin
        if v1 <= 0 or v0 <= v1:
            continue
        # Kriteria 3: 8H ke belakang tidak ada Close/Prev >= max_close
        period8 = bars[-lookback-1:-1]
        spike8  = any(b.get('P') and b['P'] > 0 and pct(b['C'], b['P']) >= max_close
                      for b in period8)
        if spike8:
            continue
        # Kriteria 4: Kemarin harus Doji ATAU Candle Merah ATAU OL
        if not b1 or not b1.get('O') or not b1.get('C') or b1['O'] <= 0:
            continue
        doji_prev  = abs(b1['C'] - b1['O']) / b1['O'] * 100 < 0.8
        merah_prev = b1['C'] < b1['O']
        ol_prev    = b1.get('L') and b1['L'] > 0 and abs(b1['O'] - b1['L']) / b1['O'] * 100 < 0.5
        if not (doji_prev or merah_prev or ol_prev):
            continue
        # Kriteria 5: Divergen volume — ada spike vol besar dalam 15H,
        # setelah spike vol mengering, harga tidak turun dari level spike
        period15 = bars[-17:-1]  # 15H ke belakang sebelum hari ini
        vol_spike_idx = None
        vol_spike_close = None
        for i, b in enumerate(period15):
            if not b.get('H') or not b.get('P') or b['P'] <= 0: continue
            if i < 4: continue  # butuh minimal 4 bar sebelumnya untuk avg
            prev4_vols = [x.get('V',0) for x in period15[max(0,i-4):i]]
            avg4 = sum(prev4_vols)/len(prev4_vols) if prev4_vols else 0
            if avg4 > 0 and b.get('V',0) > avg4 * 1.5:  # spike vol >1.5x avg
                vol_spike_idx = i
                vol_spike_close = b.get('C', 0)
        if vol_spike_idx is None:
            continue
        # Setelah spike: volume trend menurun
        after_spike = period15[vol_spike_idx+1:]
        if len(after_spike) < 2:
            continue
        after_vols = [b.get('V',0) for b in after_spike]
        # Volume hari-hari setelah spike rata-rata lebih kecil dari spike
        spike_vol = period15[vol_spike_idx].get('V',0)
        avg_after = sum(after_vols)/len(after_vols) if after_vols else 0
        vol_divergen = avg_after < spike_vol * 0.7  # vol after < 70% dari spike
        if not vol_divergen:
            continue
        # Harga tidak turun dari level spike (close sekarang >= close saat spike)
        if vol_spike_close and b0.get('C') and b0['C'] < vol_spike_close * 0.95:
            continue
        sc = 50.0 + vr0*10 + chg0*5 + hvp0
        if in_wl: sc += 30
        vp = v0/v1 if v1 > 0 else 0
        max_c7h = max((pct(b['C'],b['P']) for b in period8 if b.get('P') and b['P']>0), default=0.0)
        green = b0['C'] > (b0.get('O') or b0['C'])
        ol  = bool(b0.get('O') and b0.get('L') and b0['O']>0 and abs(b0['O']-b0['L'])/b0['O']*100 < 0.5)
        doji= bool(b0.get('O') and b0['O']>0 and abs(b0['C']-b0['O'])/b0['O']*100 < 0.8)
        candle = ('OL+Doji' if ol and doji else 'OL' if ol else
                  'Doji'    if doji else 'Hijau' if green else 'Merah')
        open_pct = pct(b0['O'], b0['P']) if b0.get('O') and b0['O'] > 0 else 0
        results.append({
            'code': code, 'in_wl': in_wl, 'close': int(b0['C']),
            'chg': round(chg0,2), 'hvp': round(hvp0,2),
            'vol': round(vr0,2), 'vol_vs_prev': round(vp,2),
            'score': round(sc,1), 'max_chg7': round(max_c7h,2),
            'candle': candle, 'open_pct': round(open_pct,2),
        })
    results.sort(key=lambda x: (-int(x['in_wl']), -x.get('chg',0), -x.get('hvp',0)))
    return results



# ══════════════════════════════════════════════════════════════════════════════
# BOS — Break Out Soon
# ══════════════════════════════════════════════════════════════════════════════
def scan_bos(all_ohlcv, avg_vols, target, window=7):
    results = []
    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target: continue
        if len(bars) < window + 2: continue
        in_wl = code in ALL_WL
        today = bars[-1]
        win = bars[-(window+1):-1]
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
                spike_days.append({'date': wb['date'][5:], 'hvp': round(hvp, 1)})
        if len(spike_days) < 2: continue
        cavg = False; vol_kering = False
        if today.get('H') and today.get('C') and today.get('A'):
            cavg = (today['C'] < today['H']) and (today['C'] < today['A'])
        prev4_vols = [b['V'] for b in bars[-5:-1] if b.get('V', 0) > 0]
        if prev4_vols:
            vol_kering = today['V'] < np.mean(prev4_vols) * 0.7
        if cavg and vol_kering:   entry = "CAVG+LowV";       score = 100
        elif cavg:                 entry = "CAVG";           score = 70
        elif vol_kering:           entry = "LowV";           score = 70
        else:                      entry = "Tunggu";         score = 40
        score += len(spike_days) * 10 + (30 if in_wl else 0)
        chg0 = (today['C'] - today['P']) / today['P'] * 100 if today.get('P') and today['P'] > 0 else 0
        hvp0 = (today['H'] - today['P']) / today['P'] * 100 if today.get('H') and today.get('P') and today['P'] > 0 else 0
        results.append({'code': code, 'in_wl': in_wl, 'close': int(today['C']),
            'chg': round(chg0,2), 'hvp': round(hvp0,2), 'spikes': spike_days,
            'n_spike': len(spike_days), 'entry': entry, 'score': score})
    results.sort(key=lambda x: (-int(x['in_wl']), -x.get('chg',0), -x.get('hvp',0)))
    return results


# ══════════════════════════════════════════════════════════════════════════════
# BOH — Breakout High
# ══════════════════════════════════════════════════════════════════════════════
def detect_descending_high(bars, spike_min_pct=4.0, dh_window_sizes=(5, 4, 3)):
    """Cek pola 'descending high': di hari tertua window ada High spike >= spike_min_pct%,
    lalu tiap hari berikutnya High-nya terus mengecil (T-4 < T-5, T-3 < T-4, dst).
    Dicoba window 5H dulu (paling meyakinkan), kalau tidak match coba 4H, lalu 3H."""
    for n in dh_window_sizes:
        if len(bars) < n: continue
        window = bars[-n:]
        first = window[0]
        if not (first.get('H') and first.get('P') and first['P'] > 0): continue
        spike_pct = (first['H'] - first['P']) / first['P'] * 100
        if spike_pct < spike_min_pct: continue
        ok = True
        for i in range(1, n):
            h_prev = window[i-1].get('H')
            h_now = window[i].get('H')
            if h_prev is None or h_now is None or not (h_now < h_prev):
                ok = False; break
        if ok:
            return {'window': n, 'spike_pct': round(spike_pct, 1)}
    return None


def scan_divergen(all_ohlcv, avg_vols, target, window_sizes=(8, 10, 15, 20),
                   vol_ratio_max=0.85, low_tolerance=0.98, price_dip_max=-3.0,
                   spike_vol_mult=1.5):
    """Pola Divergen: harga basing/naik (higher low) sementara volume TREN-nya mengering,
    mirip yang ditarik manual di TradingView (garis support naik di harga, garis
    resistance turun di volume). Sesekali boleh ada 'C-Spike' volume (di atas MA window,
    kadang dibarengi High +5-7%) — C-Spike ini dikeluarkan dari perhitungan tren supaya
    tidak menggagalkan deteksi, tapi tetap dicatat sebagai info.
    Dicoba beberapa ukuran window (8/10/15/20 hari) karena periode 'mengering' tiap
    saham bisa beda-beda panjangnya — lolos di SALAH SATU ukuran window sudah cukup."""
    results = []
    max_window = max(window_sizes)
    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target: continue
        in_wl = code in ALL_WL
        n = len(bars)
        if n < min(window_sizes) + 1: continue

        best = None
        for wsize in sorted(window_sizes):
            if n < wsize: continue
            window = bars[-wsize:]
            closes = [b['C'] for b in window if b.get('C')]
            vols   = [b.get('V', 0) for b in window]
            lows   = [b['L'] for b in window if b.get('L')]
            if len(closes) < wsize or len(lows) < wsize: continue

            vol_ma = np.mean([v for v in vols if v > 0]) if any(vols) else 0

            cspike_days = []
            for b in window:
                v = b.get('V', 0)
                if vol_ma > 0 and v > vol_ma * spike_vol_mult:
                    hp = (b['H']-b['P'])/b['P']*100 if b.get('H') and b.get('P') and b['P']>0 else 0
                    cspike_days.append({'date': b['date'][5:], 'vol_x': round(v/vol_ma,2), 'high_pct': round(hp,1)})

            non_cspike_vols = [b.get('V',0) for b in window
                               if not (vol_ma > 0 and b.get('V',0) > vol_ma * spike_vol_mult)]
            if len(non_cspike_vols) < max(4, wsize // 2):
                non_cspike_vols = vols
            half_v = len(non_cspike_vols) // 2
            vol_first  = np.mean(non_cspike_vols[:half_v]) if non_cspike_vols[:half_v] else 0
            vol_second = np.mean(non_cspike_vols[half_v:]) if non_cspike_vols[half_v:] else 0
            vol_ratio  = (vol_second / vol_first) if vol_first > 0 else 1.0

            half_l = len(lows) // 2
            low_first  = min(lows[:half_l]) if lows[:half_l] else 0
            low_second = min(lows[half_l:]) if lows[half_l:] else 0
            higher_low = low_second >= low_first * low_tolerance

            price_start = closes[0]; price_now = closes[-1]
            if not price_start or price_start <= 0: continue
            price_chg = (price_now - price_start) / price_start * 100

            vol_declining = vol_ratio < vol_ratio_max
            price_ok = price_chg > price_dip_max
            if not (vol_declining and price_ok and higher_low): continue

            # Simpan window dengan vol_ratio terkecil (paling jelas mengering)
            if best is None or vol_ratio < best['vol_ratio']:
                today = window[-1]
                chg0 = (today['C']-today['P'])/today['P']*100 if today.get('P') and today['P']>0 else 0
                score = round((1-vol_ratio)*100) + (20 if price_chg > 0 else 0) + (10*len(cspike_days)) + (30 if in_wl else 0)
                best = {
                    'code': code, 'in_wl': in_wl, 'close': int(today['C']),
                    'chg': round(chg0,2),
                    'price_chg_window': round(price_chg,1),
                    'vol_ratio': vol_ratio,
                    'vol_ratio_pct': round(vol_ratio*100,0),
                    'window_days': wsize,
                    'spike_count': len(cspike_days),
                    'last_spike': cspike_days[-1] if cspike_days else None,
                    'score': score,
                }
        if best:
            best['desc_high'] = detect_descending_high(bars)
            results.append(best)
    results.sort(key=lambda x: (-int(x['in_wl']), x['vol_ratio_pct'], -x['score']))
    return results[:75]


def scan_ara(all_ohlcv, avg_vols, target, chg_min=16.0, chg_max=30.0, lookback_days=25):
    """Deteksi saham yang pernah naik besar (16-30%, mirip ARA) dalam lookback_days
    terakhir, lalu pantau apakah harga sudah retrace ke area 1/3 bawah dari kenaikan
    itu — dihitung dari Prev Close (sebelum naik) sampai High tertinggi yang pernah
    dicapai setelahnya. Alert kalau Low hari ini sudah menyentuh/menembus level itu."""
    results = []
    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target: continue
        in_wl = code in ALL_WL
        n = len(bars)
        window = bars[-lookback_days:] if n >= lookback_days else bars
        if len(window) < 2: continue

        # Cari hari ARA PALING BARU dalam window (Chg% 16-30%)
        ara_idx = None
        for i, b in enumerate(window):
            if not b.get('P') or b['P'] <= 0: continue
            chg = (b['C'] - b['P']) / b['P'] * 100
            if chg_min <= chg <= chg_max:
                ara_idx = i  # ambil yang paling akhir kalau ada beberapa
        if ara_idx is None: continue

        ara_bar = window[ara_idx]
        prev_close = ara_bar['P']
        ara_chg = (ara_bar['C'] - prev_close) / prev_close * 100

        # Peak High tertinggi SEJAK hari ARA (termasuk hari ARA itu sendiri) sampai target
        after_ara = window[ara_idx:]
        peak_high = max((b['H'] for b in after_ara if b.get('H')), default=ara_bar.get('H', ara_bar['C']))
        if peak_high <= prev_close: continue

        range_total = peak_high - prev_close
        lower_third = prev_close + range_total / 3

        today = window[-1]
        chg0 = (today['C']-today['P'])/today['P']*100 if today.get('P') and today['P']>0 else 0
        days_since_ara = len(window) - 1 - ara_idx
        # Cek apakah hari-hari SETELAH ARA (bukan hari ARA itu sendiri, karena Low di
        # hari itu wajar rendah — harga sebelum naik) sudah pernah nyentuh 1/3 bawah.
        first_touch_idx = None
        for j in range(ara_idx + 1, len(window)):
            bj = window[j]
            if bj.get('L') is not None and bj['L'] <= lower_third:
                first_touch_idx = j
                break
        is_new_alert = (first_touch_idx is not None and first_touch_idx == len(window) - 1)
        already_alerted = first_touch_idx is not None

        results.append({
            'code': code, 'in_wl': in_wl, 'close': int(today['C']), 'chg': round(chg0,2),
            'ara_date': ara_bar['date'][5:], 'ara_chg': round(ara_chg,1),
            'prev_close': int(prev_close), 'peak_high': int(peak_high),
            'lower_third': int(round(lower_third)), 'days_since_ara': days_since_ara,
            'alerted': already_alerted, 'is_new_alert': is_new_alert,
        })
    results.sort(key=lambda x: (-int(x['is_new_alert']), -int(x['alerted']), -int(x['in_wl']), x['days_since_ara']))
    return results


def scan_boh(all_ohlcv, avg_vols, target, min_trigger=20.0, min_gap=5.0, max_days=10):
    results = []
    for code, bars in all_ohlcv.items():
        if not bars or bars[-1]['date'] != target: continue
        if len(bars) < 3: continue
        in_wl = code in ALL_WL
        found = None
        for i in range(1, len(bars)-1):
            bt = bars[i]; bg = bars[i+1]
            if not bt.get('C') or not bt.get('P') or bt['P'] <= 0: continue
            if not bg.get('O') or bt['C'] <= 0: continue
            chg_t = (bt['C'] - bt['P']) / bt['P'] * 100
            if chg_t < min_trigger: continue
            gap = (bg['O'] - bt['C']) / bt['C'] * 100
            if gap < min_gap: continue
            found = {'trigger_date': bt['date'][5:], 'trigger_chg': round(chg_t,1),
                     'gap_date': bg['date'][5:], 'gap_pct': round(gap,1), 'gap_idx': i+1}
        if not found: continue
        days_after = len(bars) - 1 - found['gap_idx']
        if days_after < 0 or days_after > max_days: continue
        today = bars[-1]
        prev4 = bars[max(0, len(bars)-5):-1]
        prev4_vols = [b['V'] for b in prev4 if b.get('V', 0) > 0]
        vol_kering = today['V'] < np.mean(prev4_vols) * 0.5 if prev4_vols else False
        chg0 = (today['C'] - today['P']) / today['P'] * 100 if today.get('P') and today['P'] > 0 else 0
        hvp0 = (today['H'] - today['P']) / today['P'] * 100 if today.get('H') and today.get('P') and today['P'] > 0 else 0
        entry = "🎯 ENTRY" if vol_kering else f"⏳ H+{days_after} stlh gap"
        score = (80 if vol_kering else 50) + (30 if in_wl else 0)
        results.append({'code': code, 'in_wl': in_wl, 'close': int(today['C']),
            'chg': round(chg0,2), 'hvp': round(hvp0,2),
            'trigger_date': found['trigger_date'], 'trigger_chg': found['trigger_chg'],
            'gap_date': found['gap_date'], 'gap_pct': found['gap_pct'],
            'days_after': days_after, 'vol_kering': vol_kering,
            'entry': entry, 'score': score})
    results.sort(key=lambda x: (-int(x['in_wl']), -x.get('chg',0), -x.get('hvp',0)))
    return results


# ══════════════════════════════════════════════════════════════════════════════
# TTx — Time Trading eXtended
# ══════════════════════════════════════════════════════════════════════════════
def scan_ttx(all_ohlcv, avg_vols, target, hvp_thresh=8.0, gap_min=3, gap_max=15, tol=2):
    def is_spike(bar, prev4):
        if not bar.get('H') or not bar.get('P') or bar['P'] <= 0: return False
        if (bar['H'] - bar['P']) / bar['P'] * 100 <= hvp_thresh: return False
        vols = [b['V'] for b in prev4 if b.get('V', 0) > 0]
        return bar['V'] > np.mean(vols) if vols else False

    results = []
    for code, bars_full in all_ohlcv.items():
        if code not in ALL_WL: continue
        # Potong ke tanggal target — WAJIB, biar scan_ttx bisa dipakai buat cek tanggal
        # historis juga (mis. di tab TrackRecord / Pola Trading Log), bukan cuma hari ini.
        target_idx = next((i for i, b in enumerate(bars_full) if b['date'] == target), None)
        if target_idx is None or target_idx < 5: continue
        bars = bars_full[:target_idx+1]
        spikes = []
        for i in range(4, len(bars)):
            if is_spike(bars[i], bars[i-4:i]):
                hvp = (bars[i]['H'] - bars[i]['P']) / bars[i]['P'] * 100
                spikes.append({'idx': i, 'date': bars[i]['date'][5:], 'hvp': round(hvp,1)})
        if len(spikes) < 2: continue
        last_idx = len(bars) - 1
        for i in range(len(spikes)-1, 0, -1):
            s2 = spikes[i]; s1 = spikes[i-1]
            gap = s2['idx'] - s1['idx']
            if not (gap_min <= gap <= gap_max): continue
            pred_idx = s2['idx'] + gap
            s3 = next((s for s in spikes[i+1:] if pred_idx-tol <= s['idx'] <= pred_idx+tol), None)
            upcoming = (pred_idx - tol) > last_idx
            reminder = upcoming and (pred_idx - tol - last_idx) <= 2
            pred_date = bars[pred_idx]['date'][5:] if pred_idx < len(bars) else f"~{pred_idx-last_idx}H lagi"
            if s3:          status = f"✅ Spike3 {s3['date']} +{s3['hvp']}%"; priority = 1
            elif reminder:  status = f"🔔 REMINDER — {pred_date}";             priority = 0
            elif upcoming:  status = f"⏳ Upcoming {pred_date}";               priority = 2
            else:           status = f"❓ Lewat {pred_date}";                  priority = 3
            today = bars[last_idx]
            chg0 = (today['C'] - today['P']) / today['P'] * 100 if today.get('P') and today['P'] > 0 else 0
            results.append({'code': code, 'in_wl': True, 'gap': gap, 'priority': priority,
                'spk1_date': s1['date'], 'spk1_hvp': s1['hvp'],
                'spk2_date': s2['date'], 'spk2_hvp': s2['hvp'],
                's3': s3, 'pred_date': pred_date, 'status': status,
                'chg': round(chg0,2), 'close': int(today['C'])})
            break
    results.sort(key=lambda x: (x['priority'], x['gap']))
    return results


def get_data_folder_signature(folder="data"):
    """Fingerprint isi folder data/ (nama file + ukuran) — dipakai sebagai cache key,
    supaya cache otomatis invalid begitu ada file baru/berubah. Sengaja TIDAK pakai
    waktu modifikasi file (mtime) karena beberapa platform deploy (termasuk kemungkinan
    Streamlit Cloud via git checkout) bisa me-reset mtime semua file jadi sama, yang
    bikin fingerprint gagal berubah walau isi folder sebenarnya sudah beda."""
    import glob
    files = sorted(glob.glob(f"{folder}/*.xls") + glob.glob(f"{folder}/*.xlsx"))
    sig = tuple((os.path.basename(f), os.path.getsize(f)) for f in files)
    return sig


@st.cache_data(show_spinner=False, ttl=90)
def load_from_folder_cached(folder, _signature):
    """Versi cached dari load_from_folder — _signature dipakai Streamlit sebagai cache
    key (nilainya sendiri tidak dipakai di dalam fungsi, makanya prefix underscore).
    ttl=90 detik sebagai jaring pengaman tambahan — data paling lama basi 90 detik
    meski karena suatu sebab fingerprint tidak berubah."""
    return load_from_folder(folder)


def load_from_folder(folder="data"):
    """Load semua file XLS/XLSX dari folder data/ di repo."""
    import glob
    all_ohlcv = {}
    files = sorted(glob.glob(f"{folder}/*.xls") + glob.glob(f"{folder}/*.xlsx"))
    if not files:
        return {}
    for path in files:
        fname = os.path.basename(path)
        # Baca tanggal dari kolom Date di dalam file (lebih akurat)
        try:
            try: df = pd.read_excel(path, sheet_name='Trades')
            except: df = pd.read_excel(path)
        except Exception as e:
            continue
        for col in ['Open','High','Low','Close','Avg','Volume','Prev','Value','Last']:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce')
        if 'Close' not in df.columns or df['Close'].isna().all():
            if 'Last' in df.columns: df['Close'] = df['Last']
        elif 'Last' in df.columns:
            df['Close'] = df['Close'].fillna(df['Last'])
        # Ambil tanggal dari kolom Date jika ada
        if 'Date' in df.columns:
            dates = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
            date = dates.dropna().iloc[0].strftime('%Y-%m-%d') if not dates.dropna().empty else None
        else:
            m = re.search(r'(\d{8})', fname)
            date = f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:]}" if m else None
        if not date: continue
        df = df.dropna(subset=['Code','Close'])
        df = df[df['Code'].apply(lambda x: str(x).isalpha() and len(str(x)) <= 6)]
        for _, row in df.iterrows():
            code = str(row['Code'])
            all_ohlcv.setdefault(code, []).append({
                'date': date,
                'O': safe_float(row.get('Open')),
                'H': safe_float(row.get('High')),
                'L': safe_float(row.get('Low')),
                'C': float(row['Close']),
                'A': safe_float(row.get('Avg')),
                'V': float(row.get('Volume') or 0),
                'P': safe_float(row.get('Prev')),
                'Val': float(row.get('Value') or 0),
                'T': str(row.get('Time', '') or ''),
            })
    for code in all_ohlcv:
        latest_per_date = {}
        for b in sorted(all_ohlcv[code], key=lambda x: x['date']):
            latest_per_date[b['date']] = b  # overwrite -> snapshot terakhir hari itu yang dipakai
        all_ohlcv[code] = [latest_per_date[d] for d in sorted(latest_per_date.keys())]
    return all_ohlcv


# ══════════════════════════════════════════════════════════════════════════════
# AUTO STOCKPICK RANGKUMAN — Kompilasi terbaik dari semua pola
# ══════════════════════════════════════════════════════════════════════════════
def auto_stockpick(boa_full, boa_near, p1_list, p3_list, ol_list, sv_list, alert_list,
                   sp_list, bos_list, boh_list, ttx_list, all_ohlcv=None, target=None, div_list=None):
    """Kompilasi saham terbaik dari semua pola.
    Filter: >=3 pola ATAU (2 pola + spike H/P>=5% dalam 10H terakhir).
    Sorted: jumlah pola desc -> Chg% desc -> H/P% desc.
    """
    picks = {}

    def add(lst, pola):
        for r in lst:
            if not r.get('in_wl'): continue
            code = r['code']
            chg = r.get('chg', 0)
            hvp = r.get('hvp', 0)
            if code not in picks:
                picks[code] = {'code': code, 'chg': chg, 'hvp': hvp,
                               'close': r.get('close', 0), 'pola': []}
            if pola not in picks[code]['pola']:
                picks[code]['pola'].append(pola)
            picks[code]['chg'] = chg
            picks[code]['hvp'] = hvp

    add(boa_full, 'BOA✅')
    add(boa_near, 'BOA~')
    add(p1_list, 'P1')
    add([r for r in p3_list  if 'B' in str(r.get('trigger',''))], 'P3')
    add([r for r in ol_list  if r.get('days') == '3H'], 'OL3')
    add([r for r in bos_list if r.get('entry','') != 'Tunggu'], 'BOS')
    add([r for r in boh_list if r.get('vol_kering')], 'BOH')
    add([r for r in ttx_list if r.get('priority') == 0], 'TTx🔔')
    add(sp_list, 'SP')
    if div_list:
        add(div_list, 'Div')
        add([r for r in div_list if r.get('desc_high')], 'Desc-High')

    def has_spike_10h(code):
        """Cek apakah ada spike H/P >= 5% dalam 10 hari terakhir."""
        if all_ohlcv is None or code not in all_ohlcv: return False
        bars = all_ohlcv[code]
        window = bars[-10:] if len(bars) >= 10 else bars
        for b in window:
            if b.get('H') and b.get('P') and b['P'] > 0:
                if (b['H'] - b['P']) / b['P'] * 100 >= 5:
                    return True
        return False

    # Filter: >=3 pola ATAU (2 pola + spike 10H)
    result = []
    for r in picks.values():
        n = len(r['pola'])
        if n >= 3:
            r['filter'] = f'{n} pola'
            result.append(r)
        elif n == 2 and has_spike_10h(r['code']):
            r['filter'] = '2 pola + spike'
            result.append(r)

    result.sort(key=lambda x: (-x['chg'], -x['hvp'], -len(x['pola'])))
    return result


# ══════════════════════════════════════════════════════════════════════════════
# CANDLESTICK CHART
# ══════════════════════════════════════════════════════════════════════════════
def fetch_yahoo_quick(code, period='2mo'):
    """Ambil data harga dari Yahoo Finance untuk 1 kode saham — BERDIRI SENDIRI,
    sama sekali tidak menyentuh all_ohlcv, scan pipeline, atau StockPick Log/
    Trading Log. Cuma dipakai buat tab 'Cek Cepat' (mis. lagi di jalan, belum
    sempat upload data screener). Return list of bars, atau None kalau gagal."""
    try:
        import yfinance as yf
        ticker = code.strip().upper() + '.JK'
        df = yf.download(ticker, period=period, interval='1d', progress=False, auto_adjust=False)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        bars = []
        for idx, row in df.iterrows():
            c = safe_float(row.get('Close'))
            if c is None: continue
            bars.append({
                'date': idx.strftime('%Y-%m-%d'),
                'O': safe_float(row.get('Open')), 'H': safe_float(row.get('High')),
                'L': safe_float(row.get('Low')), 'C': c,
                'V': float(row.get('Volume') or 0), 'P': None,
            })
        for i in range(1, len(bars)):
            bars[i]['P'] = bars[i-1]['C']
        return bars if len(bars) >= 2 else None
    except Exception:
        return None


def render_fast_chart(codes, all_ohlcv, n_days=30, height=380, key='fastchart'):
    """Chart candlestick+volume yang CEPAT — semua data OHLCV untuk 'codes' di-embed
    langsung sebagai JS (sama seperti kalkulator Miracle Cuan), jadi ganti pilihan
    saham di dropdown-nya nggak perlu Streamlit rerun sama sekali (instan, murni
    client-side). Dipakai buat gantiin render_candlestick() (Plotly) di tab yang
    seringkali ganti-ganti saham buat lihat chart (AutoSP, TrackRecord, dst)."""
    parts = []
    for code in codes:
        bars = (all_ohlcv.get(code) or [])[-n_days:]
        if len(bars) < 3: continue
        bar_str = '|'.join([
            f"{b['date'][5:]}:{int(b.get('O') or b.get('C',0))}:{int(b.get('H',0))}:{int(b.get('L') or b.get('C',0))}:{int(b.get('C',0))}:{int(b.get('V',0))}"
            for b in bars if b.get('C')
        ])
        if bar_str:
            parts.append(f"{code}~{bar_str}")
    if not parts:
        st.info("Tidak ada data chart untuk saham-saham ini.")
        return
    parts.sort(key=lambda p: p.split('~')[0])
    ohlcv_payload = ';'.join(parts)
    codes_with_data = [p.split('~')[0] for p in parts]
    options_html = ''.join([f'<option value="{c}">{c}</option>' for c in codes_with_data])

    html = f"""
<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;padding:14px;border-radius:8px;max-width:520px;margin:0 auto;box-sizing:border-box">
  <select id="fc-sel-{key}" style="background:#1e293b;color:#e2e8f0;border:1px solid #334155;border-radius:6px;padding:6px 10px;font-size:13px;margin-bottom:8px;width:100%">
    {options_html}
  </select>
  <div id="fc-lbl-{key}" style="font-size:12px;color:#94a3b8;margin-bottom:4px"></div>
  <canvas id="fc-price-{key}" style="display:block"></canvas>
  <canvas id="fc-vol-{key}" style="display:block;margin-top:4px"></canvas>
</div>
<script>
(function(){{
  const ALL_BARS_{key} = {{}};
  "{ohlcv_payload}".split(';').forEach(chunk => {{
    const [code, barsStr] = chunk.split('~');
    if (!code || !barsStr) return;
    ALL_BARS_{key}[code] = barsStr.split('|').map(b => {{
      const [d,o,h,l,c,v] = b.split(':');
      return {{d, o:+o, h:+h, l:+l, c:+c, v:+v}};
    }});
  }});

  function drawChart_{key}(code) {{
    const bars = ALL_BARS_{key}[code];
    const cvP = document.getElementById('fc-price-{key}');
    const cvV = document.getElementById('fc-vol-{key}');
    const lbl = document.getElementById('fc-lbl-{key}');
    if (!bars || bars.length < 3) {{ lbl.textContent = code + ' — data tidak cukup'; return; }}
    lbl.textContent = '📊 ' + code + ' — ' + bars.length + 'H';
    const W = Math.min(350, cvP.parentElement.getBoundingClientRect().width - 24);
    const HP = 220, HV = 60, PAD = 6;
    cvP.width = W; cvP.height = HP; cvV.width = W; cvV.height = HV;
    cvP.style.width = W + 'px'; cvP.style.height = HP + 'px';
    cvV.style.width = W + 'px'; cvV.style.height = HV + 'px';
    const ctx = cvP.getContext('2d'), vctx = cvV.getContext('2d');
    ctx.clearRect(0,0,W,HP); vctx.clearRect(0,0,W,HV);
    const n = bars.length;
    const allP = bars.flatMap(b => [b.h, b.l]);
    const mn = Math.min(...allP), mx = Math.max(...allP), rng = mx - mn || 1;
    const bw = Math.max(3, Math.floor((W - PAD*2) / n * 0.6));
    const gap = (W - PAD*2) / n;
    function toX(i) {{ return PAD + i*gap + gap/2; }}
    function toY(v) {{ return PAD + (HP - PAD*2) * (1 - (v-mn)/rng); }}
    ctx.strokeStyle = '#334155'; ctx.lineWidth = 0.5;
    for (let i=0; i<=4; i++) {{
      const y = PAD + (HP-PAD*2)*i/4;
      ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke();
      const val = mx - (mx-mn)*i/4;
      ctx.fillStyle = '#475569'; ctx.font = '9px sans-serif';
      ctx.fillText(Math.round(val).toLocaleString('id-ID'), 2, y-2);
    }}
    const closes = bars.map(b => b.c);
    function ma(arr, n) {{ return arr.map((_, i) => {{ const s = arr.slice(Math.max(0,i-n+1), i+1); return s.reduce((a,b)=>a+b,0)/s.length; }}); }}
    [[ma(closes,7),'#60a5fa'],[ma(closes,14),'#f59e0b']].forEach(([arr,col]) => {{
      ctx.beginPath(); ctx.strokeStyle = col; ctx.lineWidth = 1.2;
      arr.forEach((v,i) => {{ i===0 ? ctx.moveTo(toX(i),toY(v)) : ctx.lineTo(toX(i),toY(v)); }});
      ctx.stroke();
    }});
    bars.forEach((b,i) => {{
      const x = toX(i), green = b.c >= b.o, col = green ? '#4ade80' : '#f87171';
      ctx.strokeStyle = col; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x,toY(b.h)); ctx.lineTo(x,toY(b.l)); ctx.stroke();
      const y1 = toY(Math.max(b.o,b.c)), y2 = toY(Math.min(b.o,b.c));
      ctx.fillStyle = col; ctx.fillRect(x-bw/2, y1, bw, Math.max(1, y2-y1));
      if (i%5===0 || i===n-1) {{
        ctx.fillStyle = '#475569'; ctx.font = '8px sans-serif';
        ctx.fillText(b.d, x-10, HP-2);
      }}
    }});
    const maxV = Math.max(...bars.map(b => b.v)) || 1;
    bars.forEach((b,i) => {{
      const x = toX(i), h = Math.max(2, b.v/maxV*(HV-4));
      const green = i===0 || b.v >= bars[i-1].v;
      vctx.fillStyle = green ? '#1D9E75' : '#EF9F27';
      vctx.fillRect(x-bw/2, HV-h, bw, h);
    }});
  }}

  document.getElementById('fc-sel-{key}').addEventListener('change', function() {{
    drawChart_{key}(this.value);
  }});
  drawChart_{key}('{codes_with_data[0]}');
}})();
</script>
"""
    components.html(html, height=height, scrolling=False)


def render_candlestick(code, all_ohlcv, n_days=30, chart_key='chart'):
    """Render candlestick chart + volume bar untuk saham tertentu.
    Menggunakan index kategorikal agar tidak ada gap hari libur.
    """
    bars = all_ohlcv.get(code, [])
    if not bars:
        st.warning(f"Data tidak ditemukan untuk {code}")
        return

    bars = bars[-n_days:]
    # Gunakan index 0,1,2,... sebagai x agar tidak ada gap hari libur
    dates  = [b['date'][5:] for b in bars]  # format MM-DD sebagai label
    idx    = list(range(len(bars)))
    opens  = [b.get('O') or b.get('C') for b in bars]
    highs  = [b.get('H') for b in bars]
    lows   = [b.get('L') or b.get('C') for b in bars]
    closes = [b.get('C') for b in bars]
    vols   = [b.get('V', 0) for b in bars]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.7, 0.3], vertical_spacing=0.03)

    # Candlestick — pakai index numerik, label tanggal di ticktext
    fig.add_trace(go.Candlestick(
        x=idx, open=opens, high=highs, low=lows, close=closes,
        name=code,
        increasing_line_color='#4ade80',
        decreasing_line_color='#f87171',
        increasing_fillcolor='#4ade80',
        decreasing_fillcolor='#f87171',
    ), row=1, col=1)

    # MA7 dan MA14
    def ma(data, n):
        result = []
        for i in range(len(data)):
            window = [d for d in data[max(0,i-n+1):i+1] if d is not None]
            result.append(sum(window)/len(window) if window else None)
        return result

    ma7  = ma(closes, 7)
    ma14 = ma(closes, 14)

    fig.add_trace(go.Scatter(x=idx, y=ma7,  mode='lines',
        line=dict(color='#60a5fa', width=1), name='MA7'), row=1, col=1)
    fig.add_trace(go.Scatter(x=idx, y=ma14, mode='lines',
        line=dict(color='#f59e0b', width=1), name='MA14'), row=1, col=1)

    # Volume bar — hijau jika vol hari ini > kemarin
    vol_colors = []
    for i in range(len(vols)):
        if i == 0:
            vol_colors.append('#4ade80')
        elif vols[i] > vols[i-1]:
            vol_colors.append('#4ade80')
        else:
            vol_colors.append('#f87171')
    fig.add_trace(go.Bar(
        x=idx, y=vols, name='Volume',
        marker_color=vol_colors, opacity=0.7,
    ), row=2, col=1)

    # Tick setiap 5 bar
    tick_vals = idx[::5]
    tick_text = [dates[i] for i in tick_vals]

    fig.update_layout(
        title=dict(text=f'📊 {code} — {n_days} hari trading', font=dict(color='#e2e8f0')),
        plot_bgcolor='#1e293b',
        paper_bgcolor='#0f172a',
        font=dict(color='#94a3b8'),
        xaxis_rangeslider_visible=False,
        height=500,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation='h', y=1.02, x=0),
        showlegend=True,
    )
    fig.update_xaxes(
        gridcolor='#334155', showgrid=True,
        tickmode='array', tickvals=tick_vals, ticktext=tick_text,
    )
    fig.update_yaxes(gridcolor='#334155', showgrid=True)

    st.plotly_chart(fig, use_container_width=True, key=chart_key)


# ══════════════════════════════════════════════════════════════════════════════
# TRACK RECORD — StockPick Performance
# ══════════════════════════════════════════════════════════════════════════════
# Daftar pola yang bisa di-backtest di tab TrackRecord — tiap pola punya cara sendiri
# menentukan siapa saja yang "lolos" (entry) di suatu tanggal.
PATTERN_TRACKRECORD_CONFIG = {
    'StockPick': lambda all_ohlcv, avg_vols, date_t: [
        r for r in scan_stockpick(truncate_ohlcv_to_date(all_ohlcv, date_t), avg_vols, date_t) if r['in_wl']],
    'BOA': lambda all_ohlcv, avg_vols, date_t: [
        r for r in scan_boa(truncate_ohlcv_to_date(all_ohlcv, date_t), avg_vols, date_t)[0] if r['in_wl']],
    'BOS': lambda all_ohlcv, avg_vols, date_t: [
        r for r in scan_bos(truncate_ohlcv_to_date(all_ohlcv, date_t), avg_vols, date_t) if r['in_wl'] and r.get('entry','') != 'Tunggu'],
    'BOH': lambda all_ohlcv, avg_vols, date_t: [
        r for r in scan_boh(truncate_ohlcv_to_date(all_ohlcv, date_t), avg_vols, date_t) if r['in_wl'] and r.get('vol_kering')],
    'TTx': lambda all_ohlcv, avg_vols, date_t: [
        r for r in scan_ttx(all_ohlcv, avg_vols, date_t) if r['in_wl'] and r.get('priority') == 0],
    'P1': lambda all_ohlcv, avg_vols, date_t: [
        r for r in scan_p1(truncate_ohlcv_to_date(all_ohlcv, date_t), avg_vols, date_t) if r['in_wl']],
    'Divergen': lambda all_ohlcv, avg_vols, date_t: [
        r for r in scan_divergen(truncate_ohlcv_to_date(all_ohlcv, date_t), avg_vols, date_t) if r['in_wl']],
}


def build_trackrecord(all_ohlcv, all_dates, max_hold=5, pattern='StockPick'):
    """
    Hitung track record sebuah pola dari semua data historis.
    - Entry: emiten lolos pola tsb di hari T
    - Hasil: High tertinggi T+1 s/d T+5
    - Gain%: (Max High - Close Entry) / Close Entry * 100
    """
    import numpy as np

    get_entries = PATTERN_TRACKRECORD_CONFIG.get(pattern, PATTERN_TRACKRECORD_CONFIG['StockPick'])

    # Buat dummy avg_vols dari semua data
    avg_vols = {}
    for code, bars in all_ohlcv.items():
        vols = [b.get('V',0) for b in bars if b.get('V',0) > 0]
        avg_vols[code] = float(np.mean(vols)) if vols else 1.0

    records = []
    # Loop setiap tanggal kecuali 5 terakhir (belum ada data hasil)
    dates_sorted = sorted(all_dates)

    for i, date_t in enumerate(dates_sorted):
        # Scan pola di hari T
        entries = get_entries(all_ohlcv, avg_vols, date_t)
        if not entries:
            continue

        # Tanggal T+1 s/d T+5
        future_dates = dates_sorted[i+1:i+1+max_hold]

        for r in entries:
            code = r['code']
            close_entry = r['close']
            bars = all_ohlcv.get(code, [])

            # Cari High tertinggi di T+1 s/d T+5
            max_high = 0
            max_high_date = None
            days_checked = 0
            for fd in future_dates:
                bar = next((b for b in bars if b['date'] == fd), None)
                if bar and bar.get('H'):
                    days_checked += 1
                    if bar['H'] > max_high:
                        max_high = bar['H']
                        max_high_date = fd

            # Hitung gain
            if max_high > 0 and close_entry > 0:
                gain = (max_high - close_entry) / close_entry * 100
            else:
                gain = None

            # Status
            if len(future_dates) == 0:
                status = '⏳ Running'
            elif days_checked < max_hold and len(future_dates) < max_hold:
                status = '⏳ Running'
            elif gain is None:
                status = '❓ No Data'
            elif gain >= 5:
                status = '✅ Profit'
            elif gain >= 0:
                status = '🟡 Tipis'
            else:
                status = '❌ Loss'

            records.append({
                'Tanggal Entry': date_t,
                'Code': code,
                'Close Entry': close_entry,
                'Max High (T+1~5)': int(max_high) if max_high else '-',
                'Max High Date': max_high_date or '-',
                'Gain%': round(gain, 2) if gain is not None else None,
                'Hold Days': days_checked,
                'Status': status,
            })

    return records


def build_trackrecord_summary(all_ohlcv, all_dates, max_hold=5):
    """Resume ringkas Win Rate semua pola sekaligus — dipakai buat tabel resume
    di atas tab TrackRecord, sebelum user pilih 1 pola untuk dilihat detail."""
    summary = []
    for pattern in PATTERN_TRACKRECORD_CONFIG:
        records = build_trackrecord(all_ohlcv, all_dates, max_hold=max_hold, pattern=pattern)
        if not records:
            summary.append({'Pola': pattern, 'Total Entry': 0, '✅ Profit': 0, '🟡 Tipis': 0,
                             '❌ Loss': 0, '⏳ Running': 0, 'Win Rate': '-', 'Avg Gain%': '-'})
            continue
        total = len(records)
        profit = sum(1 for r in records if r['Status'] == '✅ Profit')
        tipis  = sum(1 for r in records if r['Status'] == '🟡 Tipis')
        loss   = sum(1 for r in records if r['Status'] == '❌ Loss')
        running = sum(1 for r in records if r['Status'] == '⏳ Running')
        done = profit + tipis + loss
        winrate = round(profit / done * 100, 1) if done > 0 else 0
        gains = [r['Gain%'] for r in records if r['Gain%'] is not None]
        avg_gain = round(sum(gains)/len(gains), 2) if gains else 0
        summary.append({
            'Pola': pattern, 'Total Entry': total, '✅ Profit': profit, '🟡 Tipis': tipis,
            '❌ Loss': loss, '⏳ Running': running,
            'Win Rate': f"{winrate}%" if done > 0 else '-',
            'Avg Gain%': f"{avg_gain:+.2f}%" if gains else '-',
        })
    summary.sort(key=lambda x: x['Total Entry'], reverse=True)
    return summary


def build_sp_autosp_breakout(all_ohlcv, all_dates, lookback_days=30, gain_threshold=5.0):
    """Rangkuman saham yang muncul di StockPick dan/atau AutoSP pada hari T,
    lalu High T+1 (keesokan hari trading) mencapai >= gain_threshold% dari Close T.
    Menandai sumbernya (SP / AutoSP / SP+AutoSP) beserta badge pola dari AutoSP."""
    avg_vols = {}
    for code, bars in all_ohlcv.items():
        vols = [b.get('V',0) for b in bars if b.get('V',0) > 0]
        avg_vols[code] = float(np.mean(vols)) if vols else 1.0

    dates_sorted = sorted(all_dates)
    scan_dates = dates_sorted[-(lookback_days+1):] if lookback_days else dates_sorted

    results = []
    for i, date_t in enumerate(dates_sorted):
        if date_t not in scan_dates: continue
        if i+1 >= len(dates_sorted): continue
        date_t1 = dates_sorted[i+1]

        ohlcv_t = truncate_ohlcv_to_date(all_ohlcv, date_t)
        sp_list_t = [r for r in scan_stockpick(ohlcv_t, avg_vols, date_t) if r['in_wl']]
        boa_full_t, boa_near_t = scan_boa(ohlcv_t, avg_vols, date_t)
        p1_list_t = scan_p1(ohlcv_t, avg_vols, date_t)
        p3_list_t = scan_p3(ohlcv_t, avg_vols, date_t)
        ol_list_t = scan_ol_seq(ohlcv_t, avg_vols, date_t)
        sv_list_t = scan_sv(ohlcv_t, avg_vols, date_t)
        alert_list_t = scan_alert(ohlcv_t, avg_vols, date_t)
        bos_list_t = scan_bos(ohlcv_t, avg_vols, date_t)
        boh_list_t = scan_boh(ohlcv_t, avg_vols, date_t)
        ttx_list_t = scan_ttx(all_ohlcv, avg_vols, date_t)
        div_list_t = scan_divergen(ohlcv_t, avg_vols, date_t)
        autosp_list_t = auto_stockpick(boa_full_t, boa_near_t, p1_list_t, p3_list_t, ol_list_t,
                                        sv_list_t, alert_list_t, sp_list_t, bos_list_t, boh_list_t,
                                        ttx_list_t, ohlcv_t, date_t, div_list_t)

        candidates = {}
        for r in sp_list_t:
            c = candidates.setdefault(r['code'], {'code': r['code'], 'close': r['close'], 'sources': set(), 'badges': []})
            c['sources'].add('SP')
        for r in autosp_list_t:
            c = candidates.setdefault(r['code'], {'code': r['code'], 'close': r['close'], 'sources': set(), 'badges': []})
            c['sources'].add('AutoSP')
            c['badges'] = r.get('pola', [])

        for code, info in candidates.items():
            bars = all_ohlcv.get(code, [])
            bar_t1 = next((b for b in bars if b['date'] == date_t1), None)
            close_entry = info['close']
            if not bar_t1 or not bar_t1.get('H') or not close_entry: continue
            gain = (bar_t1['H'] - close_entry) / close_entry * 100
            if gain >= gain_threshold:
                results.append({
                    'Tanggal Entry': date_t, 'Code': code,
                    'Sumber': ' + '.join(sorted(info['sources'])),
                    'Badge': ', '.join(info['badges']) if info['badges'] else '-',
                    'Close Entry': close_entry,
                    'Tanggal +1': date_t1, 'High T+1': int(bar_t1['H']),
                    'Gain%': round(gain, 2),
                })
    results.sort(key=lambda x: (x['Tanggal Entry'], x['Gain%']), reverse=True)
    return results


def truncate_ohlcv_to_date(all_ohlcv, date_t):
    """Potong all_ohlcv supaya bar TERAKHIR tiap kode = date_t. WAJIB dipakai sebelum
    manggil scan_* function untuk tanggal HISTORIS (bukan hari ini) — karena hampir
    semua scan_* function syaratkan bars[-1]['date']==target, yang cuma valid kalau
    target = tanggal paling baru di seluruh dataset. Tanpa truncate, scan untuk
    tanggal lama akan selalu gagal (list kosong)."""
    truncated = {}
    for code, bars in all_ohlcv.items():
        idx = None
        for i, b in enumerate(bars):
            if b['date'] == date_t:
                idx = i
                break
        if idx is not None:
            truncated[code] = bars[:idx+1]
    return truncated


def get_pattern_badges_for_date(all_ohlcv, avg_vols, date_t):
    """Hitung semua pola yang lolos di tanggal date_t (histori), return {code: [label,...]}.
    Dipakai buat nampilin badge pola 'saat entry dibuat' di tabel Trading Log."""
    result = {}
    def _add(codes_list, label):
        for r in codes_list:
            result.setdefault(r['code'], []).append(label)
    try:
        ohlcv_t = truncate_ohlcv_to_date(all_ohlcv, date_t)
        boa_full_t, boa_near_t = scan_boa(ohlcv_t, avg_vols, date_t)
        _add(boa_full_t, 'BOA✅')
        _add(boa_near_t, 'BOA~')
        _add(scan_p1(ohlcv_t, avg_vols, date_t), 'P1')
        _add([r for r in scan_p3(ohlcv_t, avg_vols, date_t) if 'B' in str(r.get('trigger',''))], 'P3')
        _add([r for r in scan_ol_seq(ohlcv_t, avg_vols, date_t) if r.get('days')=='3H'], 'OL3')
        _add(scan_sv(ohlcv_t, avg_vols, date_t), 'SV')
        _add(scan_alert(ohlcv_t, avg_vols, date_t), 'Alert')
        _add([r for r in scan_bos(ohlcv_t, avg_vols, date_t) if r.get('entry','') != 'Tunggu'], 'BOS')
        _add([r for r in scan_boh(ohlcv_t, avg_vols, date_t) if r.get('vol_kering')], 'BOH')
        _add([r for r in scan_ttx(all_ohlcv, avg_vols, date_t) if r.get('priority') == 0], 'TTx🔔')
        _add([r for r in scan_stockpick(ohlcv_t, avg_vols, date_t) if r['in_wl']], 'SP')
        _add([r for r in scan_divergen(ohlcv_t, avg_vols, date_t) if r['in_wl']], 'Div')
    except Exception:
        pass
    return result


_ENTRY_BADGE_COLORS = {
    'BOA✅': ('#EEEDFE','#3C3489'), 'BOA~': ('#EEEDFE','#534AB7'),
    'P1': ('#FCEBEB','#791F1F'), 'P3': ('#FBEAF0','#4B1528'), 'OL3': ('#EAF3DE','#27500A'),
    'SV': ('#FFF6DA','#7A5B00'), 'Alert': ('#FDE8E8','#8B1E1E'),
    'BOS': ('#E1F5EE','#085041'), 'BOH': ('#FAECE7','#712B13'),
    'TTx🔔': ('#FAEEDA','#633806'), 'SP': ('#E6F1FB','#0C447C'), 'Div': ('#E3F8EF','#0F6B4C'),
}


def render_entry_badges(labels):
    if not labels:
        return '<span style="color:#888;font-size:11px">-</span>'
    html = ''
    for l in labels:
        bg, fg = _ENTRY_BADGE_COLORS.get(l, ('#D3D1C7','#2C2C2A'))
        html += f'<span style="background:{bg};color:{fg};font-size:9px;font-weight:700;padding:1px 5px;border-radius:4px;margin-right:2px">{l}</span>'
    return html


def build_vol_sparkline(code, all_ohlcv):
    """Vol sparkline global — bisa dipanggil dari tab mana saja."""
    bars_s = all_ohlcv.get(code, [])
    vols_s = [b.get('V', 0) for b in bars_s[-14:]]
    if len(vols_s) < 3: return '—'
    mx_s = max(vols_s) if max(vols_s) > 0 else 1
    parts_s = []
    for i_s, v_s in enumerate(vols_s):
        h_s = max(2, int(v_s / mx_s * 18))
        col_s = '#1D9E75' if i_s == 0 or v_s >= vols_s[i_s-1] else '#EF9F27'
        parts_s.append('<span style="display:inline-block;width:3px;height:' + str(h_s) + 'px;background:' + col_s + ';border-radius:1px;margin-right:1px;vertical-align:bottom"></span>')
    return '<div style="display:flex;align-items:flex-end;height:20px">' + ''.join(parts_s) + '</div>'


def build_price_sparkline(code, all_ohlcv, n_days=14):
    """Price/Close sparkline global — bisa dipanggil dari tab mana saja."""
    bars_s = all_ohlcv.get(code, [])
    closes_s = [b['C'] for b in bars_s[-n_days:] if b.get('C')]
    if len(closes_s) < 3: return '—'
    mn_s, mx_s = min(closes_s), max(closes_s)
    rng_s = mx_s - mn_s if mx_s > mn_s else 1
    parts_s = []
    for i_s, c_s in enumerate(closes_s):
        h_s = max(3, int((c_s - mn_s) / rng_s * 18))
        col_s = '#1D9E75' if i_s == 0 or c_s >= closes_s[i_s-1] else '#f87171'
        parts_s.append('<span style="display:inline-block;width:3px;height:' + str(h_s) + 'px;background:' + col_s + ';border-radius:1px;margin-right:1px;vertical-align:bottom"></span>')
    return '<div style="display:flex;align-items:flex-end;height:20px">' + ''.join(parts_s) + '</div>'

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
        sumber = st.radio("📂 Sumber Data", ["📁 Folder data/", "⬆️ Upload Manual"], index=0)
        if sumber == "⬆️ Upload Manual":
            uploaded_files = st.file_uploader(
                "Upload File XLS dari RTI",
                type=['xls','xlsx'],
                accept_multiple_files=True,
                help="Bisa upload banyak file sekaligus"
            )
        else:
            uploaded_files = None
            st.caption("📁 Membaca dari folder `data/` di GitHub")
        st.divider()
        show_only_wl = st.toggle("★ Hanya WL", value=True)
        st.divider()
        # Miracle Cuan — sekarang jadi tab di dalam app (lihat tab "🌟 Miracle Cuan")
        if st.session_state.get('miracle_data'):
            st.caption("🌟 Miracle Cuan: data SP hari ini sudah terisi (lihat tab)")
        else:
            st.caption("🌟 Miracle Cuan: buka tab Stockpick dulu untuk data SP")
        st.divider()

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
    folder_files = __import__('glob').glob('data/*.xls') + __import__('glob').glob('data/*.xlsx')
    if not uploaded_files and not folder_files:
        c1,c2,c3 = st.columns([1,2,1])
        with c2:
            st.markdown("""
            <div style="text-align:center;padding:60px 20px;">
                <div style="font-size:5rem;">📂</div>
                <h2 style="color:#00d4aa;">Tidak ada data ditemukan</h2>
                <p style="color:#aaa;">Upload file .xls di sidebar,<br>
                atau taruh file XLS di folder <b>data/</b> di GitHub</p>
            </div>
            """, unsafe_allow_html=True)
            st.info("**Cara pakai:**\n1. Klik Browse files di sidebar\n2. Pilih file .xls dari RTI\n3. Hasil scan muncul otomatis")
        return

    # ── Process ───────────────────────────────────────────────────────────────
    with st.spinner("🔄 Memproses & scan semua pola..."):
        if uploaded_files:
            all_ohlcv = load_uploaded(uploaded_files)
        else:
            all_ohlcv = load_from_folder_cached("data", get_data_folder_signature("data"))
        if not all_ohlcv:
            st.error("Tidak ada data yang terbaca. Cek format file."); return

        dates = []
        all_dates = set()
        for bars in all_ohlcv.values():
            if bars:
                dates.append(bars[-1]['date'])
                for b in bars: all_dates.add(b['date'])
        target = max(dates) if dates else None
        if not target:
            st.error("Tidak bisa baca tanggal."); return

        avg_vols = {code: get_avg_vol(bars) for code,bars in all_ohlcv.items()}
        data_today = {c:b for c,b in all_ohlcv.items() if b and b[-1]['date']==target}

        # ── Auto-update TP/SL ke Google Sheet Trading Log ──
        # Dikirim ulang tiap kali data (Close/High/Low) hari ini berubah — bukan cuma
        # sekali per tanggal — supaya upload intraday berikutnya (11:59, 14:30, 16:10)
        # tetap ter-refresh, bukan hanya nempel ke snapshot pertama hari itu.
        _updates = [
            {"code": c, "high": b[-1].get('H'), "low": b[-1].get('L'), "close": b[-1].get('C')}
            for c, b in data_today.items()
            if b[-1].get('H') is not None and b[-1].get('L') is not None
        ]
        import hashlib as _hashlib
        _fingerprint = _hashlib.md5(
            str(sorted((u['code'], u['high'], u['low'], u['close']) for u in _updates)).encode()
        ).hexdigest()[:12]
        _tpsl_key = f"tpsl_sent_{target}_{_fingerprint}"
        if not st.session_state.get(_tpsl_key):
            try:
                import requests as _requests
                if _updates:
                    _resp = _requests.post(
                        "https://script.google.com/macros/s/AKfycbyz0DcMbs7VGhkinpxt0D-vnNG6WOkywzIMOMLciQpcNeN-6C4aaTaTwTRC_Rto56Ym/exec",
                        json={"action": "bulk_update_tpsl", "date": target, "updates": _updates},
                        timeout=15
                    )
                    st.session_state["tpsl_last_result"] = (
                        f"✅ Cek TP/SL {target}: {_resp.json().get('result',{})}" if _resp.ok
                        else f"⚠️ Update TP/SL gagal (HTTP {_resp.status_code})"
                    )
                st.session_state[_tpsl_key] = True
            except Exception as _e:
                st.session_state["tpsl_last_result"] = f"⚠️ Update TP/SL gagal: {_e}"

        dt = datetime.strptime(target,'%Y-%m-%d')
        delta = 3 if dt.weekday()==4 else 1
        next_date = (dt+timedelta(days=delta)).strftime('%Y-%m-%d')

        # ── Cache seluruh pipeline scan pola berdasarkan "tanda tangan" data ──
        # Streamlit rerun SELURUH script tiap ada interaksi apapun (klik tab, ketik
        # di search box, dst). Tanpa cache ini, ke-11 scan pola dihitung ulang dari
        # nol tiap kali — bahkan cuma buka tab "Cari Saham" yang sebenarnya cuma
        # butuh lookup dari hasil yang SUDAH dihitung. Cache hanya recompute kalau
        # data screener beneran berubah (upload baru).
        # _SCAN_CACHE_VERSION dinaikkan tiap kali struktur _sp_cache berubah (nambah
        # key baru dsb) — biar app yang baru di-redeploy tapi datanya SAMA (jadi
        # signature sama) tidak kepakai cache LAMA yang strukturnya beda (bisa bikin
        # KeyError). Kalau nambah field baru ke _sp_cache lagi nanti, naikkan angka ini.
        _SCAN_CACHE_VERSION = 2
        _scan_sig = (_SCAN_CACHE_VERSION, len(all_dates), target, len(all_ohlcv))
        _cache_ok = (st.session_state.get('_scan_pipeline_sig') == _scan_sig
                     and '_scan_pipeline_cache' in st.session_state)
        if _cache_ok:
            _required_keys = {'boa_full','boa_near','p1_list','p3_list','ol_list','sv_list',
                               'alert_list','clean','sp_list','bos_list','boh_list','div_list',
                               'ttx_list','ara_list','auto_sp'}
            if not _required_keys.issubset(st.session_state['_scan_pipeline_cache'].keys()):
                _cache_ok = False
        if not _cache_ok:
            _sp_cache = {}
            _sp_cache['boa_full'], _sp_cache['boa_near'] = scan_boa(all_ohlcv, avg_vols, target)
            _sp_cache['p1_list']   = scan_p1(all_ohlcv, avg_vols, target)
            _sp_cache['p3_list']   = scan_p3(all_ohlcv, avg_vols, target)
            _sp_cache['ol_list']   = scan_ol_seq(all_ohlcv, avg_vols, target)
            _sp_cache['sv_list']   = scan_sv(all_ohlcv, avg_vols, target)
            _sp_cache['alert_list']= scan_alert(all_ohlcv, avg_vols, target)
            _sp_cache['clean']     = scan_bersih(all_ohlcv, avg_vols, target,
                                    _sp_cache['p1_list'], _sp_cache['p3_list'], _sp_cache['boa_full'], _sp_cache['boa_near'], _sp_cache['sv_list'])
            _sp_cache['sp_list']   = scan_stockpick(all_ohlcv, avg_vols, target)
            _sp_cache['bos_list']  = scan_bos(all_ohlcv, avg_vols, target)
            _sp_cache['boh_list']  = scan_boh(all_ohlcv, avg_vols, target)
            _sp_cache['div_list']  = scan_divergen(all_ohlcv, avg_vols, target)
            _sp_cache['ttx_list']  = scan_ttx(all_ohlcv, avg_vols, target)
            _sp_cache['ara_list']  = scan_ara(all_ohlcv, avg_vols, target)
            _sp_cache['auto_sp']   = auto_stockpick(_sp_cache['boa_full'], _sp_cache['boa_near'], _sp_cache['p1_list'],
                                    _sp_cache['p3_list'], _sp_cache['ol_list'], _sp_cache['sv_list'], _sp_cache['alert_list'],
                                    _sp_cache['sp_list'], _sp_cache['bos_list'], _sp_cache['boh_list'], _sp_cache['ttx_list'],
                                    all_ohlcv, target, _sp_cache['div_list'])
            st.session_state['_scan_pipeline_cache'] = _sp_cache
            st.session_state['_scan_pipeline_sig'] = _scan_sig
        _sp_cache = st.session_state['_scan_pipeline_cache']
        boa_full   = _sp_cache['boa_full'];   boa_near = _sp_cache['boa_near']
        p1_list    = _sp_cache['p1_list'];    p3_list  = _sp_cache['p3_list']
        ol_list    = _sp_cache['ol_list'];    sv_list  = _sp_cache['sv_list']
        alert_list = _sp_cache['alert_list']; clean    = _sp_cache['clean']
        sp_list    = _sp_cache['sp_list'];    bos_list = _sp_cache['bos_list']
        boh_list   = _sp_cache['boh_list'];   div_list = _sp_cache['div_list']
        ttx_list   = _sp_cache['ttx_list'];   auto_sp  = _sp_cache['auto_sp']
        ara_list   = _sp_cache['ara_list']

        # ── Auto-log semua saham StockPick ke Google Sheet "StockPick Log" ──
        # Trading Log ke-2: otomatis, tanpa perlu klik Simpan manual di kalkulator.
        # TP1 default 5%, TP2 default 13%, SL default 5% (dari Close hari itu).
        # HANYA jalan kalau data hari ini sudah dari snapshot CLOSING (jam 16:10 ke atas)
        # — bukan dari upload intraday (10:00/11:59/14:30), supaya Close yang tercatat
        # adalah harga penutupan resmi, bukan harga tengah hari yang masih bisa berubah.
        _today_bars_sample = [b[-1] for b in data_today.values() if b]
        _today_time = next((b.get('T','') for b in _today_bars_sample if b.get('T')), '')
        _is_closing_snapshot = _today_time >= '16:10:00'
        st.session_state["sp_log_time_check"] = (
            f"Data jam {_today_time or '?'} — {'✅ closing, StockPick Log diproses' if _is_closing_snapshot else '⏳ belum closing (butuh ≥16:10), StockPick Log ditunda'}"
        )
        if _is_closing_snapshot:
            try:
                import requests as _requests_sp
                _sp_wl_auto = [r for r in sp_list if r.get('in_wl')]
                _sp_entries = []
                for _r in _sp_wl_auto:
                    _close = _r['close']
                    _sp_entries.append({
                        "tanggal": target, "code": _r['code'], "close_entry": _close,
                        "tp1_pct": 5, "harga_tp1": round(_close * 1.05),
                        "tp2_pct": 13, "harga_tp2": round(_close * 1.13),
                        "use_sl": True, "sl_pct": 5, "harga_sl": round(_close * 0.95),
                    })
                _sp_fingerprint = _hashlib.md5(
                    str(sorted((e['code'], e['close_entry']) for e in _sp_entries)).encode()
                ).hexdigest()[:12]
                _sp_log_key = f"sp_log_sent_{target}_{_sp_fingerprint}"
                if not st.session_state.get(_sp_log_key) and _sp_entries:
                    _resp_sp = _requests_sp.post(
                        "https://script.google.com/macros/s/AKfycbyz0DcMbs7VGhkinpxt0D-vnNG6WOkywzIMOMLciQpcNeN-6C4aaTaTwTRC_Rto56Ym/exec",
                        json={"action": "bulk_add_entries", "sheet": "StockPick Log", "entries": _sp_entries},
                        timeout=20
                    )
                    st.session_state["sp_log_last_result"] = (
                        f"✅ StockPick Log {target}: {_resp_sp.json().get('result',{})}" if _resp_sp.ok
                        else f"⚠️ StockPick Log gagal (HTTP {_resp_sp.status_code})"
                    )
                    st.session_state[_sp_log_key] = True
            except Exception as _e_sp:
                st.session_state["sp_log_last_result"] = f"⚠️ StockPick Log gagal: {_e_sp}"

        # ── Auto-update TP/SL untuk StockPick Log juga (pakai data_today yang sama) ──
        # max_hold_days=10: kalau sudah 10 hari bursa & TP2 belum kena, otomatis
        # dismiss di hari ke-11 (Apps Script yang eksekusi logic-nya).
        if _updates:
            try:
                import requests as _requests_upd2
                _resp_sp2 = _requests_upd2.post(
                    "https://script.google.com/macros/s/AKfycbyz0DcMbs7VGhkinpxt0D-vnNG6WOkywzIMOMLciQpcNeN-6C4aaTaTwTRC_Rto56Ym/exec",
                    json={"action": "bulk_update_tpsl", "sheet": "StockPick Log", "date": target, "updates": _updates, "max_hold_days": 10},
                    timeout=15
                )
            except Exception:
                pass

        # ── Build data OHLCV untuk Miracle Cuan (embed langsung, bukan URL luar) ──
        try:
            _sp_wl_mc = sorted([r for r in sp_list if r.get('in_wl')], key=lambda r: r['code'])
            _sp_data_mc = ','.join([f"{r['code']}:{r['close']}" for r in _sp_wl_mc])
            _ohlcv_parts_mc = []
            for _r in _sp_wl_mc:
                _c = _r['code']
                _b = all_ohlcv.get(_c, [])[-14:]
                if len(_b) < 3: continue
                _bs = '|'.join([
                    f"{b['date'][5:]}:{int(b.get('O') or b.get('C',0))}:{int(b.get('H',0))}:{int(b.get('L') or b.get('C',0))}:{int(b.get('C',0))}:{int(b.get('V',0))}"
                    for b in _b if b.get('C')
                ])
                if _bs: _ohlcv_parts_mc.append(f"{_c}~{_bs}")
            _ohlcv_str_mc = ';'.join(_ohlcv_parts_mc)
            st.session_state['miracle_data'] = _sp_data_mc
            st.session_state['miracle_ohlcv'] = _ohlcv_str_mc
        except: pass

    # ── Info bar ──────────────────────────────────────────────────────────────
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("📅 Data",   target)
    c2.metric("🎯 Target", next_date)
    c3.metric("📊 File",   f"{len(uploaded_files) if uploaded_files else len(glob.glob('data/*.xls')+glob.glob('data/*.xlsx'))} file")
    c4.metric("🏢 Saham",  f"{len(data_today)} saham")
    if st.session_state.get("tpsl_last_result"):
        st.caption(st.session_state["tpsl_last_result"])
    if st.session_state.get("sp_log_time_check"):
        st.caption(f"📌 StockPick Log: {st.session_state['sp_log_time_check']}")

    # ── Summary chips ─────────────────────────────────────────────────────────
    cols = st.columns(5)
    chips = [
        ("🚀 BOS",      len([r for r in bos_list   if r['in_wl'] and r['entry']!='Tunggu']), "#f59e0b"),
        ("📈 BOH",      len([r for r in boh_list   if r['in_wl']]), "#06b6d4"),
        ("🔀 Divergen", len([r for r in div_list   if r['in_wl']]), "#22d3a8"),
        ("⏰ TTx🔔",    len([r for r in ttx_list   if r['priority']==0]), "#e879f9"),
        ("🛒 Stockpick",len([r for r in sp_list    if r['in_wl']]), "#a78bfa"),
    ]
    for col,(label,val,color) in zip(cols,chips):
        col.markdown(f"""<div style="background:#1e1e2e;border:1px solid #333;border-radius:8px;
            padding:10px;text-align:center;">
            <div style="font-size:1.5rem;font-weight:bold;color:{color};">{val}</div>
            <div style="font-size:0.72rem;color:#aaa;">{label}</div>
        </div>""", unsafe_allow_html=True)

    # ── Heatmap Koreksi (T-2, T-3, T-4) ────────────────────────────────
    dates_sorted_hdr = sorted(all_dates)
    tidx = dates_sorted_hdr.index(target) if target in dates_sorted_hdr else -1
    lookback_hdr = dates_sorted_hdr[max(0, tidx-4):tidx]  # T-4 s/d T-1

    heatmap_kandidat = {}
    for d_hdr in lookback_hdr:
        d_pos = lookback_hdr.index(d_hdr)
        if d_pos == 0: continue  # butuh hari sebelumnya untuk vol comparison
        d_prev = lookback_hdr[d_pos - 1]

        for code, bars_hdr in all_ohlcv.items():
            if code not in ALL_WL: continue
            if code in heatmap_kandidat: continue  # ambil yang paling awal

            bar_d    = next((b for b in bars_hdr if b['date'] == d_hdr), None)
            bar_prev = next((b for b in bars_hdr if b['date'] == d_prev), None)
            bar_today = next((b for b in bars_hdr if b['date'] == target), None)

            if not bar_d or not bar_prev or not bar_today: continue
            if not bar_d.get('C') or not bar_d.get('P') or bar_d['P'] <= 0: continue

            # Kriteria 1: Chg% 3%-7% di hari itu
            chg_d = (bar_d['C'] - bar_d['P']) / bar_d['P'] * 100
            if not (3.0 <= chg_d <= 7.0): continue

            # Kriteria 2: Volume hari itu > volume sebelumnya
            vol_d    = bar_d.get('V', 0)
            vol_prev = bar_prev.get('V', 0)
            if vol_prev <= 0 or vol_d <= vol_prev: continue

            # Kriteria 3: Hari ini Close/Prev <= 2% (koreksi/flat)
            if not bar_today.get('C') or not bar_today.get('P') or bar_today['P'] <= 0: continue
            chg_today = (bar_today['C'] - bar_today['P']) / bar_today['P'] * 100
            if chg_today > 2.0: continue

            # Gain dari entry ke hari ini
            gain_hdr = (bar_today['C'] - bar_d['C']) / bar_d['C'] * 100
            day_ago = tidx - dates_sorted_hdr.index(d_hdr)

            heatmap_kandidat[code] = {
                'chg_entry': round(chg_d, 1),
                'chg_today': round(chg_today, 1),
                'gain': round(gain_hdr, 1),
                'day_ago': day_ago,
                'entry_close': int(bar_d['C']),
                'curr_close': int(bar_today['C']),
                'entry_date': d_hdr,
            }

    if heatmap_kandidat:
        def hdr_style(gain):
            if gain >= 3:   return '#5DCAA5','#04342C'
            if gain >= 0:   return '#9FE1CB','#085041'
            if gain > -3:   return '#EF9F27','#412402'
            return '#F0997B','#4A1B0C'

        # Cek: apakah saham ini juga masuk kriteria StockPick PADA HARI ENTRY-nya (T-2/3/4)?
        def was_stockpick_on(code, entry_date):
            bars_full = all_ohlcv.get(code, [])
            idx = next((i for i,b in enumerate(bars_full) if b['date']==entry_date), None)
            if idx is None or idx < 2: return False
            bars_trunc = bars_full[:idx+1]
            avg_vol = avg_vols.get(code, 1.0)
            try:
                res = scan_stockpick({code: bars_trunc}, {code: avg_vol}, entry_date)
                return len(res) > 0
            except Exception:
                return False

        for code, info in heatmap_kandidat.items():
            info['was_sp'] = was_stockpick_on(code, info['entry_date'])

        # Kumpulkan pola aktif per saham hari ini
        active_pola = {}
        def add_pola(lst, pola_name, key='in_wl'):
            for r in lst:
                if not r.get('in_wl'): continue
                c = r['code']
                if c not in active_pola: active_pola[c] = []
                if pola_name not in active_pola[c]:
                    active_pola[c].append(pola_name)
        add_pola(boa_full, 'BOA✅')
        add_pola(boa_near, 'BOA~')
        add_pola([r for r in bos_list if r.get('entry','')!='Tunggu'], 'BOS')
        add_pola([r for r in boh_list if r.get('vol_kering')], 'BOH')
        add_pola([r for r in ttx_list if r.get('priority')==0], 'TTx🔔')
        add_pola([r for r in p1_list], 'P1')
        add_pola(sp_list, 'SP')
        add_pola(div_list, 'Div')

        POLA_COLORS = {
            'BOA✅': '#CECBF6', 'BOA~': '#CECBF6',
            'BOS': '#9FE1CB', 'BOH': '#F5C4B3',
            'TTx🔔': '#FAC775', 'P1': '#F4C0D1', 'SP': '#B5D4F4', 'Div': '#B8EFD9',
        }

        hm_hdr_parts = []
        for code, info in sorted(heatmap_kandidat.items(), key=lambda x: -x[1]['gain']):
            bg, fg = hdr_style(info['gain'])
            sign = '+' if info['gain'] > 0 else ''
            sign_t = '+' if info['chg_today'] > 0 else ''

            # Badge pola
            polas = list(active_pola.get(code, []))
            if info.get('was_sp'):
                polas.append(f"SP@T-{info['day_ago']}")
            badge_html = ''
            if polas:
                for p in polas:
                    pc = '#FFD166' if p.startswith('SP@T-') else POLA_COLORS.get(p, '#D3D1C7')
                    badge_html += '<span style="background:' + pc + ';color:#2C2C2A;font-size:9px;font-weight:700;padding:1px 5px;border-radius:4px;margin-right:2px;">' + p + '</span>'
                badge_html = '<div style="margin-top:4px;display:flex;flex-wrap:wrap;justify-content:center;gap:2px;">' + badge_html + '</div>'

            hm_hdr_parts.append(
                '<div style="background:' + bg + ';color:' + fg + ';border:1px solid rgba(128,128,128,0.2);'
                'border-radius:8px;padding:6px 10px;min-width:72px;text-align:center;cursor:pointer;">'
                '<div style="font-size:12px;font-weight:700;">' + code + '</div>'
                '<div style="font-size:11px;font-weight:500;">' + sign + str(info['gain']) + '%</div>'
                '<div style="font-size:10px;opacity:0.8;">T-' + str(info['day_ago']) + ' @' + str(info['entry_close']) + '</div>'
                '<div style="font-size:10px;opacity:0.75;">hari ini ' + sign_t + str(info['chg_today']) + '%</div>'
                + badge_html +
                '</div>'
            )
        hm_hdr_html = '<div style="display:flex;flex-wrap:wrap;gap:6px;">' + ''.join(hm_hdr_parts) + '</div>'
        st.markdown(f"**Pantau Koreksi — {len(heatmap_kandidat)} saham** (naik 3–7% + vol naik di T-2/3/4, hari ini ≤2%)")
        st.html(hm_hdr_html)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_labels = ["🧹 Scan Bersih","🎯 BOA","📉 P1","🔄 P3","🕯️ OLseq","💰 SV","🚨 Alert","🚀 BOS","📈 BOH","🔀 Divergen","⏰ TTx","⭐ AutoSP","🛒 Stockpick","📋 TrackRecord","🌟 Miracle Cuan","🔍 Cari Saham","🔺 ARA","📡 Cek Cepat"]
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
        only_lowv = st.checkbox("🔵 Hanya tampilkan LowV", key='sv_only_lowv')
        if only_lowv:
            lst = [r for r in lst if r.get('low_v')]
        if lst:
            sv_rows_html = []
            for r in lst:
                cc = '#4ade80' if r['chg'] > 0 else ('#f87171' if r['chg'] < 0 else '#EF9F27')
                sc = '+' if r['chg'] > 0 else ''
                candle = '+'.join(x for x in ['OL' if r['ol'] else '','Doji' if r['doji'] else '','CAvg' if r['cavg'] else ''] if x) or '-'
                lowv_badge = '<span style="background:#DBEAFE;color:#1E3A8A;font-size:10px;font-weight:700;padding:3px 8px;border-radius:6px;white-space:nowrap">🔵 LowV</span>' if r.get('low_v') else ''
                best_txt = f"{r['best']['date']}+{r['best']['hvp']:.0f}%(Rp{r['best']['val_b']:.2f}M)"
                sv_rows_html.append(
                    '<tr style="border-bottom:0.5px solid rgba(128,128,128,0.12)">'
                    '<td style="padding:7px 10px;font-size:12px;color:#fbbf24">' + ('★' if r['in_wl'] else '') + '</td>'
                    '<td style="padding:7px 10px;font-weight:600;font-size:13px">' + r['code'] + '</td>'
                    '<td style="padding:7px 10px;text-align:right;font-size:13px">' + str(r['close']) + '</td>'
                    '<td style="padding:7px 10px;text-align:right;color:' + cc + ';font-weight:500">' + sc + str(r['chg']) + '%</td>'
                    '<td style="padding:7px 10px;text-align:right;font-size:12px">' + f"{r['vol']:.2f}" + '</td>'
                    '<td style="padding:7px 10px;text-align:center;font-size:12px">' + str(r['n']) + '</td>'
                    '<td style="padding:7px 10px;font-size:11px;color:#888">' + best_txt + '</td>'
                    '<td style="padding:7px 10px;text-align:right;font-size:12px">' + f"{r['max_chg15']:+.1f}%" + '</td>'
                    '<td style="padding:7px 10px;text-align:center;font-size:11px">' + candle + '</td>'
                    '<td style="padding:7px 10px;text-align:center">' + lowv_badge + '</td>'
                    '</tr>'
                )
            sv_tbl_html = (
                '<table style="width:100%;border-collapse:collapse;font-size:13px">'
                '<thead><tr style="border-bottom:1px solid rgba(128,128,128,0.25)">'
                '<th style="padding:7px 10px;color:#666;font-weight:400;font-size:11px;width:24px">★</th>'
                '<th style="padding:7px 10px;text-align:left;color:#666;font-weight:400;font-size:11px">Code</th>'
                '<th style="padding:7px 10px;text-align:right;color:#666;font-weight:400;font-size:11px">Close</th>'
                '<th style="padding:7px 10px;text-align:right;color:#666;font-weight:400;font-size:11px">Chg%</th>'
                '<th style="padding:7px 10px;text-align:right;color:#666;font-weight:400;font-size:11px">Vol</th>'
                '<th style="padding:7px 10px;text-align:center;color:#666;font-weight:400;font-size:11px">Jml Spk</th>'
                '<th style="padding:7px 10px;text-align:left;color:#666;font-weight:400;font-size:11px">Best</th>'
                '<th style="padding:7px 10px;text-align:right;color:#666;font-weight:400;font-size:11px">mc15%</th>'
                '<th style="padding:7px 10px;text-align:center;color:#666;font-weight:400;font-size:11px">Candle</th>'
                '<th style="padding:7px 10px;text-align:center;color:#666;font-weight:400;font-size:11px">LowV</th>'
                '</tr></thead><tbody>' + ''.join(sv_rows_html) + '</tbody></table>'
            )
            st.html(sv_tbl_html)
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
    with tabs[12]:
        st.markdown("### 🛒 Stockpick Buy Close")

        # Parameter fixed (tidak perlu slider lagi)

        sp_wl  = [r for r in sp_list if r['in_wl']]
        sp_nwl = [r for r in sp_list if not r['in_wl']]
        st.markdown(
            "**Kriteria: H/P 2–12% | Vol>PrevVol | 8H bersih**"
            f"WL: **{len(sp_wl)}** | Non-WL: {len(sp_nwl)}"
        )

        lst = sp_wl if show_only_wl else sp_list

        # ── Heatmap Monitor Posisi Open ─────────────────────────────
        dates_sorted_sp = sorted(all_dates)
        target_idx_sp = dates_sorted_sp.index(target) if target in dates_sorted_sp else -1
        lookback_dates_sp = dates_sorted_sp[max(0, target_idx_sp-4):target_idx_sp]

        avg_vols_sp = {}
        for c_sp, b_sp in all_ohlcv.items():
            v_sp = [b.get('V',0) for b in b_sp if b.get('V',0)>0]
            avg_vols_sp[c_sp] = float(np.mean(v_sp)) if v_sp else 1.0

        monitor_sp = {}
        for d_sp in lookback_dates_sp:
            sp_d = scan_stockpick(all_ohlcv, avg_vols_sp, d_sp)
            for r_sp in sp_d:
                if not r_sp.get('in_wl'): continue
                code_sp = r_sp['code']
                if code_sp in monitor_sp: continue
                bars_sp = all_ohlcv.get(code_sp, [])
                entry_b = next((b for b in bars_sp if b['date']==d_sp), None)
                if not entry_b: continue
                entry_c = entry_b.get('C', 0)
                entry_h = entry_b.get('H', entry_c)
                today_b = next((b for b in bars_sp if b['date']==target), None)
                if not today_b or entry_c <= 0: continue
                curr_c = today_b.get('C', 0)
                curr_h = today_b.get('H', curr_c)
                if curr_h >= entry_h: continue
                gain_sp = (curr_c - entry_c) / entry_c * 100
                day_n_sp = lookback_dates_sp.index(d_sp) + 1
                monitor_sp[code_sp] = {
                'entry_date': d_sp[5:], 'entry_close': int(entry_c),
                'entry_high': int(entry_h), 'curr_close': int(curr_c),
                'gain': round(gain_sp,2), 'day_n': day_n_sp,
                }

        def gain_style_sp(g):
            if g >= 5:   return '#5DCAA5','#04342C'
            if g >= 1:   return '#9FE1CB','#085041'
            if g > -1:   return '#555552','#D3D1C7'
            if g > -5:   return '#F5C4B3','#4A1B0C'
            return '#D85A30','#FAECE7'

        if monitor_sp:
            hm_sp_parts = []
            for code_m, info_m in sorted(monitor_sp.items(), key=lambda x: -x[1]['gain']):
                bg_m, fg_m = gain_style_sp(info_m['gain'])
                sign_m = '+' if info_m['gain'] > 0 else ''
                hm_sp_parts.append(
                '<div style="background:' + bg_m + ';color:' + fg_m + ';border:1px solid rgba(128,128,128,0.2);'
                'border-radius:8px;padding:6px 10px;min-width:72px;text-align:center;">'
                '<div style="font-size:12px;font-weight:600;">' + code_m + '</div>'
                '<div style="font-size:12px;font-weight:500;">' + sign_m + str(info_m['gain']) + '%</div>'
                '<div style="font-size:10px;opacity:0.8;">H+' + str(info_m['day_n']) + ' | @' + str(info_m['entry_close']) + '</div>'
                '</div>'
                )
            hm_sp_html = '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;">' + ''.join(hm_sp_parts) + '</div>'
            st.markdown(f"**Monitor Posisi Open — {len(monitor_sp)} saham** (H-1 s/d H-4, belum tembus High entry)")
            st.html(hm_sp_html)
            st.divider()


        def make_sparkline(code):
            bars_s = all_ohlcv.get(code, [])
            cls_s = [b['C'] for b in bars_s[-14:] if b.get('C')]
            if len(cls_s) < 3: return '—'
            mn_s, mx_s = min(cls_s), max(cls_s)
            rng_s = mx_s - mn_s if mx_s > mn_s else 1
            parts_s = []
            for i_s, c_s in enumerate(cls_s):
                h_s = max(3, int((c_s - mn_s) / rng_s * 18))
                col_s = '#1D9E75' if i_s == 0 or c_s >= cls_s[i_s-1] else '#f87171'
                parts_s.append('<span style="display:inline-block;width:3px;height:' + str(h_s) + 'px;background:' + col_s + ';border-radius:1px;margin-right:1px;vertical-align:bottom"></span>')
            return '<div style="display:flex;align-items:flex-end;height:20px">' + ''.join(parts_s) + '</div>'

        def make_vol_sparkline(code):
            bars_s = all_ohlcv.get(code, [])
            vols_s = [b.get('V', 0) for b in bars_s[-14:]]
            if len(vols_s) < 3: return '—'
            mx_s = max(vols_s) if max(vols_s) > 0 else 1
            parts_s = []
            for i_s, v_s in enumerate(vols_s):
                h_s = max(2, int(v_s / mx_s * 18))
                col_s = '#1D9E75' if i_s == 0 or v_s >= vols_s[i_s-1] else '#EF9F27'
                parts_s.append('<span style="display:inline-block;width:3px;height:' + str(h_s) + 'px;background:' + col_s + ';border-radius:1px;margin-right:1px;vertical-align:bottom"></span>')
            return '<div style="display:flex;align-items:flex-end;height:20px">' + ''.join(parts_s) + '</div>'

        if lst:
            # Render tabel SP sebagai HTML — supaya sparkline bisa inline
            def vol_color(v, thresh_low=0.3, thresh_mid=0.7):
                if v < thresh_low: return '#4ade80'
                if v < thresh_mid: return '#fbbf24'
                return ''
            def volprev_color(v):
                if v > 1.5: return '#a78bfa'
                if v > 1.0: return '#fbbf24'
                return ''

            sp_rows_html = []
            for r in lst:
                chg = r.get('chg',0); hvp = r.get('hvp',0)
                vol = r.get('vol',0); vp = r.get('vol_vs_prev',0)
                mc = r.get('max_chg7',0); candle = r.get('candle','')
                spark = make_sparkline(r['code'])

                cc  = '#4ade80' if chg>0 else ('#f87171' if chg<0 else '#EF9F27')
                hc  = '#4ade80' if hvp>0 else ('#f87171' if hvp<0 else '#EF9F27')
                vc  = vol_color(vol)
                vpc = volprev_color(vp)
                sc  = '+' if chg>0 else ''; sh = '+' if hvp>0 else ''; sm = '+' if mc>0 else ''
                wl  = '★ ' if r.get('in_wl') else ''

                candle_color = '#4ade80' if 'Hijau' in candle else ('#f87171' if 'Merah' in candle else '#fbbf24')
                open_pct_r = r.get('open_pct', 0)
                oc1_badge = '<span style="background:#DCEBFF;color:#0C447C;font-size:10px;font-weight:700;padding:2px 6px;border-radius:4px">OC1</span>' if open_pct_r > 1 else ''

                sp_rows_html.append(
                    '<tr style="border-bottom:0.5px solid rgba(128,128,128,0.12)">'
                    '<td style="padding:7px 10px;font-size:12px;color:#fbbf24">' + wl + '</td>'
                    '<td style="padding:7px 10px;font-weight:600;font-size:13px">' + r['code'] + '</td>'
                    '<td style="padding:7px 10px;text-align:right;font-size:13px">' + str(r['close']) + '</td>'
                    '<td style="padding:7px 10px;text-align:right;color:' + cc + ';font-weight:500">' + sc + str(round(chg,2)) + '%</td>'
                    '<td style="padding:7px 10px;text-align:right;color:' + hc + ';font-weight:500">' + sh + str(round(hvp,2)) + '%</td>'
                    '<td style="padding:7px 10px;text-align:center">' + spark + '</td>'
                    '<td style="padding:7px 10px;text-align:center">' + make_vol_sparkline(r['code']) + '</td>'
                    '<td style="padding:7px 10px;text-align:right;color:' + vc + '">' + str(round(vol,2)) + '</td>'
                    '<td style="padding:7px 10px;text-align:right;color:' + vpc + ';font-weight:500">' + str(round(vp,2)) + 'x</td>'
                    '<td style="padding:7px 10px;text-align:right;font-size:12px;color:#888">' + sm + str(round(mc,2)) + '%</td>'
                    '<td style="padding:7px 10px;text-align:center;color:' + candle_color + ';font-size:12px">' + candle + '</td>'
                    '<td style="padding:7px 10px;text-align:center">' + oc1_badge + '</td>'
                    '</tr>'
                )

            sp_tbl_html = (
                '<table style="width:100%;border-collapse:collapse;font-size:13px">'
                '<thead><tr style="border-bottom:1px solid rgba(128,128,128,0.25)">'
                '<th style="padding:7px 10px;color:#666;font-weight:400;font-size:11px;width:24px">★</th>'
                '<th style="padding:7px 10px;text-align:left;color:#666;font-weight:400;font-size:11px">Code</th>'
                '<th style="padding:7px 10px;text-align:right;color:#666;font-weight:400;font-size:11px">Close</th>'
                '<th style="padding:7px 10px;text-align:right;color:#666;font-weight:400;font-size:11px">Chg%</th>'
                '<th style="padding:7px 10px;text-align:right;color:#666;font-weight:400;font-size:11px">H/P%</th>'
                '<th style="padding:7px 10px;text-align:center;color:#666;font-weight:400;font-size:11px">Trend 14H</th>'
                '<th style="padding:7px 10px;text-align:center;color:#666;font-weight:400;font-size:11px">Vol Trend</th>'
                '<th style="padding:7px 10px;text-align:right;color:#666;font-weight:400;font-size:11px">Vol/avg</th>'
                '<th style="padding:7px 10px;text-align:right;color:#666;font-weight:400;font-size:11px">Vol/Prev</th>'
                '<th style="padding:7px 10px;text-align:right;color:#666;font-weight:400;font-size:11px">mc8%</th>'
                '<th style="padding:7px 10px;text-align:center;color:#666;font-weight:400;font-size:11px">Candle</th>'
                '<th style="padding:7px 10px;text-align:center;color:#666;font-weight:400;font-size:11px">OC1</th>'
                '</tr></thead><tbody>' + ''.join(sp_rows_html) + '</tbody></table>'
            )
            st.html(sp_tbl_html)



            st.info(
                "**Cara baca:** Chg% = kenaikan close dari kemarin | "
                "H/P% = high dari kemarin (≤7% = tidak overbought) | "
                "Vol/Prev = volume hari ini vs kemarin (>1.0 = naik) | "
                "mc7% = max close 7H terakhir (harus <7%) | "
                "OC1 = Open hari ini >1% di atas Prev Close"
            )
        else:
            st.info("Tidak ada saham yang memenuhi kriteria Stockpick saat ini.")


    # Tab BOS
    with tabs[7]:
        lst = [r for r in bos_list if r['in_wl']] if show_only_wl else bos_list
        entry_lst = [r for r in lst if r['entry'] != 'Tunggu']
        wait_lst  = [r for r in lst if r['entry'] == 'Tunggu']
        st.markdown(f"**BOS — Break Out Soon | Window 7H Trading | WL: {len([r for r in bos_list if r['in_wl']])} | Total: {len(bos_list)}**")
        
        st.markdown("##### 🎯 Entry Signal")
        if entry_lst:
            rows = [{'★': '★' if r['in_wl'] else '', 'Code': r['code'],
                'Close': r['close'], 'Chg%': r['chg'], 'H/P%': r['hvp'],
                'Spike dlm 7H': ' | '.join(f"{s['date']}+{s['hvp']}%" for s in r['spikes']),
                'N Spike': r['n_spike'], 'Entry': r['entry']} for r in entry_lst]
            df = pd.DataFrame(rows)
            st.dataframe(df.style
                .map(lambda v: 'color:#4ade80;font-weight:bold' if isinstance(v,float) and v>0
                          else ('color:#f87171;font-weight:bold' if isinstance(v,float) and v<0 else ''),
                     subset=['Chg%','H/P%'])
                .format({'Chg%':'{:+.2f}','H/P%':'{:+.2f}'}),
                use_container_width=True, height=350)
        else:
            st.info("Belum ada sinyal entry BOS hari ini.")
        
        st.markdown("##### ⏳ Tunggu Entry")
        if wait_lst:
            rows = [{'★': '★' if r['in_wl'] else '', 'Code': r['code'],
                'Close': r['close'], 'Chg%': r['chg'],
                'Spike dlm 7H': ' | '.join(f"{s['date']}+{s['hvp']}%" for s in r['spikes']),
                'N Spike': r['n_spike']} for r in wait_lst]
            st.dataframe(pd.DataFrame(rows).style
                .format({'Chg%':'{:+.2f}'}),
                use_container_width=True, height=250)

    # Tab BOH
    with tabs[8]:
        lst = [r for r in boh_list if r['in_wl']] if show_only_wl else boh_list
        entry_lst = [r for r in lst if r['vol_kering']]
        watch_lst = [r for r in lst if not r['vol_kering']]
        st.markdown(f"**BOH — Breakout High (Trigger≥20% + Gap>5%) | WL: {len([r for r in boh_list if r['in_wl']])} | Total: {len(boh_list)}**")
        
        st.markdown("##### 🎯 Entry: Vol Kering")
        if entry_lst:
            rows = [{'★': '★' if r['in_wl'] else '', 'Code': r['code'],
                'Close': r['close'], 'Chg%': r['chg'],
                'Trigger': f"{r['trigger_date']} +{r['trigger_chg']}%",
                'Gap': f"{r['gap_date']} +{r['gap_pct']}%",
                'H+': r['days_after'], 'Entry': r['entry']} for r in entry_lst]
            st.dataframe(pd.DataFrame(rows).style.format({'Chg%':'{:+.2f}'}),
                use_container_width=True, height=300)
        else:
            st.info("Belum ada BOH dengan vol kering hari ini.")
        
        st.markdown("##### 👀 Pantau (setelah gap, tunggu vol kering)")
        if watch_lst:
            rows = [{'★': '★' if r['in_wl'] else '', 'Code': r['code'],
                'Close': r['close'], 'Chg%': r['chg'],
                'Trigger': f"{r['trigger_date']} +{r['trigger_chg']}%",
                'Gap': f"{r['gap_date']} +{r['gap_pct']}%",
                'H+ stlh gap': r['days_after']} for r in watch_lst]
            st.dataframe(pd.DataFrame(rows).style.format({'Chg%':'{:+.2f}'}),
                use_container_width=True, height=300)
        else:
            st.info("Tidak ada BOH dalam pantauan.")

    # Tab Divergen
    with tabs[9]:
        lst = [r for r in div_list if r['in_wl']] if show_only_wl else div_list
        lst = sorted(lst, key=lambda r: r['chg'])
        st.markdown(f"**Divergen — Harga Basing/Naik + Volume Mengering (8-20H, fleksibel) | WL: {len([r for r in div_list if r['in_wl']])} | Total: {len(div_list)}**")
        st.caption("Tren volume mengering, harga tidak turun signifikan (higher low) — sesekali boleh ada C-Spike volume di atas MA window. Ditampilkan maksimal 75 saham dengan sinyal paling kuat (rasio volume terkecil).")
        if lst:
            div_rows_html = []
            for r in lst:
                cc = '#4ade80' if r['chg'] > 0 else ('#f87171' if r['chg'] < 0 else '#EF9F27')
                pcc = '#4ade80' if r['price_chg_window'] > 0 else ('#f87171' if r['price_chg_window'] < 0 else '#EF9F27')
                sc = '+' if r['chg'] > 0 else ''
                spc = '+' if r['price_chg_window'] > 0 else ''
                cspike_txt = (f"{r['last_spike']['date']} {r['last_spike']['vol_x']}x vol / High +{r['last_spike']['high_pct']}%"
                            if r.get('last_spike') else '-')
                dh = r.get('desc_high')
                dh_txt = f"✅ {dh['window']}H (spike +{dh['spike_pct']}%)" if dh else '-'
                dh_c = '#4ade80' if dh else '#888'
                div_rows_html.append(
                    '<tr style="border-bottom:0.5px solid rgba(128,128,128,0.12)">'
                    '<td style="padding:7px 10px;font-size:12px;color:#fbbf24">' + ('★' if r['in_wl'] else '') + '</td>'
                    '<td style="padding:7px 10px;font-weight:600;font-size:13px">' + r['code'] + '</td>'
                    '<td style="padding:7px 10px;text-align:right;font-size:13px">' + str(r['close']) + '</td>'
                    '<td style="padding:7px 10px;text-align:right;color:' + cc + ';font-weight:500">' + sc + str(r['chg']) + '%</td>'
                    '<td style="padding:7px 10px;text-align:center">' + build_price_sparkline(r['code'], all_ohlcv) + '</td>'
                    '<td style="padding:7px 10px;text-align:center">' + build_vol_sparkline(r['code'], all_ohlcv) + '</td>'
                    '<td style="padding:7px 10px;text-align:right;color:' + pcc + ';font-weight:500">' + spc + str(r['price_chg_window']) + '%</td>'
                    '<td style="padding:7px 10px;text-align:right;font-size:12px;color:#888">' + f"{r['vol_ratio_pct']:.0f}%" + '</td>'
                    '<td style="padding:7px 10px;text-align:center;font-size:12px">' + str(r['spike_count']) + '</td>'
                    '<td style="padding:7px 10px;font-size:11px;color:#888">' + cspike_txt + '</td>'
                    '<td style="padding:7px 10px;font-size:11px;color:' + dh_c + '">' + dh_txt + '</td>'
                    '<td style="padding:7px 10px;text-align:center;font-size:12px">' + str(r['window_days']) + '</td>'
                    '</tr>'
                )
            div_tbl_html = (
                '<table style="width:100%;border-collapse:collapse;font-size:13px">'
                '<thead><tr style="border-bottom:1px solid rgba(128,128,128,0.25)">'
                '<th style="padding:7px 10px;color:#666;font-weight:400;font-size:11px;width:24px">★</th>'
                '<th style="padding:7px 10px;text-align:left;color:#666;font-weight:400;font-size:11px">Code</th>'
                '<th style="padding:7px 10px;text-align:right;color:#666;font-weight:400;font-size:11px">Close</th>'
                '<th style="padding:7px 10px;text-align:right;color:#666;font-weight:400;font-size:11px">Chg%</th>'
                '<th style="padding:7px 10px;text-align:center;color:#666;font-weight:400;font-size:11px">Trend 14H</th>'
                '<th style="padding:7px 10px;text-align:center;color:#666;font-weight:400;font-size:11px">Vol Trend</th>'
                '<th style="padding:7px 10px;text-align:right;color:#666;font-weight:400;font-size:11px">Chg Window%</th>'
                '<th style="padding:7px 10px;text-align:right;color:#666;font-weight:400;font-size:11px">Vol Skrg vs Awal</th>'
                '<th style="padding:7px 10px;text-align:center;color:#666;font-weight:400;font-size:11px">C-Spike</th>'
                '<th style="padding:7px 10px;text-align:left;color:#666;font-weight:400;font-size:11px">C-Spike Terakhir</th>'
                '<th style="padding:7px 10px;text-align:left;color:#666;font-weight:400;font-size:11px">Desc-High</th>'
                '<th style="padding:7px 10px;text-align:center;color:#666;font-weight:400;font-size:11px">Window (H)</th>'
                '</tr></thead><tbody>' + ''.join(div_rows_html) + '</tbody></table>'
            )
            st.html(div_tbl_html)
        else:
            st.info("Tidak ada saham dengan pola Divergen hari ini.")

    # Tab TTx
    with tabs[10]:
        remind_lst   = [r for r in ttx_list if r['priority'] == 0]
        confirm_lst  = [r for r in ttx_list if r['priority'] == 1]
        upcoming_lst = [r for r in ttx_list if r['priority'] == 2]
        miss_lst     = [r for r in ttx_list if r['priority'] == 3]
        
        st.markdown(f"**TTx — Time Trading (H/P>8% + Vol>avg4H | Siklus Berulang) | Total: {len(ttx_list)}**")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("🔔 Reminder", len(remind_lst))
        c2.metric("✅ Confirmed", len(confirm_lst))
        c3.metric("⏳ Upcoming", len(upcoming_lst))
        c4.metric("❓ Miss", len(miss_lst))
        
        def ttx_rows(lst):
            return [{'Code': r['code'], 'Gap': f"{r['gap']}H",
                'Spike1': f"{r['spk1_date']} +{r['spk1_hvp']}%",
                'Spike2': f"{r['spk2_date']} +{r['spk2_hvp']}%",
                'Status': r['status'], 'Close': r['close'], 'Chg%': r['chg']} for r in lst]
        
        if remind_lst:
            st.markdown("##### 🔔 REMINDER — Spike ke-3 segera!")
            st.dataframe(pd.DataFrame(ttx_rows(remind_lst)).style
                .format({'Chg%':'{:+.2f}'}), use_container_width=True, height=300)
        
        if confirm_lst:
            st.markdown("##### ✅ Confirmed — Spike ke-3 sudah terjadi")
            st.dataframe(pd.DataFrame(ttx_rows(confirm_lst)).style
                .format({'Chg%':'{:+.2f}'}), use_container_width=True, height=350)
        
        if upcoming_lst:
            with st.expander(f"⏳ Upcoming ({len(upcoming_lst)} saham)"):
                st.dataframe(pd.DataFrame(ttx_rows(upcoming_lst)).style
                    .format({'Chg%':'{:+.2f}'}), use_container_width=True)
        
        if miss_lst:
            with st.expander(f"❓ Miss/Lewat ({len(miss_lst)} saham)"):
                st.dataframe(pd.DataFrame(ttx_rows(miss_lst)).style
                    .format({'Chg%':'{:+.2f}'}), use_container_width=True)


    # Tab Auto StockPick
    with tabs[11]:
        st.markdown(f"**⭐ Auto StockPick — {target}**")
        st.caption("Filter: ≥3 pola ATAU 2 pola + spike ≥5% dalam 10H | Sorted: Chg% → H/P% → N Pola")

        if auto_sp:
            # ── Heatmap Monitor Posisi Open (StockPick H-4) ──────────
            dates_sorted_hm = sorted(all_dates)
            target_idx_hm = dates_sorted_hm.index(target) if target in dates_sorted_hm else -1
            lookback_dates = dates_sorted_hm[max(0, target_idx_hm-4):target_idx_hm]  # 4 hari sebelum hari ini

            # Rebuild avg_vols untuk scan
            avg_vols_hm = {}
            for code_hm, bars_hm in all_ohlcv.items():
                vols_hm = [b.get('V',0) for b in bars_hm if b.get('V',0)>0]
                avg_vols_hm[code_hm] = float(np.mean(vols_hm)) if vols_hm else 1.0

            monitor = {}  # code -> {entry_date, entry_close, entry_high, curr_close, day_n}
            for d in lookback_dates:
                sp_d = scan_stockpick(all_ohlcv, avg_vols_hm, d)
                for r in sp_d:
                    if not r.get('in_wl'): continue
                    code = r['code']
                    if code in monitor: continue  # ambil entry pertama saja
                    bars_c = all_ohlcv.get(code, [])
                    entry_bar = next((b for b in bars_c if b['date']==d), None)
                    if not entry_bar: continue
                    entry_close = entry_bar.get('C', 0)
                    entry_high  = entry_bar.get('H', entry_close)
                    # Cari close hari ini
                    today_bar = next((b for b in bars_c if b['date']==target), None)
                    if not today_bar: continue
                    curr_close = today_bar.get('C', 0)
                    curr_high  = today_bar.get('H', curr_close)
                    # Belum menembus high entry
                    if curr_high >= entry_high: continue
                    if entry_close <= 0: continue
                    gain = (curr_close - entry_close) / entry_close * 100
                    day_n = lookback_dates.index(d) + 1
                    monitor[code] = {
                        'entry_date': d[5:], 'entry_close': entry_close,
                        'entry_high': entry_high, 'curr_close': curr_close,
                        'gain': round(gain,2), 'day_n': day_n,
                    }

            def gain_style(gain):
                if gain >= 5:    return '#5DCAA5','#04342C'
                if gain >= 1:    return '#9FE1CB','#085041'
                if gain > -1:    return '#555552','#D3D1C7'
                if gain > -5:    return '#F5C4B3','#4A1B0C'
                return '#D85A30','#FAECE7'

            hm_parts = []
            for code, info in sorted(monitor.items(), key=lambda x: -x[1]['gain']):
                bg, fg = gain_style(info['gain'])
                sign = '+' if info['gain'] > 0 else ''
                part = (
                    '<div style="background:' + bg + ';color:' + fg + ';border:1px solid rgba(128,128,128,0.2);'
                    'border-radius:8px;padding:6px 10px;min-width:68px;text-align:center;">'
                    '<div style="font-size:12px;font-weight:600;">' + code + '</div>'
                    '<div style="font-size:11px;font-weight:500;">' + sign + str(info['gain']) + '%</div>'
                    '<div style="font-size:10px;opacity:0.75;">H+' + str(info['day_n']) + ' | entry ' + str(info['entry_close']) + '</div>'
                    '</div>'
                )
                hm_parts.append(part)

            if hm_parts:
                hm_html = '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;">' + ''.join(hm_parts) + '</div>'
                st.markdown(f"**Monitor Posisi Open — {len(monitor)} saham** (StockPick H-1 s/d H-4, belum tembus High entry)")
                st.html(hm_html)
            else:
                st.info("Tidak ada posisi open dari StockPick 4 hari terakhir.")
            st.divider()

            # Tabel dengan badge + sparkline
            BADGE = {
                'BOA✅': ('#EEEDFE','#3C3489'), 'BOA~': ('#EEEDFE','#534AB7'),
                'BOS':   ('#E1F5EE','#085041'), 'BOH':  ('#FAECE7','#712B13'),
                'TTx🔔': ('#FAEEDA','#633806'), 'SP':   ('#E6F1FB','#0C447C'),
                'P1':    ('#FCEBEB','#791F1F'), 'P3':   ('#FBEAF0','#4B1528'),
                'OL3':   ('#EAF3DE','#27500A'), 'Div':  ('#E3F8EF','#0F6B4C'),
                'Desc-High': ('#FFF1E0','#8A4B00'),
            }

            tbl_rows = []
            for r in auto_sp:
                bars_data = all_ohlcv.get(r['code'], [])
                cls = [b['C'] for b in bars_data[-14:] if b.get('C')]
                if len(cls) >= 3:
                    mn, mx = min(cls), max(cls)
                    rng = mx - mn if mx > mn else 1
                    spark_parts = []
                    for i2, c in enumerate(cls):
                        h2 = max(3, int((c - mn) / rng * 18))
                        col2 = '#1D9E75' if i2 == 0 or c >= cls[i2-1] else '#f87171'
                        spark_parts.append('<span style="display:inline-block;width:3px;height:' + str(h2) + 'px;background:' + col2 + ';border-radius:1px;margin-right:1px;vertical-align:bottom"></span>')
                    spark = '<div style="display:flex;align-items:flex-end;height:20px">' + ''.join(spark_parts) + '</div>'
                else:
                    spark = '—'

                badge_parts = []
                for p in r['pola']:
                    bg2, fg2 = BADGE.get(p, ('#E6F1FB','#0C447C'))
                    badge_parts.append('<span style="background:' + bg2 + ';color:' + fg2 + ';padding:2px 8px;border-radius:20px;font-size:10px;font-weight:500;margin-right:3px;white-space:nowrap">' + p + '</span>')
                badges = ''.join(badge_parts)

                chg = r['chg']; hvp = r['hvp']
                cc = '#4ade80' if chg > 0 else ('#f87171' if chg < 0 else '#EF9F27')
                hc = '#4ade80' if hvp > 0 else ('#f87171' if hvp < 0 else '#EF9F27')
                sc = '+' if chg > 0 else ''; sh = '+' if hvp > 0 else ''

                tbl_rows.append(
                    '<tr style="border-bottom:0.5px solid rgba(128,128,128,0.15)">'
                    '<td style="padding:8px 10px;font-weight:600">' + r['code'] + '</td>'
                    '<td style="padding:8px 10px;text-align:right">' + str(r['close']) + '</td>'
                    '<td style="padding:8px 10px;text-align:right;color:' + cc + ';font-weight:500">' + sc + str(round(chg,2)) + '%</td>'
                    '<td style="padding:8px 10px;text-align:right;color:' + hc + ';font-weight:500">' + sh + str(round(hvp,2)) + '%</td>'
                    '<td style="padding:8px 10px;text-align:center">' + spark + '</td>'
                    '<td style="padding:8px 10px;text-align:center">' + build_vol_sparkline(r['code'], all_ohlcv) + '</td>'
                    '<td style="padding:8px 10px">' + badges + '</td>'
                    '<td style="padding:8px 10px;font-size:11px;color:#888">' + r.get('filter','') + '</td>'
                    '</tr>'
                )

            tbl_html = (
                '<table style="width:100%;border-collapse:collapse;font-size:13px">'
                '<thead><tr style="border-bottom:1px solid rgba(128,128,128,0.2)">'
                '<th style="padding:8px 10px;text-align:left;color:#888;font-weight:400">Code</th>'
                '<th style="padding:8px 10px;text-align:right;color:#888;font-weight:400">Close</th>'
                '<th style="padding:8px 10px;text-align:right;color:#888;font-weight:400">Chg%</th>'
                '<th style="padding:8px 10px;text-align:right;color:#888;font-weight:400">H/P%</th>'
                '<th style="padding:8px 10px;text-align:center;color:#888;font-weight:400">Trend 14H</th>'
                '<th style="padding:8px 10px;text-align:center;color:#888;font-weight:400">Vol Trend</th>'
                '<th style="padding:8px 10px;text-align:left;color:#888;font-weight:400">Pola</th>'
                '<th style="padding:8px 10px;text-align:left;color:#888;font-weight:400">Filter</th>'
                '</tr></thead><tbody>' + ''.join(tbl_rows) + '</tbody></table>'
            )
            st.markdown(f"**{len(auto_sp)} saham terseleksi**")
            st.html(tbl_html)

            # Chart candlestick (versi cepat — ganti saham nggak perlu reload)
            st.divider()
            codes_available = [r['code'] for r in auto_sp]
            render_fast_chart(codes_available, all_ohlcv, n_days=30, key='autosp')

            # Distribusi pola
            st.divider()
            all_polas = {}
            for r in auto_sp:
                for p in r['pola']:
                    all_polas[p] = all_polas.get(p,0) + 1
            cols2 = st.columns(min(len(all_polas),8))
            for i3,(p,n) in enumerate(sorted(all_polas.items(),key=lambda x:-x[1])):
                cols2[i3 % len(cols2)].metric(p, n)
        else:
            st.info("Belum ada sinyal Auto StockPick hari ini.")
    # Tab Track Record
    with tabs[13]:
        st.markdown(f"**📋 Track Record | Entry → Max High T+1~T+5 | Semua Histori**")
        st.caption("Entry = muncul di pola tsb hari T | Gain% = (Max High T+1~5 - Close Entry) / Close Entry")

        # ── Breakout SP & AutoSP ──────────────────────────────────────────
        st.markdown("**🏆 Breakout SP & AutoSP — Capai Target% Keesokan Hari**")
        st.caption("Saham yang muncul di StockPick dan/atau AutoSP pada hari T, lalu High T+1 mencapai target gain dari Close T. Sumber & badge pola AutoSP ditandai.")
        col_lb1, col_lb2, col_lb3 = st.columns([2,2,1])
        lookback_opt = col_lb1.selectbox("Lookback hari:", [10,20,30,60,"Semua"], index=1, key='sp_autosp_lookback')
        gain_thresh = col_lb2.number_input("Target gain%:", min_value=1.0, max_value=20.0, value=5.0, step=0.5, key='sp_autosp_gain_thresh')
        if col_lb3.button("🔍 Hitung", key='btn_sp_autosp_breakout', use_container_width=True):
            lb_days = None if lookback_opt == "Semua" else lookback_opt
            with st.spinner("Menghitung breakout SP & AutoSP (bisa agak lama)..."):
                st.session_state['sp_autosp_breakout_cache'] = build_sp_autosp_breakout(
                    all_ohlcv, all_dates, lookback_days=lb_days, gain_threshold=gain_thresh)

        breakout_results = st.session_state.get('sp_autosp_breakout_cache')
        if breakout_results is not None:
            if breakout_results:
                st.success(f"{len(breakout_results)} kejadian ditemukan")
                _sumber_color = {'SP': ('#B5D4F4','#0C447C'), 'AutoSP': ('#E3F8EF','#0F6B4C'), 'SP + AutoSP': ('#FFF1E0','#8A4B00')}
                _bo_rows = []
                for r in breakout_results:
                    sb, sf = _sumber_color.get(r['Sumber'], ('#D3D1C7','#2C2C2A'))
                    sumber_chip = f'<span style="background:{sb};color:{sf};font-size:11px;font-weight:700;padding:2px 8px;border-radius:5px">{r["Sumber"]}</span>'
                    badge_html = ''
                    if r['Badge'] != '-':
                        for b in r['Badge'].split(', '):
                            badge_html += f'<span style="background:#EEEDFE;color:#3C3489;font-size:10px;font-weight:600;padding:1px 6px;border-radius:4px;margin-right:3px">{b}</span>'
                    else:
                        badge_html = '<span style="color:#888;font-size:11px">-</span>'
                    _bo_rows.append(
                        '<tr style="border-bottom:0.5px solid rgba(128,128,128,0.15)">'
                        f'<td style="padding:7px 10px;font-size:12px">{r["Tanggal Entry"]}</td>'
                        f'<td style="padding:7px 10px;font-weight:600;font-size:13px">{r["Code"]}</td>'
                        f'<td style="padding:7px 10px;text-align:center">{sumber_chip}</td>'
                        f'<td style="padding:7px 10px">{badge_html}</td>'
                        f'<td style="padding:7px 10px;text-align:right;font-size:12px">{r["Close Entry"]}</td>'
                        f'<td style="padding:7px 10px;font-size:12px">{r["Tanggal +1"]}</td>'
                        f'<td style="padding:7px 10px;text-align:right;font-size:12px">{r["High T+1"]}</td>'
                        f'<td style="padding:7px 10px;text-align:right;color:#4ade80;font-weight:600">+{r["Gain%"]}%</td>'
                        '</tr>'
                    )
                _bo_tbl = (
                    '<table style="width:100%;border-collapse:collapse;font-size:13px">'
                    '<thead><tr style="border-bottom:1px solid rgba(128,128,128,0.3)">'
                    '<th style="padding:7px 10px;text-align:left;color:#888;font-weight:400;font-size:11px">Tanggal Entry</th>'
                    '<th style="padding:7px 10px;text-align:left;color:#888;font-weight:400;font-size:11px">Code</th>'
                    '<th style="padding:7px 10px;text-align:center;color:#888;font-weight:400;font-size:11px">Sumber</th>'
                    '<th style="padding:7px 10px;text-align:left;color:#888;font-weight:400;font-size:11px">Badge</th>'
                    '<th style="padding:7px 10px;text-align:right;color:#888;font-weight:400;font-size:11px">Close Entry</th>'
                    '<th style="padding:7px 10px;text-align:left;color:#888;font-weight:400;font-size:11px">Tanggal +1</th>'
                    '<th style="padding:7px 10px;text-align:right;color:#888;font-weight:400;font-size:11px">High T+1</th>'
                    '<th style="padding:7px 10px;text-align:right;color:#888;font-weight:400;font-size:11px">Gain%</th>'
                    '</tr></thead><tbody>' + ''.join(_bo_rows) + '</tbody></table>'
                )
                st.html(_bo_tbl)
            else:
                st.info("Tidak ada saham yang capai target dalam periode ini.")
        st.divider()

        # Cache berdasarkan "tanda tangan" data (jumlah tanggal + tanggal terakhir +
        # jumlah kode) — bukan isi data_ohlcv langsung (terlalu besar buat di-hash tiap
        # kali). Interaksi apapun di tab ini (pilih pola, pilih saham buat chart, dst)
        # bikin Streamlit rerun seluruh script; tanpa cache ini, seluruh backtest
        # 7 pola x semua tanggal historis dihitung ulang dari nol tiap kali.
        _tr_sig = (len(all_dates), max(all_dates) if all_dates else None, len(all_ohlcv))
        if st.session_state.get('_tr_summary_sig') != _tr_sig:
            with st.spinner("Menghitung resume semua pola..."):
                st.session_state['_tr_summary_cache'] = build_trackrecord_summary(all_ohlcv, all_dates, max_hold=5)
                st.session_state['_tr_summary_sig'] = _tr_sig
        tr_summary = st.session_state['_tr_summary_cache']

        st.markdown("**📊 Resume Semua Pola**")
        st.dataframe(pd.DataFrame(tr_summary), use_container_width=True, hide_index=True)
        st.divider()

        pattern_options = list(PATTERN_TRACKRECORD_CONFIG.keys())
        pattern_sel = st.selectbox("🔍 Lihat detail pola:", pattern_options, index=0, key='tr_pattern_select')

        _tr_detail_key = (pattern_sel, _tr_sig)
        if st.session_state.get('_tr_detail_key') != _tr_detail_key:
            with st.spinner(f"Menghitung detail track record {pattern_sel}..."):
                st.session_state['_tr_detail_cache'] = build_trackrecord(all_ohlcv, all_dates, max_hold=5, pattern=pattern_sel)
                st.session_state['_tr_detail_key'] = _tr_detail_key
        tr_records = st.session_state['_tr_detail_cache']

        if tr_records:
            df_tr = pd.DataFrame(tr_records)

            # Summary metrics
            total = len(df_tr)
            done  = df_tr[df_tr['Status'].isin(['✅ Profit','🟡 Tipis','❌ Loss'])]
            profit = len(df_tr[df_tr['Status'] == '✅ Profit'])
            tipis  = len(df_tr[df_tr['Status'] == '🟡 Tipis'])
            loss   = len(df_tr[df_tr['Status'] == '❌ Loss'])
            running = len(df_tr[df_tr['Status'] == '⏳ Running'])
            winrate = round(profit / len(done) * 100, 1) if len(done) > 0 else 0
            avg_gain = round(done['Gain%'].mean(), 2) if len(done) > 0 and done['Gain%'].notna().any() else 0

            c1,c2,c3,c4,c5,c6 = st.columns(6)
            c1.metric("Total Entry", total)
            c2.metric("✅ Profit (≥5%)", profit)
            c3.metric("🟡 Tipis (0~5%)", tipis)
            c4.metric("❌ Loss", loss)
            c5.metric("⏳ Running", running)
            c6.metric("Win Rate", f"{winrate}%")

            st.divider()

            # Filter status
            filter_status = st.multiselect(
                "Filter Status:",
                options=['✅ Profit','🟡 Tipis','❌ Loss','⏳ Running'],
                default=['✅ Profit','🟡 Tipis','❌ Loss','⏳ Running'],
                key='tr_filter'
            )
            df_show = df_tr[df_tr['Status'].isin(filter_status)] if filter_status else df_tr
            df_show = df_show.sort_values(['Tanggal Entry','Gain%'], ascending=[False, False])

            st.dataframe(
                df_show.style
                .map(lambda v: 'color:#4ade80;font-weight:bold' if isinstance(v,float) and v and v>=5
                          else ('color:#facc15' if isinstance(v,float) and v and 0<=v<5
                          else ('color:#f87171;font-weight:bold' if isinstance(v,float) and v and v<0 else '')),
                     subset=['Gain%'])
                .format({'Gain%': lambda x: f'+{x:.2f}%' if x and x>0 else (f'{x:.2f}%' if x else '-')}),
                use_container_width=True,
                height=500,
                hide_index=True,
            )

            # Chart candlestick dari track record (versi cepat)
            st.divider()
            tr_codes = df_show['Code'].unique().tolist()
            if tr_codes:
                render_fast_chart(tr_codes, all_ohlcv, n_days=30, key='trackrecord')
        else:
            st.info(f"Belum ada data track record untuk pola {pattern_sel}. Upload lebih banyak file screener ke folder data/.")

    # Tab Miracle Cuan
    with tabs[14]:
        _mc_data_embed = st.session_state.get('miracle_data', '')
        _mc_ohlcv_embed = st.session_state.get('miracle_ohlcv', '')
        if not _mc_data_embed:
            st.caption("Belum ada data SP hari ini — buka tab Stockpick dulu supaya data OHLCV terisi otomatis, atau isi manual di kalkulator di bawah.")
        else:
            st.caption("Data SP hari ini sudah terisi otomatis ke kalkulator di bawah.")
        try:
            with open('miracle_cuan.html', 'r', encoding='utf-8') as _f:
                _mc_html = _f.read()
            import json as _json
            _inject = (
                "<script>\n"
                f"window.MC_PRESET_DATA = {_json.dumps(_mc_data_embed)};\n"
                f"window.MC_PRESET_OHLCV = {_json.dumps(_mc_ohlcv_embed)};\n"
                "</script>\n"
            )
            _marker = "<script>\nlet E=0, CODE='', ALL_BARS={}, TP1_PCT=5.0;"
            if _marker in _mc_html:
                _mc_html = _mc_html.replace(_marker, _inject + _marker, 1)
            else:
                _mc_html = _inject + _mc_html
            components.html(_mc_html, height=950, scrolling=True)
        except FileNotFoundError:
            st.error("File `miracle_cuan.html` tidak ditemukan di root repo. Upload file tersebut ke repo `screener_streamlit` (sejajar dengan app.py).")

        # ── Statistik & Win Rate (dari Google Sheet Dashboard + Trading Log) ──
        def render_trading_log_section(section_title, sheet_param, cache_key):
            st.divider()
            st.subheader(section_title)
            _mc_webhook = "https://script.google.com/macros/s/AKfycbyz0DcMbs7VGhkinpxt0D-vnNG6WOkywzIMOMLciQpcNeN-6C4aaTaTwTRC_Rto56Ym/exec"

            _colr1, _colr2 = st.columns([1,5])
            if _colr1.button("🔄 Refresh", key=f"refresh_{cache_key}"):
                st.session_state.pop(cache_key, None)

            if cache_key not in st.session_state:
                try:
                    import requests as _requests
                    _sresp = _requests.get(_mc_webhook, params={'action':'get_stats','sheet':sheet_param}, timeout=15)
                    st.session_state[cache_key] = _sresp.json() if _sresp.ok else {'status':'error','message':f'HTTP {_sresp.status_code}'}
                except Exception as _e:
                    st.session_state[cache_key] = {'status':'error','message':str(_e)}

            _sd = st.session_state.get(cache_key, {})
            if _sd.get('status') == 'ok':
                stats = _sd.get('stats', {})
                entries = _sd.get('entries', [])

                def _stat_card(icon, label, value, bg, border, text):
                    return (
                        f'<div style="background:{bg};border:1px solid {border};'
                        f'border-radius:10px;padding:14px 16px;min-width:0">'
                        f'<div style="font-size:11px;color:{text};opacity:0.75;text-transform:uppercase;letter-spacing:0.6px;'
                        f'display:flex;align-items:center;gap:5px">{icon} {label}</div>'
                        f'<div style="font-size:26px;font-weight:700;margin-top:6px;color:{text};line-height:1">{value}</div>'
                        f'</div>'
                    )

                row1 = ''.join([
                    _stat_card('📌', 'Total Entry', stats.get('Total Entry', '-'), '#F1F5F9', '#CBD5E1', '#334155'),
                    _stat_card('✅', 'TP1 Hit', stats.get('TP1 Hit', '-'), '#DCFCE7', '#86EFAC', '#166534'),
                    _stat_card('🎯', 'TP2 Hit', stats.get('TP2 Hit', '-'), '#BBF7D0', '#4ADE80', '#14532D'),
                    _stat_card('🛑', 'SL Hit', stats.get('SL Hit', '-'), '#FEE2E2', '#FCA5A5', '#991B1B'),
                    _stat_card('⏳', 'Running', stats.get('Running', '-'), '#FEF3C7', '#FCD34D', '#92400E'),
                ])
                row2 = ''.join([
                    _stat_card('🏆', 'Win Rate TP1', stats.get('Win Rate TP1', '-'), '#E0F2FE', '#7DD3FC', '#075985'),
                    _stat_card('🏆', 'Win Rate TP2', stats.get('Win Rate TP2', '-'), '#DBEAFE', '#93C5FD', '#1E3A8A'),
                    _stat_card('📅', 'Avg Hari TP1', stats.get('Avg Hari TP1', '-'), '#F3E8FF', '#D8B4FE', '#6B21A8'),
                    _stat_card('📅', 'Avg Hari TP2', stats.get('Avg Hari TP2', '-'), '#EDE9FE', '#C4B5FD', '#5B21B6'),
                ])
                st.html(
                    f'<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:10px">{row1}</div>'
                    f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px">{row2}</div>'
                )

                running_entries = [e for e in entries if e.get('status') in ('Running','Partial')]
                # Cache badge Pola disimpan di session_state (bukan dict lokal) supaya
                # PERSISTEN antar Streamlit rerun — tiap klik tab/widget apapun bikin
                # seluruh script main() jalan ulang dari atas, jadi tanpa ini badge
                # dihitung ulang dari nol (11 scan x tiap tanggal unik) tiap kali,
                # bahkan pas cuma pindah ke tab lain yang tidak terkait.
                _entry_badge_cache = st.session_state.setdefault('_pattern_badge_cache_global', {})
                def _entry_badges(code, tanggal):
                    if tanggal == target:
                        # Data hari ini masih bisa berubah kalau ada upload baru lagi
                        # (intraday berikutnya) — jangan di-cache, selalu hitung ulang.
                        result = get_pattern_badges_for_date(all_ohlcv, avg_vols, tanggal)
                    else:
                        if tanggal not in _entry_badge_cache:
                            _entry_badge_cache[tanggal] = get_pattern_badges_for_date(all_ohlcv, avg_vols, tanggal)
                        result = _entry_badge_cache[tanggal]
                    return render_entry_badges(result.get(code, []))

                if running_entries:
                    running_entries.sort(key=lambda e: str(e.get('tanggal','')), reverse=True)
                    st.markdown(f"**{len(running_entries)} entry masih berjalan**")
                    _rows = []
                    for e in running_entries:
                        chg_raw = str(e.get('chg_berjalan','') or '')
                        chg_c = '#f87171' if chg_raw.startswith('-') else ('#4ade80' if chg_raw not in ('','0.00%') else '#888')
                        tp1_hit = e.get('tp1_hit')
                        tp2_hit = e.get('tp2_hit')
                        hari_tp1 = e.get('hari_tp1')
                        hari_berjalan = e.get('hari_berjalan')
                        tp1_new = tp1_hit and str(hari_tp1) not in ('', 'None') and str(hari_tp1) == str(hari_berjalan)
                        new_badge = '<span style="background:#fed7aa;color:#9a3412;font-size:9px;font-weight:700;padding:1px 5px;border-radius:4px;margin-left:4px">🆕 NEW</span>' if tp1_new else ''
                        tp1_txt = f"{e.get('harga_tp1','')} {'✅' if tp1_hit else ''}"
                        tp2_txt = f"{e.get('harga_tp2','')} {'✅' if tp2_hit else ''}"
                        tp1_c = '#4ade80' if tp1_hit else '#888'
                        tp2_c = '#4ade80' if tp2_hit else '#888'
                        pola_badges = _entry_badges(e.get('code',''), e.get('tanggal',''))
                        _rows.append(
                            '<tr style="border-bottom:0.5px solid rgba(128,128,128,0.15)">'
                            f'<td style="padding:6px 8px;font-size:12px">{e.get("tanggal","")}</td>'
                            f'<td style="padding:6px 8px;font-weight:600;font-size:13px">{e.get("code","")}</td>'
                            f'<td style="padding:6px 8px">{pola_badges}</td>'
                            f'<td style="padding:6px 8px;text-align:right;font-size:12px">{e.get("close_entry","")}</td>'
                            f'<td style="padding:6px 8px;text-align:right;font-size:12px;color:{chg_c};font-weight:500">{chg_raw}</td>'
                            f'<td style="padding:6px 8px;text-align:center;font-size:12px">{e.get("hari_berjalan","")}</td>'
                            f'<td style="padding:6px 8px;font-size:12px;color:{tp1_c}"><div style="display:flex;align-items:center;justify-content:flex-end;gap:6px">{new_badge}<span>{tp1_txt}</span></div></td>'
                            f'<td style="padding:6px 8px;text-align:right;font-size:12px;color:{tp2_c}">{tp2_txt}</td>'
                            f'<td style="padding:6px 8px;text-align:center;font-size:11px">{e.get("status","")}</td>'
                            '</tr>'
                        )
                    _tbl = (
                        '<table style="width:100%;border-collapse:collapse">'
                        '<thead><tr style="border-bottom:1px solid rgba(128,128,128,0.3)">'
                        '<th style="padding:6px 8px;text-align:left;font-size:11px;color:#888">Tanggal</th>'
                        '<th style="padding:6px 8px;text-align:left;font-size:11px;color:#888">Code</th>'
                        '<th style="padding:6px 8px;text-align:left;font-size:11px;color:#888">Pola</th>'
                        '<th style="padding:6px 8px;text-align:right;font-size:11px;color:#888">Entry</th>'
                        '<th style="padding:6px 8px;text-align:right;font-size:11px;color:#888">Chg%</th>'
                        '<th style="padding:6px 8px;text-align:center;font-size:11px;color:#888">Hari</th>'
                        '<th style="padding:6px 8px;text-align:right;font-size:11px;color:#888">TP1</th>'
                        '<th style="padding:6px 8px;text-align:right;font-size:11px;color:#888">TP2</th>'
                        '<th style="padding:6px 8px;text-align:center;font-size:11px;color:#888">Status</th>'
                        '</tr></thead><tbody>' + ''.join(_rows) + '</tbody></table>'
                    )
                    st.html(_tbl)
                else:
                    st.caption("Tidak ada entry yang sedang berjalan.")

                # ── Entry yang sudah closed (TP2 Hit / SL Hit) ──
                closed_entries = [e for e in entries if e.get('status') in ('TP2 Hit','SL Hit','Dismissed')]
                if closed_entries:
                    closed_entries.sort(key=lambda e: str(e.get('tanggal','')), reverse=True)
                    st.markdown(f"**{len(closed_entries)} entry sudah match (closed)**")
                    _rows2 = []
                    for e in closed_entries:
                        is_tp2 = e.get('status') == 'TP2 Hit'
                        is_sl = e.get('status') == 'SL Hit'
                        is_dismissed = e.get('status') == 'Dismissed'
                        if is_tp2:
                            result_label = '✅ TP2 Hit'; result_color = '#4ade80'
                            gain_raw = str(e.get('tp2_pct',''))
                            gain_display = gain_raw
                            hari_final = e.get('hari_tp2','')
                        elif is_sl:
                            result_label = '🔴 SL Hit'; result_color = '#f87171'
                            gain_raw = str(e.get('sl_pct',''))
                            gain_display = ('-' + gain_raw if gain_raw and not gain_raw.startswith('-') else gain_raw)
                            hari_final = e.get('hari_sl','')
                        else:  # Dismissed — batas waktu 10 hari lewat, TP2 belum kena
                            result_label = '⏹️ Dismiss'; result_color = '#94a3b8'
                            gain_display = e.get('catatan','') or '-'
                            hari_final = e.get('hari_berjalan','')
                        pola_badges2 = _entry_badges(e.get('code',''), e.get('tanggal',''))
                        _rows2.append(
                            '<tr style="border-bottom:0.5px solid rgba(128,128,128,0.15)">'
                            f'<td style="padding:6px 8px;font-size:12px">{e.get("tanggal","")}</td>'
                            f'<td style="padding:6px 8px;font-weight:600;font-size:13px">{e.get("code","")}</td>'
                            f'<td style="padding:6px 8px">{pola_badges2}</td>'
                            f'<td style="padding:6px 8px;text-align:right;font-size:12px">{e.get("close_entry","")}</td>'
                            f'<td style="padding:6px 8px;text-align:right;font-size:11px;color:{result_color};font-weight:600">{gain_display}</td>'
                            f'<td style="padding:6px 8px;text-align:center;font-size:12px">{hari_final}</td>'
                            f'<td style="padding:6px 8px;text-align:center;font-size:11px;color:{result_color}">{result_label}</td>'
                            '</tr>'
                        )
                    _tbl2 = (
                        '<table style="width:100%;border-collapse:collapse">'
                        '<thead><tr style="border-bottom:1px solid rgba(128,128,128,0.3)">'
                        '<th style="padding:6px 8px;text-align:left;font-size:11px;color:#888">Tanggal</th>'
                        '<th style="padding:6px 8px;text-align:left;font-size:11px;color:#888">Code</th>'
                        '<th style="padding:6px 8px;text-align:left;font-size:11px;color:#888">Pola</th>'
                        '<th style="padding:6px 8px;text-align:right;font-size:11px;color:#888">Entry</th>'
                        '<th style="padding:6px 8px;text-align:right;font-size:11px;color:#888">Gain%</th>'
                        '<th style="padding:6px 8px;text-align:center;font-size:11px;color:#888">Hari</th>'
                        '<th style="padding:6px 8px;text-align:center;font-size:11px;color:#888">Result</th>'
                        '</tr></thead><tbody>' + ''.join(_rows2) + '</tbody></table>'
                    )
                    st.html(_tbl2)
            else:
                st.caption(f"⚠️ Gagal ambil statistik: {_sd.get('message','unknown error')}")

        render_trading_log_section("📊 Statistik Trading Log", "Trading Log", "mc_stats_cache")
        render_trading_log_section("📊 Statistik StockPick Log (Otomatis)", "StockPick Log", "sp_stats_cache")
        if st.session_state.get("sp_log_last_result"):
            st.caption(st.session_state["sp_log_last_result"])

    # Tab Cari Saham — kebalikan dari tab lain: cari 1 kode, lihat pola apa saja yang lolos
    with tabs[15]:
        st.markdown("### 🔍 Cari Saham")
        st.caption("Ketik kode saham — lihat semua pola yang lolos untuk saham itu hari ini.")
        search_code = st.text_input("Kode saham:", value="", placeholder="Contoh: CENT", key="search_stock_code").strip().upper()

        if search_code:
            bars_s = all_ohlcv.get(search_code, [])
            if not bars_s or bars_s[-1]['date'] != target:
                st.warning(f"Kode **{search_code}** tidak ditemukan di data hari ini ({target}), atau kode salah.")
            else:
                today_bar = bars_s[-1]
                chg_s = (today_bar['C']-today_bar['P'])/today_bar['P']*100 if today_bar.get('P') and today_bar['P']>0 else 0
                in_wl_s = search_code in ALL_WL

                c1, c2, c3 = st.columns([2,3,3])
                with c1:
                    st.metric(f"{'★ ' if in_wl_s else ''}{search_code}", f"{int(today_bar['C'])}", f"{chg_s:+.2f}%")
                with c2:
                    st.caption("Trend 14H")
                    st.html(build_price_sparkline(search_code, all_ohlcv))
                with c3:
                    st.caption("Vol Trend")
                    st.html(build_vol_sparkline(search_code, all_ohlcv))

                st.divider()
                st.markdown("**Pola yang lolos hari ini:**")

                matches = []  # (badge_label, color_bg, color_text, detail_text)

                boa_full_hit = next((r for r in boa_full if r['code']==search_code), None)
                boa_near_hit = next((r for r in boa_near if r['code']==search_code), None)
                if boa_full_hit:
                    matches.append(('BOA ✅ Full', '#EEEDFE','#3C3489', f"Score {boa_full_hit.get('score','-')}"))
                elif boa_near_hit:
                    matches.append(('BOA ~ Near', '#EEEDFE','#534AB7', f"Score {boa_near_hit.get('score','-')}"))

                p1_hit = next((r for r in p1_list if r['code']==search_code), None)
                if p1_hit:
                    matches.append(('P1 Kering', '#FCEBEB','#791F1F', f"H+{p1_hit.get('lag','-')} dari spike"))

                p3_hit = next((r for r in p3_list if r['code']==search_code), None)
                if p3_hit:
                    matches.append(('P3', '#FBEAF0','#4B1528', p3_hit.get('trigger','-')))

                ol_hit = next((r for r in ol_list if r['code']==search_code), None)
                if ol_hit:
                    matches.append(('OL Berturut', '#EAF3DE','#27500A', f"{ol_hit.get('days','-')}: {ol_hit.get('seq','-')}"))

                sv_hit = next((r for r in sv_list if r['code']==search_code), None)
                if sv_hit:
                    best_v = sv_hit.get('best', {})
                    matches.append(('SV', '#FFF6DA','#7A5B00', f"{sv_hit.get('n','-')}x spike, terbaik +{best_v.get('hvp','-')}%"))

                alert_hit = next((r for r in alert_list if r['code']==search_code), None)
                if alert_hit:
                    matches.append(('Alert Reversal', '#FDE8E8','#8B1E1E', f"Drop {alert_hit.get('acc_drop','-')}% dlm 5H"))

                bos_hit = next((r for r in bos_list if r['code']==search_code and r.get('entry','')!='Tunggu'), None)
                if bos_hit:
                    matches.append(('BOS', '#E1F5EE','#085041', f"Entry {bos_hit.get('entry','-')}"))

                boh_hit = next((r for r in boh_list if r['code']==search_code and r.get('vol_kering')), None)
                if boh_hit:
                    matches.append(('BOH', '#FAECE7','#712B13', f"H+{boh_hit.get('days_after','-')} stlh gap"))

                ttx_hit = next((r for r in ttx_list if r['code']==search_code and r.get('priority')==0), None)
                if ttx_hit:
                    matches.append(('TTx 🔔', '#FAEEDA','#633806', "Reminder aktif"))

                sp_hit = next((r for r in sp_list if r['code']==search_code and r.get('in_wl')), None)
                if sp_hit:
                    oc1_txt = " + OC1" if sp_hit.get('open_pct',0) > 1 else ""
                    matches.append(('StockPick', '#E6F1FB','#0C447C', f"Chg {sp_hit.get('chg','-')}%{oc1_txt}"))

                div_hit = next((r for r in div_list if r['code']==search_code), None)
                if div_hit:
                    dh = div_hit.get('desc_high')
                    dh_txt = f", Desc-High {dh['window']}H" if dh else ""
                    matches.append(('Divergen', '#E3F8EF','#0F6B4C', f"Vol {div_hit.get('vol_ratio_pct','-'):.0f}% (W{div_hit.get('window_days','-')}H){dh_txt}"))

                if matches:
                    badge_html = ''
                    for label, bg, txt, detail in matches:
                        badge_html += (
                            f'<div style="display:inline-flex;flex-direction:column;background:{bg};color:{txt};'
                            f'border-radius:8px;padding:8px 12px;margin:0 8px 8px 0;min-width:120px">'
                            f'<span style="font-weight:700;font-size:13px">{label}</span>'
                            f'<span style="font-size:11px;opacity:0.85">{detail}</span>'
                            f'</div>'
                        )
                    st.html(f'<div style="display:flex;flex-wrap:wrap">{badge_html}</div>')
                    st.caption(f"Total {len(matches)} pola lolos untuk {search_code} hari ini.")
                else:
                    st.info(f"{search_code} tidak lolos pola manapun hari ini.")

    # Tab ARA — pantau saham yang pernah naik besar (16-30%), alert kalau harga
    # retrace ke area sepertiga bawah dari kenaikan itu.
    with tabs[16]:
        lst = [r for r in ara_list if r['in_wl']] if show_only_wl else ara_list
        st.markdown(f"**🔺 ARA Watch — Naik 16-30%, Alert kalau Retrace ke 1/3 Bawah | WL: {len([r for r in ara_list if r['in_wl']])} | Total: {len(ara_list)}**")
        st.caption("1/3 bawah dihitung dari Prev Close (sebelum naik) sampai High tertinggi yang pernah dicapai setelahnya. Look-back 25 hari terakhir.")
        if lst:
            n_new_alert = len([r for r in lst if r['is_new_alert']])
            if n_new_alert > 0:
                st.warning(f"🚨 {n_new_alert} saham BARU SAJA menyentuh area 1/3 bawah hari ini!")
            ara_rows_html = []
            for r in lst:
                cc = '#4ade80' if r['chg'] > 0 else ('#f87171' if r['chg'] < 0 else '#EF9F27')
                sc = '+' if r['chg'] > 0 else ''
                if r['is_new_alert']:
                    status_badge = '<span style="background:#FEE2E2;color:#991B1B;font-size:10px;font-weight:700;padding:3px 8px;border-radius:6px;white-space:nowrap">🚨 ALERT BARU</span>'
                elif r['alerted']:
                    status_badge = '<span style="background:#FEF3C7;color:#92400E;font-size:10px;font-weight:700;padding:3px 8px;border-radius:6px;white-space:nowrap">⚠️ Sudah di 1/3</span>'
                else:
                    status_badge = '<span style="background:#F1F5F9;color:#334155;font-size:10px;font-weight:600;padding:3px 8px;border-radius:6px;white-space:nowrap">⏳ Belum</span>'
                ara_rows_html.append(
                    '<tr style="border-bottom:0.5px solid rgba(128,128,128,0.12)">'
                    '<td style="padding:7px 10px;font-size:12px;color:#fbbf24">' + ('★' if r['in_wl'] else '') + '</td>'
                    '<td style="padding:7px 10px;font-weight:600;font-size:13px">' + r['code'] + '</td>'
                    '<td style="padding:7px 10px;text-align:right;font-size:13px">' + str(r['close']) + '</td>'
                    '<td style="padding:7px 10px;text-align:right;color:' + cc + ';font-weight:500">' + sc + str(r['chg']) + '%</td>'
                    '<td style="padding:7px 10px;font-size:11px;color:#888">' + r['ara_date'] + ' (+' + str(r['ara_chg']) + '%)</td>'
                    '<td style="padding:7px 10px;text-align:right;font-size:12px">' + str(r['prev_close']) + '</td>'
                    '<td style="padding:7px 10px;text-align:right;font-size:12px">' + str(r['peak_high']) + '</td>'
                    '<td style="padding:7px 10px;text-align:right;font-size:12px;font-weight:600">' + str(r['lower_third']) + '</td>'
                    '<td style="padding:7px 10px;text-align:center;font-size:12px">' + str(r['days_since_ara']) + '</td>'
                    '<td style="padding:7px 10px;text-align:center">' + status_badge + '</td>'
                    '</tr>'
                )
            ara_tbl_html = (
                '<table style="width:100%;border-collapse:collapse;font-size:13px">'
                '<thead><tr style="border-bottom:1px solid rgba(128,128,128,0.25)">'
                '<th style="padding:7px 10px;color:#666;font-weight:400;font-size:11px;width:24px">★</th>'
                '<th style="padding:7px 10px;text-align:left;color:#666;font-weight:400;font-size:11px">Code</th>'
                '<th style="padding:7px 10px;text-align:right;color:#666;font-weight:400;font-size:11px">Close</th>'
                '<th style="padding:7px 10px;text-align:right;color:#666;font-weight:400;font-size:11px">Chg%</th>'
                '<th style="padding:7px 10px;text-align:left;color:#666;font-weight:400;font-size:11px">Tgl ARA</th>'
                '<th style="padding:7px 10px;text-align:right;color:#666;font-weight:400;font-size:11px">Prev Close</th>'
                '<th style="padding:7px 10px;text-align:right;color:#666;font-weight:400;font-size:11px">Peak High</th>'
                '<th style="padding:7px 10px;text-align:right;color:#666;font-weight:400;font-size:11px">1/3 Bawah</th>'
                '<th style="padding:7px 10px;text-align:center;color:#666;font-weight:400;font-size:11px">Hari</th>'
                '<th style="padding:7px 10px;text-align:center;color:#666;font-weight:400;font-size:11px">Status</th>'
                '</tr></thead><tbody>' + ''.join(ara_rows_html) + '</tbody></table>'
            )
            st.html(ara_tbl_html)
        else:
            st.info("Tidak ada saham dengan pola ARA dalam 25 hari terakhir.")

    # Tab Cek Cepat (Yahoo Finance) — BERDIRI SENDIRI, tidak menyentuh scan
    # pipeline / StockPick Log / Trading Log sama sekali. Buat kondisi lagi
    # mobile/di jalan, belum sempat upload data screener RTI.
    with tabs[17]:
        st.markdown("### 📡 Cek Cepat (Yahoo Finance)")
        st.warning(
            "⚠️ Fitur terpisah — data dari **Yahoo Finance** (delay ~15 menit, "
            "bukan harga real-time bursa). TIDAK dipakai untuk scan pola, StockPick Log, "
            "atau Trading Log manapun. Murni buat cek cepat harga pas lagi mobile."
        )
        yq_code = st.text_input("Kode saham:", value="", placeholder="Contoh: CENT", key="yahoo_quick_code").strip().upper()

        if yq_code:
            yq_cache_key = f"yahoo_quick_{yq_code}"
            col_yq1, col_yq2 = st.columns([1,5])
            if col_yq1.button("🔄 Refresh", key="yahoo_quick_refresh"):
                st.session_state.pop(yq_cache_key, None)
            if yq_cache_key not in st.session_state:
                with st.spinner(f"Mengambil data {yq_code} dari Yahoo Finance..."):
                    st.session_state[yq_cache_key] = fetch_yahoo_quick(yq_code)

            yq_bars = st.session_state.get(yq_cache_key)
            if not yq_bars:
                st.error(f"Data untuk **{yq_code}** tidak ditemukan di Yahoo Finance. Cek lagi kode sahamnya, atau saham ini mungkin tidak tercover Yahoo.")
            else:
                last = yq_bars[-1]
                chg = (last['C']-last['P'])/last['P']*100 if last.get('P') and last['P']>0 else 0
                in_wl_yq = yq_code in ALL_WL
                c1, c2 = st.columns([1,2])
                with c1:
                    st.metric(f"{'★ ' if in_wl_yq else ''}{yq_code}", f"{int(last['C'])}", f"{chg:+.2f}%")
                    st.caption(f"Update terakhir: {last['date']} (Yahoo, delay ~15 menit)")
                with c2:
                    yq_ohlcv = {yq_code: yq_bars}
                    render_fast_chart([yq_code], yq_ohlcv, n_days=30, key='yahooquick')
        else:
            st.caption("Masukkan kode saham di atas untuk cek harga cepat via Yahoo Finance.")

    st.divider()
    st.caption(f"IDX Screener v2.0 | Hadi Lie | {now.strftime('%d %b %Y %H:%M')}")


if __name__ == "__main__":
    main()
