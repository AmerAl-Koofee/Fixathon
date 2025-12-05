import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

RAW_XLSX = BASE_DIR / "data" / "nordpool_daily_se3_se4_2023_2025.xlsx"
OUT_CSV  = BASE_DIR / "data" / "nordpool_electricity_monthly.csv"

# -------------------------------------------------
# Read all sheets (2023, 2024, 2025) from the Excel
# -------------------------------------------------
# pip install openpyxl if needed
sheets = pd.read_excel(RAW_XLSX, sheet_name=None, engine="openpyxl")

frames = []

for year, df in sheets.items():
    print(f"Sheet {year}: columns -> {df.columns.tolist()[:5]}")
    # Keep only the columns we care about
    df = df[["Deliver Date CET", "SE3 (SEK)", "SE4 (SEK)"]].copy()
    df.rename(
        columns={
            "Deliver Date CET": "date",
            "SE3 (SEK)": "price_se3",
            "SE4 (SEK)": "price_se4",
        },
        inplace=True,
    )
    frames.append(df)

# Stack all years into one DataFrame
daily = pd.concat(frames, ignore_index=True)

# -------------------------------------------------
# Parse dates and convert prices to numeric
# -------------------------------------------------
daily["date"] = pd.to_datetime(daily["date"])
daily["price_se3"] = pd.to_numeric(daily["price_se3"], errors="coerce")
daily["price_se4"] = pd.to_numeric(daily["price_se4"], errors="coerce")

daily = daily.dropna(subset=["price_se3", "price_se4"])

print("Daily data sample:")
print(daily.head())

# -------------------------------------------------
# Create month column (month end) and aggregate
# -------------------------------------------------
daily["month"] = daily["date"].dt.to_period("M").dt.to_timestamp("M")

monthly = (
    daily.groupby("month")[["price_se3", "price_se4"]]
         .mean()
         .reset_index()
         .rename(columns={"month": "date"})
)

# National-ish average of SE3 & SE4
monthly["elec_price_avg"] = monthly[["price_se3", "price_se4"]].mean(axis=1)

# -------------------------------------------------
# Build index and YoY changes
# -------------------------------------------------
monthly = monthly.sort_values("date")

# Base = average of the first year in the sample
first_year = monthly["date"].dt.year.min()
base_mask = monthly["date"].dt.year == first_year
base_mean = monthly.loc[base_mask, "elec_price_avg"].mean()

monthly["elec_price_index"] = monthly["elec_price_avg"] / base_mean * 100
monthly["elec_price_yoy"] = monthly["elec_price_index"].pct_change(12) * 100

# -------------------------------------------------
# Save
# -------------------------------------------------
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
monthly.to_csv(OUT_CSV, index=False)

print(f"\nSaved monthly Nord Pool prices to: {OUT_CSV}")
print(monthly.head())
