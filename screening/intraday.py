# screening/intraday.py — 10 Kriteria Screening Opening
import numpy as np
from utils import pct


def screen_intraday_10(df_today, df_prev, hist_vols, wl):
    """
    Wrapper 10 kriteria — sama seperti run_intraday.py tapi bisa dipanggil sebagai modul.
    df_today, df_prev = pandas DataFrame dengan kolom Open/High/Low/Close/Volume/Prev/Code
    hist_vols = dict {code: [list_volume]}
    wl = set kode WL
    """
    from run_intraday import screen_intraday
    return screen_intraday(df_today, df_prev, hist_vols, wl)
