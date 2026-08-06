def gordon_growth_tv(last_fcff, wacc, terminal_growth):
    """Gordon-growth terminal value: last_fcff*(1+g)/(wacc-g). Requires g < wacc."""
    if terminal_growth >= wacc:
        raise ValueError(
            f"terminal_growth ({terminal_growth}) must be < wacc ({wacc})"
        )
    return last_fcff * (1 + terminal_growth) / (wacc - terminal_growth)


def exit_multiple_tv(last_ebitda, ev_ebitda_multiple):
    """Exit-multiple terminal value: metric * multiple (metric chosen in enterprise_value)."""
    return last_ebitda * ev_ebitda_multiple