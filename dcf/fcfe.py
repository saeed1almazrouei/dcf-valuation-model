import pandas as pd

from dcf.projection import build_projection
from dcf.valuation import pv_explicit, enterprise_value
from dcf.terminal import gordon_growth_tv

def fcfe_direct(net_income, dna, capex, delta_nwc, net_borrowing):
    """FCFE from the bottom up.

    Net income already reflects after-tax interest, so no separate tax term.
    Net borrowing is new debt raised minus debt repaid: positive = cash IN to
    equity (the firm borrowed), negative = cash OUT (the firm paid debt down).
    """
    return net_income + dna - capex - delta_nwc + net_borrowing


def fcfe_from_fcff(fcff_value, interest, tax_rate, net_borrowing):
    """FCFE built off FCFF: remove after-tax interest paid to debt, add net borrowing.

    Algebraically identical to fcfe_direct when inputs are consistent, i.e.
    net_income == (ebit - interest) * (1 - tax_rate).
    """
    return fcff_value - interest * (1 - tax_rate) + net_borrowing



def build_fcfe_projection(a, debt_pct, cost_of_debt):
    """Extend the FCFF projection with a constant-debt-ratio schedule and FCFE.

    Debt is held at `debt_pct` of revenue, so the firm borrows as it grows.
    Interest accrues on the opening (prior-year) debt balance.
    """
    df = build_projection(a).copy()

    prev_revenue = df["revenue"].shift(1)
    prev_revenue.iloc[0] = a.base_revenue          # year-1 opening = base year

    debt = debt_pct * df["revenue"]
    prev_debt = debt_pct * prev_revenue
    interest = cost_of_debt * prev_debt
    net_borrowing = debt - prev_debt

    net_income = (df["ebit"] - interest) * (1 - a.tax_rate)

    df["interest"] = interest
    df["net_income"] = net_income
    df["net_borrowing"] = net_borrowing
    df["fcfe"] = net_income + df["dna"] - df["capex"] - df["delta_nwc"] + net_borrowing
    return df


def equity_value_fcfe(df, cost_of_equity, terminal_growth):
    """Equity value directly: PV of FCFE at Re + an FCFE Gordon terminal value."""
    n = df.index[-1]
    pv_flows = pv_explicit(df, cost_of_equity, column="fcfe")
    tv = gordon_growth_tv(df["fcfe"].iloc[-1], cost_of_equity, terminal_growth)
    pv_tv = tv / (1 + cost_of_equity) ** n
    return pv_flows + pv_tv


def reconcile_equity(a, wacc, cost_of_equity, cost_of_debt, terminal_growth,
                     debt_pct, cash=0.0):
    """Equity value two ways, and the gap between them.

    direct   : discount FCFE at the cost of equity
    indirect : enterprise value (FCFF @ WACC) minus net debt
    """
    ev = enterprise_value(build_projection(a), wacc, "gordon",
                          terminal_growth=terminal_growth).enterprise_value

    fcfe_df = build_fcfe_projection(a, debt_pct, cost_of_debt)
    direct = equity_value_fcfe(fcfe_df, cost_of_equity, terminal_growth)

    net_debt = debt_pct * a.base_revenue - cash
    indirect = ev - net_debt

    return {
        "enterprise_value": ev,
        "net_debt": net_debt,
        "equity_indirect": indirect,      # EV − net debt
        "equity_direct": direct,          # PV of FCFE
        "gap": direct - indirect,
        "gap_pct": 100 * (direct - indirect) / indirect,
    }