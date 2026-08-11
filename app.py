"""
IDX Screener Dashboard — Hadi Lie
Streamlit Web App
"""

import streamlit as st
import pandas as pd
import numpy as np
import os, sys
from datetime import datetime

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IDX Screener — Hadi Lie",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Header */
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 20px 30px;
        border-radius: 12px;
        margin-bottom: 20px;
        color: white;
    }
    .main-header h1 { color: #00d4aa; margin: 0; font-size: 2rem; }
    .main-header p  { color: #aaa; margin: 5px 0 0 0; font-size: 0.9rem; }

    /* Metric cards */
    .metric-card {
        background: #1e1e2e;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 15px 20px;
        text-align: center;
    }
    .metric-card .value { font-size: 2rem; font-weight: bold; }
    .metric-card .label { font-size: 0.8rem; color: #aaa; margin-top: 4px; }

    /* Badge */
    .badge-wl  { background:#1a472a; color:#4ade80; padding:2px 8px; border-radius:4px; font-size:0.75rem; }
    .badge-boa { background:#1e3a5f; color:#60a5fa; padding:2px 8px; border-radius:4px; font-size:0.75rem; }
    .badge-p1  { background:#4a1942; color:#f472b6; padding:2px 8px; border-radius:4px; font-size:0.75rem; }
    .badge-p3  { background:#4a3500; color:#fbbf24; padding:2px 8px; border-radius:4px; font-size:0.75rem; }
    .badge-sv  { background:#1a3a3a; color:#2dd4bf; padding:2px 8px; border-radius:4px; font-size:0.75rem; }
    .badge-ol  { background:#3a2a00; color:#fb923c; padding:2px 8px; border-radius:4px; font-size:0.75rem; }

    /* Positive/Negative */
    .pos { color: #4ade80; font-weight: bold; }
    .neg { color: #f87171; font-weight: bold; }
    .neu { color: #94a3b8; }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── Imports dari screener ──────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import ALL_WL
from utils.loader import get_avg_vol, get_latest_date, filter_target_date
from utils.reporter import scan_bersih
from patterns import scan_boa, scan_p1, scan_p2, scan_p3, scan_ol_berturut, scan_sv, scan_tt, scan_alert


# ── Helper functions ───────────────────────────────────────────────────────────
def load_uploaded_files(uploaded_files):
    """Load dari file yang diupload via Streamlit"""
    import tempfile, re

    all_ohlcv = {}
    for uf in uploaded_files:
        # Simpan ke temp file
        suffix = '.xlsx' if uf.name.endswith('.xlsx') else '.xls'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uf.read())
            tmp_path = tmp.name

        # Ekstrak tanggal dari nama file
        m = re.search(r'(\d{8})', uf.name)
        if m:
            raw = m.group(1)
            date = f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
        else:
            date = datetime.now().strftime('%Y-%m-%d')

        try:
            df = pd.read_excel(tmp_path, sheet_name='Trades')
        except:
            try: df = pd.read_excel(tmp_path)
            except: continue

        for col in ['Open','High','Low','Close','Avg','Volume','Prev','Value']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        if 'Close' not in df.columns or df['Close'].isna().all():
            if 'Last' in df.columns:
                df['Close'] = pd.to_numeric(df['Last'], errors='coerce')

        df = df.dropna(subset=['Code','Close'])
        df = df[df['Code'].apply(lambda x: str(x).isalpha() and len(str(x))<=6)]

        for _, row in df.iterrows():
            code = str(row['Code'])
            if code not in all_ohlcv: all_ohlcv[code] = []
            all_ohlcv[code].append({
                'date': date,
                'O': float(row['Open'])   if pd.notna(row.get('Open',   float('nan'))) else None,
                'H': float(row['High'])   if pd.notna(row.get('High',   float('nan'))) else None,
                'L': float(row['Low'])    if pd.notna(row.get('Low',    float('nan'))) else None,
                'C': float(row['Close']),
                'A': float(row['Avg'])    if pd.notna(row.get('Avg',    float('nan'))) else None,
                'V': float(row['Volume']) if pd.notna(row.get('Volume', float('nan'))) else 0.0,
                'P': float(row['Prev'])   if pd.notna(row.get('Prev',   float('nan'))) else None,
                'Val': float(row['Value'])if pd.notna(row.get('Value',  float('nan'))) else 0.0,
            })
        os.unlink(tmp_path)

    # Sort & deduplicate
    for code in all_ohlcv:
        seen = set(); deduped = []
        for b in sorted(all_ohlcv[code], key=lambda x: x['date']):
            if b['date'] not in seen:
                seen.add(b['date']); deduped.append(b)
        all_ohlcv[code] = deduped

    return all_ohlcv


def color_chg(val):
    """Warna untuk perubahan harga"""
    if val > 0: return f'<span class="pos">+{val:.2f}%</span>'
    if val < 0: return f'<span class="neg">{val:.2f}%</span>'
    return f'<span class="neu">{val:.2f}%</span>'

def color_vol(val):
    if val < 0.3: return f'<span class="pos">↓{val:.2f}×</span>'
    if val < 0.7: return f'<span style="color:#fbbf24">{val:.2f}×</span>'
    return f'<span class="neu">{val:.2f}×</span>'


# ── MAIN APP ──────────────────────────────────────────────────────────────────
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📈 IDX Screener</h1>
        <p>Sistem Pola Candlestick Proprietary | Hadi Lie</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/IDX_logo.svg/200px-IDX_logo.svg.png", width=120)
        st.markdown("### ⚙️ Konfigurasi")

        # Upload files
        st.markdown("**📂 Upload File XLS dari RTI:**")
        uploaded_files = st.file_uploader(
            "Pilih file .xls / .xlsx",
            type=['xls', 'xlsx'],
            accept_multiple_files=True,
            help="Bisa upload banyak file sekaligus untuk analisa historis"
        )

        st.divider()

        # Filter options
        st.markdown("**🔍 Filter Tampilan:**")
        show_only_wl = st.toggle("Hanya WL", value=True)
        min_vol      = st.slider("Max Vol Ratio", 0.1, 2.0, 0.7, 0.1,
                                  help="Filter saham dengan vol < threshold (kering)")

        st.divider()
        st.markdown("**📋 Pola yang Ditampilkan:**")
        show_boa   = st.checkbox("BOA & ~BOA",    value=True)
        show_p1    = st.checkbox("P1 RCDrop1",    value=True)
        show_p3    = st.checkbox("P3 Momentum",   value=True)
        show_ol    = st.checkbox("OL Berturut",   value=True)
        show_sv    = st.checkbox("SV Valuasi",    value=True)
        show_alert = st.checkbox("Alert Reversal",value=True)
        show_clean = st.checkbox("Scan Bersih",   value=True)

        st.divider()
        st.caption(f"🕐 {datetime.now().strftime('%d %b %Y %H:%M')}")

    # ── Main Content ──────────────────────────────────────────────────────────
    if not uploaded_files:
        # Welcome screen
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown("""
            <div style="text-align:center; padding: 60px 20px;">
                <div style="font-size: 5rem;">📂</div>
                <h2 style="color: #00d4aa;">Upload File XLS untuk Mulai</h2>
                <p style="color: #aaa;">
                    Taruh file <b>.xls</b> dari RTI Screener di panel kiri<br>
                    Bisa upload banyak file sekaligus untuk analisa lengkap
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.info("""
            **Cara pakai:**
            1. Klik **Browse files** di sidebar kiri
            2. Pilih file `.xls` dari RTI Screener
            3. Hasil scan muncul otomatis
            """)
        return

    # ── Load & Scan ───────────────────────────────────────────────────────────
    with st.spinner("🔄 Memproses data..."):
        all_ohlcv = load_uploaded_files(uploaded_files)
        target_date = get_latest_date(all_ohlcv)
        if not target_date:
            st.error("Tidak bisa membaca tanggal dari file. Pastikan format nama file benar.")
            return

        avg_vols = {code: get_avg_vol(bars) for code, bars in all_ohlcv.items()}
        data_today = filter_target_date(all_ohlcv, target_date)

        # Jalankan semua scan
        boa_full, boa_near = scan_boa(all_ohlcv, avg_vols, target_date)
        p1_list    = scan_p1(all_ohlcv, avg_vols, target_date)
        p2_list    = scan_p2(all_ohlcv, avg_vols, target_date)
        p3_list    = scan_p3(all_ohlcv, avg_vols, target_date)
        ol_seq     = scan_ol_berturut(all_ohlcv, avg_vols, target_date)
        sv_list    = scan_sv(all_ohlcv, avg_vols, target_date)
        tt_list    = scan_tt(all_ohlcv, avg_vols, target_date)
        alert_list = scan_alert(all_ohlcv, avg_vols, target_date)
        clean      = scan_bersih(all_ohlcv, avg_vols, target_date,
                                  p1_list, p2_list, p3_list, boa_full, boa_near, sv_list, tt_list)

    # ── Header Info ───────────────────────────────────────────────────────────
    from datetime import datetime, timedelta
    dt = datetime.strptime(target_date, '%Y-%m-%d')
    delta = 3 if dt.weekday() == 4 else 1
    next_date = (dt + timedelta(days=delta)).strftime('%Y-%m-%d')

    st.markdown(f"""
    <div style="display:flex; gap:20px; margin-bottom:20px; flex-wrap:wrap;">
        <div style="background:#1e1e2e; border:1px solid #333; border-radius:10px; padding:12px 20px;">
            <span style="color:#aaa; font-size:0.8rem;">📅 Data</span>
            <div style="font-size:1.2rem; font-weight:bold; color:#00d4aa;">{target_date}</div>
        </div>
        <div style="background:#1e1e2e; border:1px solid #333; border-radius:10px; padding:12px 20px;">
            <span style="color:#aaa; font-size:0.8rem;">🎯 Target</span>
            <div style="font-size:1.2rem; font-weight:bold; color:#fbbf24;">{next_date}</div>
        </div>
        <div style="background:#1e1e2e; border:1px solid #333; border-radius:10px; padding:12px 20px;">
            <span style="color:#aaa; font-size:0.8rem;">📊 File diproses</span>
            <div style="font-size:1.2rem; font-weight:bold;">{len(uploaded_files)} file</div>
        </div>
        <div style="background:#1e1e2e; border:1px solid #333; border-radius:10px; padding:12px 20px;">
            <span style="color:#aaa; font-size:0.8rem;">🏢 Saham di-scan</span>
            <div style="font-size:1.2rem; font-weight:bold;">{len(data_today)}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Summary Metrics ───────────────────────────────────────────────────────
    c1,c2,c3,c4,c5,c6,c7,c8 = st.columns(8)
    metrics = [
        (c1, "BOA ✅",    sum(1 for r in boa_full if r['in_wl']),  "#60a5fa"),
        (c2, "~BOA",      sum(1 for r in boa_near if r['in_wl']),  "#93c5fd"),
        (c3, "P1",        sum(1 for r in p1_list  if r['in_wl']),  "#f472b6"),
        (c4, "P3",        sum(1 for r in p3_list  if r['in_wl']),  "#fbbf24"),
        (c5, "OLseq",     sum(1 for r in ol_seq   if r['in_wl']),  "#fb923c"),
        (c6, "SV",        sum(1 for r in sv_list  if r['in_wl']),  "#2dd4bf"),
        (c7, "Alert",     sum(1 for r in alert_list if r['in_wl']), "#f87171"),
        (c8, "Bersih WL", sum(1 for r in clean    if r['in_wl']),  "#4ade80"),
    ]
    for col, label, val, color in metrics:
        col.markdown(f"""
        <div style="background:#1e1e2e; border:1px solid #333; border-radius:8px;
                    padding:12px; text-align:center;">
            <div style="font-size:1.6rem; font-weight:bold; color:{color};">{val}</div>
            <div style="font-size:0.75rem; color:#aaa;">{label}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tabs = st.tabs(["🧹 Scan Bersih", "🎯 BOA", "📉 P1 & P3", "🕯️ OL Berturut", "💰 SV", "🚨 Alert"])

    # ── Tab 1: Scan Bersih ────────────────────────────────────────────────────
    with tabs[0]:
        if not show_clean:
            st.info("Scan Bersih dimatikan di sidebar.")
        else:
            wl_clean  = [r for r in clean if r['in_wl']]
            nwl_clean = [r for r in clean if not r['in_wl']]
            display   = wl_clean if show_only_wl else clean

            st.markdown(f"### 🧹 Scan Bersih ≤13% | WL: {len(wl_clean)} | Total: {len(clean)}")

            if display:
                rows = []
                for r in display:
                    tags_html = ' '.join([
                        f'<span class="badge-boa">BOA</span>'   if 'BOA!' in r['ex'] else '',
                        f'<span class="badge-boa">~BOA</span>'  if '~BOA' in r['ex'] else '',
                        f'<span class="badge-p1">P1</span>'     if 'P1'   in r['ex'] else '',
                        f'<span class="badge-p3">P3</span>'     if 'P3'   in r['ex'] else '',
                        f'<span class="badge-sv">SV</span>'     if 'SV'   in r['ex'] else '',
                        f'<span class="badge-ol">OLseq</span>'  if 'OLseq' in ' '.join(r['ex']) else '',
                    ])
                    rows.append({
                        'Code':   f"★ {r['code']}" if r['in_wl'] else r['code'],
                        'Close':  r['close'],
                        'Chg%':   r['chg'],
                        'H/P%':   r['hvp'],
                        'Vol':    r['vol'],
                        'mc15%':  r['max_chg15'],
                        'Spike':  f"{r['n_spike']}x+{r['max_spike']:.0f}%" if r['n_spike'] else '-',
                        'OL':     r['n_ol'],
                        'Doji':   r['n_dj'],
                        'CAvg':   r['n_ca'],
                        'Signal': ' '.join(r['ex'][:4]),
                        'Candle': '+'.join(r['tags']) or '-',
                    })

                df_clean = pd.DataFrame(rows)

                # Color formatting
                def style_df(df):
                    def color_chg_col(val):
                        if isinstance(val, float):
                            if val > 0: return 'color: #4ade80; font-weight: bold'
                            if val < 0: return 'color: #f87171; font-weight: bold'
                        return ''
                    def color_vol_col(val):
                        if isinstance(val, float):
                            if val < 0.3: return 'color: #4ade80'
                            if val < 0.7: return 'color: #fbbf24'
                        return ''
                    return df.style\
                        .applymap(color_chg_col, subset=['Chg%','H/P%'])\
                        .applymap(color_vol_col, subset=['Vol'])\
                        .format({'Chg%':'{:+.2f}','H/P%':'{:+.2f}','Vol':'{:.2f}','mc15%':'{:+.1f}'})

                st.dataframe(
                    style_df(df_clean),
                    use_container_width=True,
                    height=500,
                )
            else:
                st.warning("Tidak ada hasil scan bersih.")

    # ── Tab 2: BOA ────────────────────────────────────────────────────────────
    with tabs[1]:
        if not show_boa:
            st.info("BOA dimatikan di sidebar.")
        else:
            boa_wl   = [r for r in boa_full if r['in_wl']]
            boa_nwl  = [r for r in boa_full if not r['in_wl']]
            near_wl  = [r for r in boa_near if r['in_wl']]

            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown(f"### 🎯 BOA (6/6) — WL: {len(boa_wl)} | Non-WL: {len(boa_nwl)}")
                display_boa = boa_wl if show_only_wl else boa_full
                if display_boa:
                    rows = []
                    for r in display_boa:
                        spk = ' | '.join([f"{s['date']}+{s['hvp']:.0f}%({s['vr']:.1f}x)" for s in r['spikes']])
                        rows.append({
                            'Code':     f"★ {r['code']}" if r['in_wl'] else r['code'],
                            'Close':    r['close'],
                            'Chg%':     r['chg'],
                            'Vol':      r['vol'],
                            'Range%':   r['rng'],
                            'DistLow%': r['dist_low'],
                            'OL+Dj':    r['n_ol'] + r['n_doji'],
                            'CAvg':     r['n_cavg'],
                            'Window':   r['window'],
                            'Spikes':   spk or '-',
                        })
                    df_boa = pd.DataFrame(rows)
                    st.dataframe(
                        df_boa.style
                            .applymap(lambda v: 'color:#4ade80;font-weight:bold' if isinstance(v,float) and v>0 else
                                               ('color:#f87171;font-weight:bold' if isinstance(v,float) and v<0 else ''),
                                      subset=['Chg%'])
                            .applymap(lambda v: 'color:#4ade80' if isinstance(v,float) and v<0.3 else
                                               ('color:#fbbf24' if isinstance(v,float) and v<0.7 else ''),
                                      subset=['Vol'])
                            .format({'Chg%':'{:+.2f}','Vol':'{:.2f}','Range%':'{:.1f}','DistLow%':'{:.1f}'}),
                        use_container_width=True, height=400,
                    )

            with col_b:
                st.markdown(f"### ⚠️ Hampir BOA (4-5/6) — WL: {len(near_wl)}")
                display_near = near_wl if show_only_wl else boa_near
                if display_near:
                    rows = []
                    for r in display_near:
                        rows.append({
                            'Code':     f"★ {r['code']}" if r['in_wl'] else r['code'],
                            'Close':    r['close'],
                            'Vol':      r['vol'],
                            'Range%':   r['rng'],
                            'DistLow%': r['dist_low'],
                            'OL+Dj':    r['n_ol'] + r['n_doji'],
                            'CAvg':     r['n_cavg'],
                            'Missing':  ', '.join(r['fails'][:2]),
                        })
                    df_near = pd.DataFrame(rows)
                    st.dataframe(
                        df_near.style
                            .applymap(lambda v: 'color:#4ade80' if isinstance(v,float) and v<0.3 else
                                               ('color:#fbbf24' if isinstance(v,float) and v<0.7 else ''),
                                      subset=['Vol'])
                            .format({'Vol':'{:.2f}','Range%':'{:.1f}','DistLow%':'{:.1f}'}),
                        use_container_width=True, height=400,
                    )

    # ── Tab 3: P1 & P3 ───────────────────────────────────────────────────────
    with tabs[2]:
        if not show_p1:
            st.info("P1/P3 dimatikan di sidebar.")
        else:
            col_a, col_b = st.columns(2)

            with col_a:
                p1_wl = [r for r in p1_list if r['in_wl']]
                st.markdown(f"### 📉 P1 RCDrop1 — WL: {len(p1_wl)}")
                display_p1 = p1_wl if show_only_wl else p1_list
                if display_p1:
                    rows = []
                    for r in display_p1:
                        rows.append({
                            'Code':      f"★ {r['code']}" if r['in_wl'] else r['code'],
                            'Close':     r['close'],
                            'Chg%':      r['chg'],
                            'Vol':       r['vol'],
                            'Spike':     f"{r['spike_date']}",
                            'Spk H/P%':  r['spike_hvp'],
                            'Spk Vol':   r['spike_vol'],
                            'Lag (H)':   r['lag'],
                            'maxCA%':    r['max_ca'],
                        })
                    df_p1 = pd.DataFrame(rows)
                    st.dataframe(
                        df_p1.style
                            .applymap(lambda v: 'color:#4ade80;font-weight:bold' if isinstance(v,float) and v<0 else
                                               ('color:#f87171;font-weight:bold' if isinstance(v,float) and v<0 else ''), subset=['maxCA%'])
                            .applymap(lambda v: 'color:#4ade80' if isinstance(v,float) and v<0.3 else
                                               ('color:#fbbf24' if isinstance(v,float) and v<0.7 else ''), subset=['Vol'])
                            .format({'Chg%':'{:+.2f}','Vol':'{:.2f}','Spk H/P%':'{:.1f}','Spk Vol':'{:.1f}','maxCA%':'{:+.1f}'}),
                        use_container_width=True, height=400,
                    )
                else:
                    st.info("Tidak ada P1 WL saat ini.")

            with col_b:
                p3_wl = [r for r in p3_list if r['in_wl']]
                st.markdown(f"### 🔄 P3 Momentum — WL: {len(p3_wl)}")
                display_p3 = p3_wl if show_only_wl else p3_list
                if display_p3:
                    rows = []
                    for r in display_p3:
                        rows.append({
                            'Code':     f"★ {r['code']}" if r['in_wl'] else r['code'],
                            'Close':    r['close'],
                            'Chg%':     r['chg'],
                            'Vol':      r['vol'],
                            'Spk1':     f"{r['spk1_date']}+{r['spk1_hvp']:.0f}%",
                            'Spk2':     f"{r['spk2_date']}+{r['spk2_hvp']:.0f}%",
                            'Trigger':  r['trigger'],
                        })
                    df_p3 = pd.DataFrame(rows)
                    st.dataframe(df_p3, use_container_width=True, height=400)
                else:
                    st.info("Tidak ada P3 WL saat ini.")

    # ── Tab 4: OL Berturut ────────────────────────────────────────────────────
    with tabs[3]:
        if not show_ol:
            st.info("OL Berturut dimatikan di sidebar.")
        else:
            ol_wl = [r for r in ol_seq if r['in_wl'] and r['vol'] > 0]
            st.markdown(f"### 🕯️ OL Berturut — WL: {len(ol_wl)}")
            display_ol = ol_wl if show_only_wl else [r for r in ol_seq if r['vol'] > 0]
            if display_ol:
                rows = []
                for r in display_ol:
                    rows.append({
                        'Code':   f"★ {r['code']}" if r['in_wl'] else r['code'],
                        'Close':  r['close'],
                        'Chg%':   r['chg'],
                        'H/P%':   r['hvp'],
                        'Vol':    r['vol'],
                        'Hari':   r['days'],
                        'Sequence': r['seq'],
                    })
                df_ol = pd.DataFrame(rows)
                st.dataframe(
                    df_ol.style
                        .applymap(lambda v: 'color:#4ade80;font-weight:bold' if isinstance(v,float) and v>0 else
                                           ('color:#f87171;font-weight:bold' if isinstance(v,float) and v<0 else ''), subset=['Chg%','H/P%'])
                        .applymap(lambda v: 'color:#4ade80' if isinstance(v,float) and v<0.3 else
                                           ('color:#fbbf24' if isinstance(v,float) and v<0.7 else ''), subset=['Vol'])
                        .format({'Chg%':'{:+.2f}','H/P%':'{:+.2f}','Vol':'{:.2f}'}),
                    use_container_width=True, height=500,
                )

    # ── Tab 5: SV ─────────────────────────────────────────────────────────────
    with tabs[4]:
        if not show_sv:
            st.info("SV dimatikan di sidebar.")
        else:
            sv_wl = [r for r in sv_list if r['in_wl']]
            st.markdown(f"### 💰 Spike Valuasi (Rp800Jt–5M) — WL: {len(sv_wl)}")
            display_sv = sv_wl if show_only_wl else sv_list
            if display_sv:
                rows = []
                for r in display_sv:
                    sig = '+'.join(x for x in ['OL' if r['ol'] else '', 'Doji' if r['doji'] else '', 'CAvg' if r['cavg'] else ''] if x) or '-'
                    spk = ' | '.join([f"{s['date']}+{s['hvp']:.0f}%(Rp{s['val_b']:.2f}M)" for s in r['spikes'][:2]])
                    rows.append({
                        'Code':    f"★ {r['code']}" if r['in_wl'] else r['code'],
                        'Close':   r['close'],
                        'Chg%':    r['chg'],
                        'mc15%':   r['max_chg15'],
                        'Jml Spk': r['n'],
                        'Best Spk': f"{r['best']['date']}+{r['best']['hvp']:.0f}%",
                        'Value':   f"Rp{r['best']['val_b']:.2f}M",
                        'Candle':  sig,
                    })
                df_sv = pd.DataFrame(rows)
                st.dataframe(
                    df_sv.style
                        .applymap(lambda v: 'color:#4ade80;font-weight:bold' if isinstance(v,float) and v>0 else
                                           ('color:#f87171;font-weight:bold' if isinstance(v,float) and v<0 else ''), subset=['Chg%'])
                        .format({'Chg%':'{:+.2f}','mc15%':'{:+.1f}'}),
                    use_container_width=True, height=500,
                )

    # ── Tab 6: Alert ──────────────────────────────────────────────────────────
    with tabs[5]:
        if not show_alert:
            st.info("Alert dimatikan di sidebar.")
        else:
            al_wl = [r for r in alert_list if r['in_wl']]
            st.markdown(f"### 🚨 Alert Reversal — WL: {len(al_wl)}")
            display_al = al_wl if show_only_wl else alert_list
            if display_al:
                rows = []
                for r in display_al:
                    rows.append({
                        'Code':     f"★ {r['code']}" if r['in_wl'] else r['code'],
                        'Close':    r['close'],
                        'Chg%':     r['chg'],
                        'Vol':      r['vol'],
                        'Drop 5H%': r['acc_drop'],
                        'Med Vol':  r['med_vol'],
                        'Merah':    f"{r['red5']}/5",
                        'Last Spk': r['spk'],
                    })
                df_al = pd.DataFrame(rows)
                st.dataframe(
                    df_al.style
                        .applymap(lambda v: 'color:#f87171;font-weight:bold' if isinstance(v,float) and v<0 else '', subset=['Drop 5H%','Chg%'])
                        .applymap(lambda v: 'color:#4ade80' if isinstance(v,float) and v<0.3 else '', subset=['Med Vol','Vol'])
                        .format({'Chg%':'{:+.2f}','Vol':'{:.2f}','Drop 5H%':'{:.1f}','Med Vol':'{:.2f}'}),
                    use_container_width=True, height=400,
                )
            else:
                st.success("✅ Tidak ada Alert WL saat ini — pasar sehat!")

    # ── Footer ────────────────────────────────────────────────────────────────
    st.divider()
    st.caption("IDX Screener v1.0 | Sistem Pola Candlestick Proprietary | Hadi Lie | 2026")


if __name__ == "__main__":
    main()
