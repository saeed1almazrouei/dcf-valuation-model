# API Reference

Every public function in the `dcf` package, its inputs, the allowed values, and
what it returns. Grouped by module. All rates and percentages are decimals
(0.10 means 10 percent). All dollar figures are in whatever unit you feed in
(the model is unit-agnostic, just be consistent).

---

## dcf.fcff

### `fcff(ebit, tax_rate, dna, capex, delta_nwc)`

Free cash flow to the firm for one period.

| Input | Type | Meaning |
|-------|------|---------|
| `ebit` | number | Operating income (EBIT) for the period |
| `tax_rate` | number 0 to 1 | Tax rate as a decimal |
| `dna` | number | Depreciation and amortization |
| `capex` | number | Capital expenditure |
| `delta_nwc` | number | Increase in net working capital. Positive means cash tied up, negative means cash released |

Returns: a single number, the period's FCFF.
Raises: `ValueError` if `tax_rate` is not between 0 and 1.

---

## dcf.projection

### `class Assumptions`

Operating assumptions that drive a projection. Fields:

| Field | Type | Meaning |
|-------|------|---------|
| `base_revenue` | number | Year 0 (last actual) revenue |
| `growth` | number or list | A single rate applied every year, or a list of `years` per-year rates |
| `ebit_margin` | number | EBIT as a fraction of revenue |
| `tax_rate` | number 0 to 1 | Tax rate |
| `dna_pct` | number | D&A as a fraction of revenue |
| `capex_pct` | number | Capex as a fraction of revenue |
| `nwc_pct` | number | Net working capital as a fraction of revenue (drives dNWC off the revenue change) |
| `years` | int | Number of years to project. Default 10 |

### `Assumptions.from_base_year(revenue, ebit, dna, capex, nwc, tax_rate, growth, years=10)`

Build an `Assumptions` from base-year dollar figures instead of ratios. Each
ratio is derived by dividing the dollar amount by `revenue`.

| Input | Type | Meaning |
|-------|------|---------|
| `revenue` | number | Base-year revenue |
| `ebit` | number | Base-year operating income |
| `dna` | number | Base-year D&A |
| `capex` | number | Base-year capex |
| `nwc` | number | Base-year net working capital LEVEL (not the change) |
| `tax_rate` | number 0 to 1 | Tax rate |
| `growth` | number or list | Revenue growth, a single rate or a list of `years` rates |
| `years` | int | Projection length. Default 10 |

Returns: an `Assumptions` instance.

### `build_projection(a)`

Project `a.years` of financials and FCFF from an `Assumptions`.

| Input | Type | Meaning |
|-------|------|---------|
| `a` | Assumptions | The assumptions to roll forward |

Returns: a pandas DataFrame indexed by `year` (1 to `years`), with columns
`revenue`, `ebit`, `dna`, `capex`, `delta_nwc`, `fcff`.
Raises: `ValueError` if `growth` is a list whose length is not `years`.

### `projection_from_lists(ebit, dna, capex, delta_nwc, tax_rate, revenue=None)`

Build a projection table from your own per-year forecasts instead of the
constant-growth engine.

| Input | Type | Meaning |
|-------|------|---------|
| `ebit` | list | EBIT per year, one entry per projected year (any length) |
| `dna` | list | D&A per year (same length as `ebit`) |
| `capex` | list | Capex per year (same length) |
| `delta_nwc` | list | Increase in NWC per year (same length) |
| `tax_rate` | number or list | A scalar applied every year, or a per-year list |
| `revenue` | list or None | Optional revenue per year. Needed only if you later value with `exit_metric="sales"` |

Returns: a DataFrame in the same shape as `build_projection`.
Raises: `ValueError` if any list length does not match `ebit`.

---

## dcf.valuation

### `cost_of_equity_capm(risk_free, beta, equity_risk_premium)`

CAPM cost of equity: `Re = Rf + beta * ERP`.

| Input | Type | Meaning |
|-------|------|---------|
| `risk_free` | number | Risk-free rate |
| `beta` | number | Equity beta |
| `equity_risk_premium` | number | Equity risk premium |

Returns: the cost of equity as a decimal.

### `wacc(equity_value, debt_value, cost_of_equity, cost_of_debt, tax_rate)`

Blended cost of capital using market-value weights.

| Input | Type | Meaning |
|-------|------|---------|
| `equity_value` | number | Market value of equity |
| `debt_value` | number | Market value of debt |
| `cost_of_equity` | number | Cost of equity (for example from `cost_of_equity_capm`) |
| `cost_of_debt` | number | Pre-tax cost of debt |
| `tax_rate` | number 0 to 1 | Tax rate, applied to the debt leg for the after-tax shield |

Returns: the WACC as a decimal.

### `pv_explicit(df, rate, column="fcff")`

Present value of an explicit cash-flow stream.

| Input | Type | Meaning |
|-------|------|---------|
| `df` | DataFrame | A projection table indexed by year |
| `rate` | number | Discount rate |
| `column` | str | Which column to discount. Default `"fcff"`. Use `"fcfe"` for the equity stream |

Returns: the present value as a number.

### `enterprise_value(df, wacc, method="gordon", terminal_growth=None, exit_multiple=None, exit_metric="ebitda")`

Assemble enterprise value from a projection and a terminal method.

| Input | Type | Meaning |
|-------|------|---------|
| `df` | DataFrame | A projection table (from `build_projection` or `projection_from_lists`) |
| `wacc` | number | Discount rate |
| `method` | str | `"gordon"` or `"exit"`. Default `"gordon"` |
| `terminal_growth` | number or None | Required when `method="gordon"`. Must be less than `wacc` |
| `exit_multiple` | number or None | Required when `method="exit"` |
| `exit_metric` | str | Which final-year metric the exit multiple is applied to. One of `"ebitda"` (default), `"ebit"`, `"sales"` (also accepts `"revenue"`) |

Returns: a `Valuation` (see below).
Raises: `ValueError` if a required terminal parameter is missing, if `method` is
unknown, if `exit_metric` is unknown, or (for `"sales"`) if the projection has no
revenue column.

### `class Valuation`

The result object returned by `enterprise_value`. Fields:

| Field | Meaning |
|-------|---------|
| `method` | The terminal method used, `"gordon"` or `"exit"` |
| `pv_explicit` | Present value of the explicit FCFF stream |
| `terminal_value` | Terminal value as of the final year, undiscounted |
| `pv_terminal` | That terminal value discounted to today |
| `enterprise_value` | `pv_explicit + pv_terminal` |
| `tv_share` | `pv_terminal / enterprise_value`, the terminal-value fraction |

### `implied_exit_multiple(df, wacc, terminal_growth, metric="ebitda")`

The EV/metric exit multiple that the Gordon terminal value implies.

| Input | Type | Meaning |
|-------|------|---------|
| `df` | DataFrame | A projection table |
| `wacc` | number | Discount rate |
| `terminal_growth` | number | Perpetual growth rate. Must be less than `wacc` |
| `metric` | str | `"ebitda"` (default), `"ebit"`, or `"sales"` |

Returns: the implied multiple as a number. Feeding it back as `exit_multiple`
with the same metric reproduces the Gordon enterprise value exactly.

---

## dcf.terminal

### `gordon_growth_tv(last_fcff, wacc, terminal_growth)`

Terminal value via a growing perpetuity.

| Input | Type | Meaning |
|-------|------|---------|
| `last_fcff` | number | Final explicit-year FCFF |
| `wacc` | number | Discount rate |
| `terminal_growth` | number | Perpetual growth rate. Must be less than `wacc` |

Returns: terminal value as of the final year, undiscounted.
Raises: `ValueError` if `terminal_growth >= wacc`.

### `exit_multiple_tv(last_ebitda, ev_ebitda_multiple)`

Terminal value as a metric times a multiple. (The metric selection happens in
`enterprise_value`. This function just multiplies.)

| Input | Type | Meaning |
|-------|------|---------|
| `last_ebitda` | number | Final-year metric value (EBITDA, EBIT, or sales) |
| `ev_ebitda_multiple` | number | The multiple to apply |

Returns: terminal value as of the final year, undiscounted.

---

## dcf.sensitivity

### `ev_grid(df, wacc_range, g_range)`

Gordon-method enterprise value across a WACC by terminal-growth grid.

| Input | Type | Meaning |
|-------|------|---------|
| `df` | DataFrame | A projection table |
| `wacc_range` | sequence | WACC values, one per row |
| `g_range` | sequence | Terminal growth values, one per column |

Returns: a DataFrame with WACC as the index and growth as the columns. Cells
where `g >= wacc` are `NaN` (the perpetuity is undefined there).

### `divergence_grid(df, wacc_range, g_range, exit_multiple, as_percent=True)`

How far Gordon enterprise value sits from the exit-multiple enterprise value,
across the same grid.

| Input | Type | Meaning |
|-------|------|---------|
| `df` | DataFrame | A projection table |
| `wacc_range` | sequence | WACC values, one per row |
| `g_range` | sequence | Terminal growth values, one per column |
| `exit_multiple` | number | The EV/EBITDA multiple to compare against |
| `as_percent` | bool | If True (default), cells are percent of exit EV. If False, cells are raw value differences |

Returns: a DataFrame. Positive means Gordon values the firm higher than the exit
multiple. Cells where `g >= wacc` are `NaN`.

---

## dcf.plots

### `plot_ev_grid(grid, ax=None, title="Enterprise value - Gordon growth")`

Sequential heatmap of an enterprise-value grid.

| Input | Type | Meaning |
|-------|------|---------|
| `grid` | DataFrame | Output of `ev_grid` |
| `ax` | matplotlib Axes or None | Axis to draw on. A new one is created if omitted |
| `title` | str | Plot title |

Returns: the matplotlib Axes.

### `plot_divergence_grid(grid, ax=None, title="Gordon vs. exit multiple - divergence (%)")`

Diverging heatmap of a divergence grid, with gray pinned at zero (methods agree).

| Input | Type | Meaning |
|-------|------|---------|
| `grid` | DataFrame | Output of `divergence_grid` |
| `ax` | matplotlib Axes or None | Axis to draw on. A new one is created if omitted |
| `title` | str | Plot title |

Returns: the matplotlib Axes.

---

## dcf.fcfe

### `fcfe_direct(net_income, dna, capex, delta_nwc, net_borrowing)`

Free cash flow to equity, bottom-up.

| Input | Type | Meaning |
|-------|------|---------|
| `net_income` | number | Net income (already after interest and tax) |
| `dna` | number | Depreciation and amortization |
| `capex` | number | Capital expenditure |
| `delta_nwc` | number | Increase in net working capital |
| `net_borrowing` | number | New debt raised minus debt repaid. Positive is cash into equity |

Returns: FCFE for the period.

### `fcfe_from_fcff(fcff_value, interest, tax_rate, net_borrowing)`

Free cash flow to equity, built from FCFF.

| Input | Type | Meaning |
|-------|------|---------|
| `fcff_value` | number | The period's FCFF |
| `interest` | number | Interest expense for the period |
| `tax_rate` | number 0 to 1 | Tax rate, for the after-tax interest adjustment |
| `net_borrowing` | number | New debt raised minus debt repaid |

Returns: FCFE for the period. Equal to `fcfe_direct` when inputs are consistent.

### `build_fcfe_projection(a, debt_pct, cost_of_debt)`

Extend an FCFF projection with a constant-debt-ratio schedule and FCFE.

| Input | Type | Meaning |
|-------|------|---------|
| `a` | Assumptions | The operating assumptions |
| `debt_pct` | number | Debt held as a fraction of revenue each year |
| `cost_of_debt` | number | Pre-tax cost of debt, applied to the opening debt balance |

Returns: a DataFrame with the `build_projection` columns plus `interest`,
`net_income`, `net_borrowing`, and `fcfe`.

### `equity_value_fcfe(df, cost_of_equity, terminal_growth)`

Equity value directly: present value of FCFE plus an FCFE Gordon terminal value.

| Input | Type | Meaning |
|-------|------|---------|
| `df` | DataFrame | An FCFE projection (from `build_fcfe_projection`) |
| `cost_of_equity` | number | Discount rate for equity cash flows |
| `terminal_growth` | number | Perpetual growth rate. Must be less than `cost_of_equity` |

Returns: equity value as a number.

### `reconcile_equity(a, wacc, cost_of_equity, cost_of_debt, terminal_growth, debt_pct, cash=0.0)`

Equity value computed two ways, and the gap between them.

| Input | Type | Meaning |
|-------|------|---------|
| `a` | Assumptions | The operating assumptions |
| `wacc` | number | Discount rate for the FCFF (enterprise-value) side |
| `cost_of_equity` | number | Discount rate for the FCFE (direct) side |
| `cost_of_debt` | number | Pre-tax cost of debt |
| `terminal_growth` | number | Perpetual growth rate, used on both sides |
| `debt_pct` | number | Debt as a fraction of revenue |
| `cash` | number | Cash netted against debt for net debt. Default 0 |

Returns: a dict with keys `enterprise_value`, `net_debt`, `equity_indirect`
(enterprise value minus net debt), `equity_direct` (present value of FCFE),
`gap` (direct minus indirect), and `gap_pct` (gap as a percent of indirect).
