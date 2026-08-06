from dataclasses import dataclass
from dcf.terminal import gordon_growth_tv, exit_multiple_tv

def cost_of_equity_capm(risk_free, beta, equity_risk_premium):
    """CAPM: Re = Rf + beta * ERP."""
    return risk_free + beta * equity_risk_premium


def wacc(equity_value, debt_value, cost_of_equity, cost_of_debt, tax_rate):
    """Blended cost of capital. Weights use market values of equity and debt.

    Note the circularity: equity_value is roughly what a DCF is trying to
    estimate, yet it's needed here for the weight. Standard practice uses
    target weights or current market cap — a genuine soft spot, not a bug.
    """
    V = equity_value + debt_value
    return (equity_value / V) * cost_of_equity + (debt_value / V) * cost_of_debt * (1 - tax_rate)

def pv_explicit(df, rate, column="fcff"):
    factors = [1.0 / (1.0 + rate) ** t for t in df.index]
    return float((df[column].values * factors).sum())





@dataclass
class Valuation:
    method: str
    pv_explicit: float      # PV of the 10-year FCFF stream
    terminal_value: float   # TV as of year n, undiscounted
    pv_terminal: float      # that TV discounted back to today
    enterprise_value: float # pv_explicit + pv_terminal
    tv_share: float         # pv_terminal / enterprise_value  <- the "60-80%" number


def enterprise_value(df, wacc, method="gordon", terminal_growth=None, exit_multiple=None):
    """Assemble enterprise value from a projection and a terminal method.

    method="gordon" needs terminal_growth; method="exit" needs exit_multiple.
    Returns a Valuation with the full breakdown, not just the EV, so the
    terminal-value share is always visible.
    """
    pv_flows = pv_explicit(df, wacc)
    n = df.index[-1]                       # last explicit year (10)

    if method == "gordon":
        if terminal_growth is None:
            raise ValueError("gordon method requires terminal_growth")
        tv = gordon_growth_tv(df["fcff"].iloc[-1], wacc, terminal_growth)
    elif method == "exit":
        if exit_multiple is None:
            raise ValueError("exit method requires exit_multiple")
        last_ebitda = df["ebit"].iloc[-1] + df["dna"].iloc[-1]
        tv = exit_multiple_tv(last_ebitda, exit_multiple)
    else:
        raise ValueError(f"unknown method: {method!r}")

    pv_tv = tv / (1 + wacc) ** n
    ev = pv_flows + pv_tv
    return Valuation(method, pv_flows, tv, pv_tv, ev, pv_tv / ev)