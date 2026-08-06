def gordon_growth_tv(last_fcff, wacc, terminal_growth):
    """Terminal value at year n via a growing perpetuity (Gordon growth).

    Assumes FCFF grows at `terminal_growth` forever after the last explicit
    year. Numerator is *next* year's cash flow: last_fcff * (1 + g).

    Raises ValueError if terminal_growth >= wacc, where the perpetuity
    formula breaks down (nothing outgrows its discount rate forever).
    """
    if terminal_growth >= wacc:
        raise ValueError(
            f"terminal_growth ({terminal_growth}) must be < wacc ({wacc})"
        )
    return last_fcff * (1 + terminal_growth) / (wacc - terminal_growth)


def exit_multiple_tv(last_ebitda, ev_ebitda_multiple):
    """Terminal value at year n as an EV/EBITDA exit.

    Assumes the firm is 'sold' in year n at a multiple comparable companies
    trade at. EBITDA is reconstructed upstream as EBIT_n + D&A_n.
    """
    return last_ebitda * ev_ebitda_multiple