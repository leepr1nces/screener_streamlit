"""
IDX Screener Dashboard — Hadi Lie
Streamlit Web App — Standalone (semua kode dalam 1 file)
"""

import streamlit as st
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
        results.append({'code':code,'in_wl':in_wl,'close':int(b0['C']),'chg':round(chg0,2),
            'vol':round(vr0,2),'score':round(sc,1),'n':len(spikes_val),
            'best':best,'spikes':spikes_val[:3],'max_chg15':round(max_chg15,2),
            'ol':is_ol(b0),'doji':is_doji(b0),'cavg':bool(b0.get('A') and b0['C']<b0['A'])})
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
        results.append({
            'code': code, 'in_wl': in_wl, 'close': int(b0['C']),
            'chg': round(chg0,2), 'hvp': round(hvp0,2),
            'vol': round(vr0,2), 'vol_vs_prev': round(vp,2),
            'score': round(sc,1), 'max_chg7': round(max_c7h,2),
            'candle': candle,
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
        if cavg and vol_kering:   entry = "CAVG+VolKering"; score = 100
        elif cavg:                 entry = "CAVG";           score = 70
        elif vol_kering:           entry = "VolKering";      score = 70
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
    for code, bars in all_ohlcv.items():
        if code not in ALL_WL or len(bars) < 6: continue
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
            })
    for code in all_ohlcv:
        seen = set(); deduped = []
        for b in sorted(all_ohlcv[code], key=lambda x: x['date']):
            if b['date'] not in seen:
                seen.add(b['date']); deduped.append(b)
        all_ohlcv[code] = deduped
    return all_ohlcv


# ══════════════════════════════════════════════════════════════════════════════
# AUTO STOCKPICK RANGKUMAN — Kompilasi terbaik dari semua pola
# ══════════════════════════════════════════════════════════════════════════════
def auto_stockpick(boa_full, boa_near, p1_list, p3_list, ol_list, sv_list, alert_list,
                   sp_list, bos_list, boh_list, ttx_list, all_ohlcv=None, target=None):
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
    add([r for r in p1_list  if r.get('signal') == 'Kering'], 'P1')
    add([r for r in p3_list  if 'B' in str(r.get('signal',''))], 'P3')
    add([r for r in ol_list  if r.get('ol_count',0) >= 3], 'OL3')
    add([r for r in bos_list if r.get('entry','') != 'Tunggu'], 'BOS')
    add([r for r in boh_list if r.get('vol_kering')], 'BOH')
    add([r for r in ttx_list if r.get('priority') == 0], 'TTx🔔')
    add(sp_list, 'SP')

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
def render_candlestick(code, all_ohlcv, n_days=30):
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

    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TRACK RECORD — StockPick Performance
# ══════════════════════════════════════════════════════════════════════════════
def build_trackrecord(all_ohlcv, all_dates, max_hold=5):
    """
    Hitung track record StockPick dari semua data historis.
    - Entry: emiten lolos StockPick di hari T
    - Hasil: High tertinggi T+1 s/d T+5
    - Gain%: (Max High - Close Entry) / Close Entry * 100
    """
    import numpy as np

    # Buat dummy avg_vols dari semua data
    avg_vols = {}
    for code, bars in all_ohlcv.items():
        vols = [b.get('V',0) for b in bars if b.get('V',0) > 0]
        avg_vols[code] = float(np.mean(vols)) if vols else 1.0

    records = []
    # Loop setiap tanggal kecuali 5 terakhir (belum ada data hasil)
    dates_sorted = sorted(all_dates)

    for i, date_t in enumerate(dates_sorted):
        # Scan StockPick di hari T
        sp = scan_stockpick(all_ohlcv, avg_vols, date_t)
        sp_wl = [r for r in sp if r['in_wl']]
        if not sp_wl:
            continue

        # Tanggal T+1 s/d T+5
        future_dates = dates_sorted[i+1:i+1+max_hold]

        for r in sp_wl:
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
            all_ohlcv = load_from_folder("data")
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
        sp_list = scan_stockpick(all_ohlcv, avg_vols, target)
        bos_list  = scan_bos(all_ohlcv, avg_vols, target)
        boh_list  = scan_boh(all_ohlcv, avg_vols, target)
        ttx_list  = scan_ttx(all_ohlcv, avg_vols, target)
        auto_sp   = auto_stockpick(boa_full, boa_near, p1_list, p3_list, ol_list, sv_list, alert_list, sp_list, bos_list, boh_list, ttx_list, all_ohlcv, target)

    # ── Info bar ──────────────────────────────────────────────────────────────
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("📅 Data",   target)
    c2.metric("🎯 Target", next_date)
    c3.metric("📊 File",   f"{len(uploaded_files) if uploaded_files else len(glob.glob('data/*.xls')+glob.glob('data/*.xlsx'))} file")
    c4.metric("🏢 Saham",  f"{len(data_today)} saham")

    # ── Summary chips ─────────────────────────────────────────────────────────
    cols = st.columns(12)
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
        ("BOS",      len([r for r in bos_list   if r['in_wl'] and r['entry']!='Tunggu']), "#f59e0b"),
        ("BOH",      len([r for r in boh_list   if r['in_wl']]), "#06b6d4"),
        ("TTx🔔",    len([r for r in ttx_list   if r['priority']==0]), "#e879f9"),
    ]
    for col,(label,val,color) in zip(cols,chips):
        col.markdown(f"""<div style="background:#1e1e2e;border:1px solid #333;border-radius:8px;
            padding:10px;text-align:center;">
            <div style="font-size:1.5rem;font-weight:bold;color:{color};">{val}</div>
            <div style="font-size:0.72rem;color:#aaa;">{label}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_labels = ["🧹 Scan Bersih","🎯 BOA","📉 P1","🔄 P3","🕯️ OLseq","💰 SV","🚨 Alert","🚀 BOS","📈 BOH","⏰ TTx","⭐ AutoSP","🛒 Stockpick","📋 TrackRecord"]
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
    with tabs[11]:
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
                col_s = '#1D9E75' if i_s == 0 or c_s >= cls_s[i_s-1] else '#D85A30'
                parts_s.append('<span style="display:inline-block;width:3px;height:' + str(h_s) + 'px;background:' + col_s + ';border-radius:1px;margin-right:1px;vertical-align:bottom"></span>')
            return '<div style="display:flex;align-items:flex-end;height:20px">' + ''.join(parts_s) + '</div>'

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

    # Tab TTx
    with tabs[9]:
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
    with tabs[10]:
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
                'OL3':   ('#EAF3DE','#27500A'),
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
                        h = max(3, int((c - mn) / rng * 18))
                        col = '#1D9E75' if i2 == 0 or c >= cls[i2-1] else '#D85A30'
                        spark_parts.append('<span style="display:inline-block;width:3px;height:' + str(h) + 'px;background:' + col + ';border-radius:1px;margin-right:1px;vertical-align:bottom"></span>')
                    spark = '<div style="display:flex;align-items:flex-end;height:20px">' + ''.join(spark_parts) + '</div>'
                else:
                    spark = '—'

                badge_parts = []
                for p in r['pola']:
                    bg2, fg2 = BADGE.get(p, ('#E6F1FB','#0C447C'))
                    badge_parts.append('<span style="background:' + bg2 + ';color:' + fg2 + ';padding:2px 8px;border-radius:20px;font-size:10px;font-weight:500;margin-right:3px;white-space:nowrap">' + p + '</span>')
                badges = ''.join(badge_parts)

                chg = r['chg']; hvp = r['hvp']
                cc = '#4ade80' if chg > 0 else ('#f87171' if chg < 0 else '#888')
                hc = '#4ade80' if hvp > 0 else ('#f87171' if hvp < 0 else '#888')
                sc = '+' if chg > 0 else ''; sh = '+' if hvp > 0 else ''

                tbl_rows.append(
                    '<tr style="border-bottom:0.5px solid rgba(128,128,128,0.15)">'
                    '<td style="padding:8px 10px;font-weight:600">' + r['code'] + '</td>'
                    '<td style="padding:8px 10px;text-align:right">' + str(r['close']) + '</td>'
                    '<td style="padding:8px 10px;text-align:right;color:' + cc + ';font-weight:500">' + sc + str(round(chg,2)) + '%</td>'
                    '<td style="padding:8px 10px;text-align:right;color:' + hc + ';font-weight:500">' + sh + str(round(hvp,2)) + '%</td>'
                    '<td style="padding:8px 10px;text-align:center">' + spark + '</td>'
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
                '<th style="padding:8px 10px;text-align:left;color:#888;font-weight:400">Pola</th>'
                '<th style="padding:8px 10px;text-align:left;color:#888;font-weight:400">Filter</th>'
                '</tr></thead><tbody>' + ''.join(tbl_rows) + '</tbody></table>'
            )
            st.markdown(f"**{len(auto_sp)} saham terseleksi**")
            st.html(tbl_html)

            # Chart candlestick
            st.divider()
            codes_available = [r['code'] for r in auto_sp]
            col_sel, col_day = st.columns([3,1])
            selected = col_sel.selectbox('📊 Chart:', options=codes_available, index=0, key='autosp_chart_select')
            n_days = col_day.selectbox('Periode:', options=[14,21,30], index=2, key='autosp_chart_days')
            render_candlestick(selected, all_ohlcv, n_days=n_days)

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
    with tabs[12]:
        st.markdown(f"**📋 Track Record StockPick | Entry → Max High T+1~T+5 | Semua Histori**")
        st.caption("Entry = muncul di StockPick hari T | Gain% = (Max High T+1~5 - Close Entry) / Close Entry")

        with st.spinner("Menghitung track record dari semua data..."):
            tr_records = build_trackrecord(all_ohlcv, all_dates, max_hold=5)

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

            # Chart candlestick dari track record
            st.divider()
            tr_codes = df_show['Code'].unique().tolist()
            if tr_codes:
                sel_tr = st.selectbox('📊 Chart saham:', tr_codes, key='tr_chart_select')
                render_candlestick(sel_tr, all_ohlcv, n_days=30)
        else:
            st.info("Belum ada data track record. Upload lebih banyak file screener ke folder data/.")

    st.divider()
    st.caption(f"IDX Screener v2.0 | Hadi Lie | {now.strftime('%d %b %Y %H:%M')}")


if __name__ == "__main__":
    main()
