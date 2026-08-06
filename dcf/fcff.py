def fcff(ebit, tax_rate, dna, capex, delta_nwc):
    free_cff = ebit * (1- tax_rate) + dna - capex - delta_nwc
    return free_cff