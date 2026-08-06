import numpy as np
import pandas as pd

from dcf.valuation import enterprise_value


def ev_grid(df, wacc_range, g_range):
    """Gordon EV across WACC (rows) by terminal growth (cols). NaN where g >= wacc."""
    out = np.full((len(wacc_range), len(g_range)), np.nan)
    for i, w in enumerate(wacc_range):
        for j, g in enumerate(g_range):
            try:
                out[i, j] = enterprise_value(df, w, "gordon", terminal_growth=g).enterprise_value
            except ValueError:
                pass  # leave as NaN
    return pd.DataFrame(out, index=np.round(wacc_range, 4), columns=np.round(g_range, 4))


def divergence_grid(df, wacc_range, g_range, exit_multiple, as_percent=True):
    """Gordon-minus-exit EV across the WACC by g grid (percent by default, positive = Gordon higher)."""
    out = np.full((len(wacc_range), len(g_range)), np.nan)
    for i, w in enumerate(wacc_range):
        exit_ev = enterprise_value(df, w, "exit", exit_multiple=exit_multiple).enterprise_value
        for j, g in enumerate(g_range):
            try:
                gordon_ev = enterprise_value(df, w, "gordon", terminal_growth=g).enterprise_value
            except ValueError:
                continue
            diff = gordon_ev - exit_ev
            out[i, j] = 100 * diff / exit_ev if as_percent else diff
    return pd.DataFrame(out, index=np.round(wacc_range, 4), columns=np.round(g_range, 4))