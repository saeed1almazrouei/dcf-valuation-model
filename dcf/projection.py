import pandas as pd
from dataclasses import dataclass

from dcf.fcff import fcff


@dataclass
class Assumptions:
    base_revenue: float       # year 0 (last actual) revenue
    growth: float | list      # single rate applied every year, OR a list of `years` rates
    ebit_margin: float        # EBIT as % of revenue
    tax_rate: float
    dna_pct: float            # D&A as % of revenue
    capex_pct: float          # capex as % of revenue
    nwc_pct: float            # ΔNWC as % of the *change* in revenue
    years: int = 10

    @classmethod
    def from_base_year(cls, revenue, ebit, dna, capex, nwc, tax_rate, growth, years=10):
        """Build assumptions from base-year dollar figures off the statements.

        Each ratio is derived by dividing the base-year dollar amount by base-year
        revenue, then held constant across the projection:
            ebit_margin = ebit  / revenue
            dna_pct     = dna    / revenue
            capex_pct   = capex  / revenue
            nwc_pct     = nwc    / revenue      # nwc is the LEVEL, not the change

        The projection derives each year's ΔNWC from nwc_pct × (change in revenue),
        so you never supply a change directly.
        """
        return cls(
            base_revenue=revenue,
            growth=growth,
            ebit_margin=ebit / revenue,
            tax_rate=tax_rate,
            dna_pct=dna / revenue,
            capex_pct=capex / revenue,
            nwc_pct=nwc / revenue,
            years=years,
        )


def _growth_path(growth, years):
    """Turn `growth` into a list of length `years`.

    Accepts a single number (applied every year) or a list of per-year rates.
    Raises if a list is passed with the wrong length, so a mismatch fails loudly.
    """
    if isinstance(growth, (int, float)):
        return [float(growth)] * years
    path = list(growth)
    if len(path) != years:
        raise ValueError(f"growth has {len(path)} entries, expected {years}")
    return path


def build_projection(a: Assumptions) -> pd.DataFrame:
    """Project `a.years` of financials and FCFF from a set of assumptions.

    Everything is driven off revenue. ΔNWC is tied to the change in revenue,
    so a zero-growth year produces zero ΔNWC.
    """
    growth = _growth_path(a.growth, a.years)
    prev_revenue = a.base_revenue          # carry-forward starts at the base year
    rows = []

    for t in range(1, a.years + 1):
        g = growth[t - 1]
        revenue = prev_revenue * (1 + g)
        ebit = revenue * a.ebit_margin
        dna = revenue * a.dna_pct
        capex = revenue * a.capex_pct
        delta_nwc = a.nwc_pct * (revenue - prev_revenue)   # change, not level
        f = fcff(ebit, a.tax_rate, dna, capex, delta_nwc)  # reuse the tested function

        rows.append({
            "year": t,
            "revenue": revenue,
            "ebit": ebit,
            "dna": dna,
            "capex": capex,
            "delta_nwc": delta_nwc,
            "fcff": f,
        })
        prev_revenue = revenue             # this year becomes next year's base

    return pd.DataFrame(rows).set_index("year")