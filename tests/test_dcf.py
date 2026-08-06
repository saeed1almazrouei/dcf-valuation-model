import numpy as np
import pytest

from dcf.fcff import fcff
from dcf.projection import Assumptions, build_projection
from dcf.valuation import wacc, pv_explicit, enterprise_value
from dcf.terminal import gordon_growth_tv, exit_multiple_tv
from dcf.sensitivity import ev_grid, divergence_grid


BASE = Assumptions(1000, 0.10, 0.20, 0.25, 0.05, 0.07, 0.10)


# --- FCFF derivation ---
def test_fcff_hand_calc():
    assert fcff(1000, 0.25, 200, 300, 150) == pytest.approx(500.0)

def test_fcff_nwc_sign_releases_cash():
    # a *decrease* in working capital (negative delta) frees cash -> higher FCFF
    base = fcff(1000, 0.25, 200, 300, 0)
    assert fcff(1000, 0.25, 200, 300, -50) == pytest.approx(base + 50)


# --- projection engine ---
def test_zero_growth_is_flat_with_no_nwc():
    df = build_projection(Assumptions(1000, 0.0, 0.20, 0.25, 0.05, 0.07, 0.10))
    assert (df["delta_nwc"] == 0).all()
    assert df["fcff"].nunique() == 1
    assert df["fcff"].iloc[0] == pytest.approx(130.0)

def test_revenue_compounds():
    df = build_projection(BASE)
    assert df["revenue"].iloc[0] == pytest.approx(1100)
    assert df["revenue"].iloc[1] == pytest.approx(1210)
    assert len(df) == 10

def test_growth_path_wrong_length_raises():
    with pytest.raises(ValueError):
        build_projection(Assumptions(1000, [0.1] * 9, 0.20, 0.25, 0.05, 0.07, 0.10))


# --- discounting ---
def test_pv_at_zero_rate_equals_sum():
    df = build_projection(BASE)
    assert pv_explicit(df, 0.0) == pytest.approx(df["fcff"].sum())

def test_higher_rate_lowers_pv():
    df = build_projection(BASE)
    assert pv_explicit(df, 0.10) < pv_explicit(df, 0.0)

def test_wacc_endpoints():
    assert wacc(100, 0, 0.10, 0.05, 0.25) == pytest.approx(0.10)        # all equity
    assert wacc(0, 100, 0.10, 0.05, 0.25) == pytest.approx(0.05 * 0.75)  # all debt, after tax


# --- terminal value ---
def test_gordon_uses_next_year_numerator():
    assert gordon_growth_tv(100, 0.10, 0.02) == pytest.approx(100 * 1.02 / 0.08)

def test_gordon_guard_raises_when_g_ge_wacc():
    with pytest.raises(ValueError):
        gordon_growth_tv(100, 0.10, 0.10)
    with pytest.raises(ValueError):
        gordon_growth_tv(100, 0.10, 0.12)

def test_exit_multiple_tv():
    assert exit_multiple_tv(648.435, 8) == pytest.approx(5187.48)


# --- enterprise value assembly ---
def test_breakdown_is_internally_consistent():
    df = build_projection(BASE)
    v = enterprise_value(df, 0.10, "gordon", terminal_growth=0.02)
    assert v.enterprise_value == pytest.approx(v.pv_explicit + v.pv_terminal)
    assert v.tv_share == pytest.approx(v.pv_terminal / v.enterprise_value)
    assert v.enterprise_value == pytest.approx(2750.68, abs=0.5)

def test_missing_terminal_params_raise():
    df = build_projection(BASE)
    with pytest.raises(ValueError):
        enterprise_value(df, 0.10, "gordon")   # no terminal_growth
    with pytest.raises(ValueError):
        enterprise_value(df, 0.10, "exit")     # no exit_multiple


# --- sensitivity grids ---
def test_invalid_region_is_nan():
    df = build_projection(BASE)
    grid = ev_grid(df, np.array([0.08, 0.10]), np.array([0.05, 0.12]))
    assert np.isnan(grid.loc[0.08, 0.12])   # g >= wacc -> blank

def test_divergence_sign_flips_across_g():
    df = build_projection(BASE)
    d = divergence_grid(df, np.array([0.10]), np.array([0.0, 0.04]), 8)
    assert d.loc[0.10, 0.0] < 0    # Gordon below exit at low g
    assert d.loc[0.10, 0.04] > 0   # Gordon above exit at high g

def test_from_base_year_matches_ratio_constructor():
    dollars = Assumptions.from_base_year(
        revenue=1000, ebit=200, dna=50, capex=70, nwc=100, tax_rate=0.25, growth=0.10
    )
    ratios = Assumptions(1000, 0.10, 0.20, 0.25, 0.05, 0.07, 0.10)
    assert dollars == ratios

def test_cost_of_equity_capm():
    # Re = Rf + beta*ERP = 0.04 + 1.1*0.05 = 0.095
    from dcf.valuation import cost_of_equity_capm
    assert cost_of_equity_capm(0.04, 1.1, 0.05) == pytest.approx(0.095)

def test_fcfe_two_methods_agree():
    from dcf.fcfe import fcfe_direct, fcfe_from_fcff
    ebit, interest, tax = 300, 40, 0.25
    dna, capex, nwc, nb = 50, 70, 10, 15
    net_income = (ebit - interest) * (1 - tax)
    fcff_value = fcff(ebit, tax, dna, capex, nwc)
    direct = fcfe_direct(net_income, dna, capex, nwc, nb)
    viaf = fcfe_from_fcff(fcff_value, interest, tax, nb)
    assert direct == pytest.approx(viaf)

def test_fcfe_reconciles_exactly_with_no_debt():
    from dcf.fcfe import reconcile_equity
    a = Assumptions.from_base_year(1000, 200, 50, 70, 100, 0.25, 0.10)
    r = reconcile_equity(a, wacc=0.10, cost_of_equity=0.10, cost_of_debt=0.06,
                         terminal_growth=0.02, debt_pct=0.0, cash=0.0)
    assert r["net_debt"] == pytest.approx(0.0)
    assert r["equity_direct"] == pytest.approx(r["equity_indirect"])
    assert r["gap"] == pytest.approx(0.0, abs=1e-6)