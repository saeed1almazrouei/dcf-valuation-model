"""Heatmap rendering for the sensitivity grids."""

import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# --- validated palette (from the dataviz reference instance) ---
_BLUE_SEQ = ["#cde2fb", "#9ec5f4", "#5598e7", "#2a78d6", "#184f95", "#0d366b"]
_DIVERGING = ["#256abf", "#f0efec", "#d03b3b"]  # blue  <-  gray  ->  red

SEQ_CMAP = LinearSegmentedColormap.from_list("dcf_seq", _BLUE_SEQ)
DIV_CMAP = LinearSegmentedColormap.from_list("dcf_div", _DIVERGING)

_SURFACE = "#fcfcfb"   # cell-gap color = chart surface, gives the 2px "breathing" gap


def plot_ev_grid(grid, ax=None, title="Enterprise value — Gordon growth"):
    """Sequential heatmap of enterprise value across WACC (rows) x g (cols)."""
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 5))
    sns.heatmap(
        grid, ax=ax, cmap=SEQ_CMAP,
        annot=True, fmt=".0f", annot_kws={"fontsize": 8},
        mask=grid.isna(),                       # blank the invalid region
        linewidths=1.5, linecolor=_SURFACE,
        cbar_kws={"label": "Enterprise value"},
    )
    ax.set_xlabel("Terminal growth  g")
    ax.set_ylabel("WACC")
    ax.set_title(title, loc="left", fontsize=11)
    return ax


def plot_divergence_grid(grid, ax=None,
                         title="Gordon vs. exit multiple — divergence (%)"):
    """Diverging heatmap, gray pinned at 0 (methods agree)."""
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 5))
    vmax = float(np.nanmax(np.abs(grid.values)))   # symmetric limits keep gray at 0
    sns.heatmap(
        grid, ax=ax, cmap=DIV_CMAP,
        center=0, vmin=-vmax, vmax=vmax,           # <- the non-negotiable line
        annot=True, fmt="+.1f", annot_kws={"fontsize": 8},
        mask=grid.isna(),
        linewidths=1.5, linecolor=_SURFACE,
        cbar_kws={"label": "Gordon − exit  (% of exit EV)"},
    )
    ax.set_xlabel("Terminal growth  g")
    ax.set_ylabel("WACC")
    ax.set_title(title, loc="left", fontsize=11)
    return ax