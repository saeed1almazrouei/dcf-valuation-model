"""Discounting, WACC, and enterprise-value assembly for the DCF model."""

from dataclasses import dataclass

from dcf.terminal import gordon_growth_tv, exit_multiple_tv


def cost_of_equity_capm(risk_free, beta, equity_risk_premium):
    """CAPM cost of equity: Re = Rf + beta * ERP."""
    return risk_free + beta * equity_risk_premium


def wacc(equity_value, debt_value, cost_of_equity, cost_of_debt, tax_rate):
    """Blended cost of capital. Weights use market values of equity and debt.

    Note the circularity: equity_value is roughly what a DCF is trying to
    estimate, yet it's needed here for the weight.
    """
    V = equity_value + debt_value
    return (equity_value / V) * cost_of_equity + (debt_value / V) * cost_of_debt * (1 - tax_rate)


def pv_explicit(df, rate, column="fcff"):
    """Present value of an explicit cash-flow stream (column defaults to fcff)."""
    factors = [1.0 / (1.0 + rate) ** t for t in df.index]
    return float((df[column].values * factors).sum())


def _terminal_metric(df, metric):
    """The final-year value of the metric an exit multiple is applied to.

    "ebitda" -> EBIT_n + D&A_n, "ebit" -> EBIT_n, "sales"/"revenue" -> revenue_n.
    """
    metric = metric.lower()
    if metric == "ebitda":
        return df["ebit"].iloc[-1] + df["dna"].iloc[-1]
    if metric == "ebit":
        return df["ebit"].iloc[-1]
    if metric in ("sales", "revenue"):
        value = df["revenue"].iloc[-1]
        if value != value:  # NaN guard (projection_from_lists with no revenue)
            raise ValueError("sales metric needs a revenue column. none was supplied")
        return value
    raise ValueError(f"unknown exit metric: {metric!r} (use 'ebitda', 'ebit', or 'sales')")


@dataclass
class Valuation:
    method: str
    pv_explicit: float
    terminal_value: float
    pv_terminal: float
    enterprise_value: float
    tv_share: float


def enterprise_value(df, wacc, method="gordon", terminal_growth=None,
                     exit_multiple=None, exit_metric="ebitda"):
    """Assemble enterprise value from a projection and a terminal method.

    method="gordon" needs terminal_growth.
    method="exit"   needs exit_multiple, applied to `exit_metric` (default
                    "ebitda" also "ebit" or "sales").
    """
    pv_flows = pv_explicit(df, wacc)
    n = df.index[-1]

    if method == "gordon":
        if terminal_growth is None:
            raise ValueError("gordon method requires terminal_growth")
        tv = gordon_growth_tv(df["fcff"].iloc[-1], wacc, terminal_growth)
    elif method == "exit":
        if exit_multiple is None:
            raise ValueError("exit method requires exit_multiple")
        tv = exit_multiple_tv(_terminal_metric(df, exit_metric), exit_multiple)
    else:
        raise ValueError(f"unknown method: {method!r}")

    pv_tv = tv / (1 + wacc) ** n
    ev = pv_flows + pv_tv
    return Valuation(method, pv_flows, tv, pv_tv, ev, pv_tv / ev)


def implied_exit_multiple(df, wacc, terminal_growth, metric="ebitda"):
    """The EV/<metric> exit multiple that the Gordon terminal value implies.

        implied = gordon_TV_n / metric_n

    Feeding the result back as `exit_multiple` (same metric) reproduces the
    Gordon enterprise value exactly - it tells you what multiple you are
    *implicitly* assuming with your growth rate.
    """
    tv = gordon_growth_tv(df["fcff"].iloc[-1], wacc, terminal_growth)
    return tv / _terminal_metric(df, metric)