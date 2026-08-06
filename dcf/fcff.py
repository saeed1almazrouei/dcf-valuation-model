def fcff(ebit, tax_rate, dna, capex, delta_nwc):
    """FCFF for one period: EBIT*(1-tax) + D&A - Capex - dNWC (dNWC positive = cash out)."""
    free_cff = ebit * (1- tax_rate) + dna - capex - delta_nwc
    return free_cff