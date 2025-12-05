import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"

SCB_PATH         = DATA_DIR / "scb_cpif_components.csv"
WAGES_PATH       = DATA_DIR / "mi_wages.csv"
PP_PATH          = DATA_DIR / "ki_price_plans.csv"
EXPECT_PATH      = DATA_DIR / "ki_inflation_expectations.csv"
ELECTRICITY_PATH = DATA_DIR / "nordpool_electricity_monthly.csv"

OUT_CSV          = DATA_DIR / "features_merged.csv"

# -------------------------------------------------
# Load all datasets
# -------------------------------------------------

scb = pd.read_csv(SCB_PATH, parse_dates=["date"])
wages = pd.read_csv(WAGES_PATH, parse_dates=["date"])
pp = pd.read_csv(PP_PATH, parse_dates=["date"])
exp = pd.read_csv(EXPECT_PATH, parse_dates=["date"])
elec = pd.read_csv(ELECTRICITY_PATH, parse_dates=["date"])

print("SCB columns:", scb.columns.tolist())
print("Wages columns:", wages.columns.tolist())
print("Price plans columns:", pp.columns.tolist())
print("Expectations columns:", exp.columns.tolist())
print("Electricity columns:", elec.columns.tolist())

# In case expectation column name is slightly different, rename second column to infl_exp_households_1y
if exp.columns[1] != "infl_exp_households_1y":
    exp = exp.rename(columns={exp.columns[1]: "infl_exp_households_1y"})

# Same for price plans
if pp.columns[1] != "price_plans_total":
    pp = pp.rename(columns={pp.columns[1]: "price_plans_total"})

# -------------------------------------------------
# Harmonise to monthly period key
# -------------------------------------------------

scb["month"] = scb["date"].dt.to_period("M")
wages["month"] = wages["date"].dt.to_period("M")
exp["month"] = exp["date"].dt.to_period("M")
elec["month"] = elec["date"].dt.to_period("M")

# KI price plans are quarterly. Resample to monthly and forward-fill.
pp = pp.set_index("date").sort_index()

# resample to month end, forward-fill last known quarter value
pp_m = pp.resample("M").ffill().reset_index()
pp_m["month"] = pp_m["date"].dt.to_period("M")

# -------------------------------------------------
# Start from SCB as the base (one row per month)
# -------------------------------------------------

merged = scb.copy()

# Join wages
merged = merged.merge(
    wages[["month", "wage_index", "wage_yoy"]],
    on="month",
    how="left"
)

# Join KI expectations
merged = merged.merge(
    exp[["month", "infl_exp_households_1y"]],
    on="month",
    how="left"
)

# Join Nord Pool electricity
merged = merged.merge(
    elec[["month", "price_se3", "price_se4", "elec_price_avg", "elec_price_index", "elec_price_yoy"]],
    on="month",
    how="left"
)

# Join KI price plans (monthly-fwd-filled)
merged = merged.merge(
    pp_m[["month", "price_plans_total"]],
    on="month",
    how="left"
)

# -------------------------------------------------
# Create lag features and next-month target
# -------------------------------------------------

merged = merged.sort_values("date")

# Lags: one month lag for some key drivers
merged["wage_yoy_lag1"]          = merged["wage_yoy"].shift(1)
merged["elec_price_yoy_lag1"]    = merged["elec_price_yoy"].shift(1)
merged["price_plans_total_lag1"] = merged["price_plans_total"].shift(1)

# Target: next month headline CPI YoY
merged["cpi_yoy_target_next"] = merged["cpi_yoy"].shift(-1)

# -------------------------------------------------
# Clean up and save
# -------------------------------------------------

# Keep 'date' as the main time column, drop 'month'
merged = merged.drop(columns=["month"])

# Optionally, you can drop the earliest row(s) where lags are NaN:
# merged = merged[merged["date"] >= merged["date"].min() + pd.DateOffset(months=1)]

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
merged.to_csv(OUT_CSV, index=False)

print(f"\nSaved merged features to: {OUT_CSV}")
print("Merged columns:", merged.columns.tolist())
print(merged.tail())
