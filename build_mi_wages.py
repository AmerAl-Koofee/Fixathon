import re
import pandas as pd
from pathlib import Path

# -------------------------------------------------
# Paths
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]

RAW_XLSX = BASE_DIR / "data" / "mi_wages_total_economy.xlsx"
OUT_CSV  = BASE_DIR / "data" / "mi_wages.csv"

# -------------------------------------------------
# Read raw Excel (no header)
# -------------------------------------------------
# pip install openpyxl if needed
df = pd.read_excel(RAW_XLSX, header=None, engine="openpyxl")

print("Raw shape:", df.shape)
print(df.iloc[:6, :8])  # quick peek

# -------------------------------------------------
# Find the row with month labels: e.g. 2008M01, 2008M02...
# -------------------------------------------------
month_pattern = re.compile(r"^\d{4}M(0[1-9]|1[0-2])$")

header_row_idx = None
for i in range(len(df)):
    row = df.iloc[i]
    if any(isinstance(v, str) and month_pattern.match(v.strip()) for v in row):
        header_row_idx = i
        break

if header_row_idx is None:
    raise ValueError("Could not find a row with month labels like '2008M01'")

header_row = df.iloc[header_row_idx]

# Which columns are the months?
month_cols = [
    j for j, v in header_row.items()
    if isinstance(v, str) and month_pattern.match(v.strip())
]

if not month_cols:
    raise ValueError("Found header row but no month columns")

print("Header row index:", header_row_idx)
print("Month column indices:", month_cols[:10])

# -------------------------------------------------
# Find the data row: first row below header that has numbers under those months
# -------------------------------------------------
data_row_idx = None
for i in range(header_row_idx + 1, len(df)):
    row = df.iloc[i]
    if any(pd.notnull(row[j]) for j in month_cols):
        data_row_idx = i
        break

if data_row_idx is None:
    raise ValueError("Could not find data row under the month headers")

data_row = df.iloc[data_row_idx]
print("Data row index:", data_row_idx)

# -------------------------------------------------
# Build tidy dataframe: one row per month
# -------------------------------------------------
periods = header_row[month_cols].astype(str).str.strip().values
index_values = pd.to_numeric(data_row[month_cols], errors="coerce").values

wages_df = pd.DataFrame({
    "period_raw": periods,          # e.g. 2008M01
    "wage_index": index_values,     # index level
})

wages_df = wages_df.dropna(subset=["wage_index"])

# -------------------------------------------------
# Convert 2008M01 -> proper date
# -------------------------------------------------
wages_df["date"] = pd.to_datetime(
    wages_df["period_raw"].str.replace("M", "-") + "-01",
    format="%Y-%m-%d"
)

wages_df = wages_df.sort_values("date")

# -------------------------------------------------
# Compute year-on-year wage growth (%)
# -------------------------------------------------
wages_df["wage_yoy"] = wages_df["wage_index"].pct_change(12) * 100

# (Optionally drop first 12 months with NaNs)
wages_df = wages_df[wages_df["date"] >= wages_df["date"].min() + pd.DateOffset(years=1)]

# Keep final columns
out = wages_df[["date", "wage_index", "wage_yoy"]]

# -------------------------------------------------
# Save
# -------------------------------------------------
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
out.to_csv(OUT_CSV, index=False)

print(f"Saved cleaned Medlingsinstitutet wages to: {OUT_CSV}")
print(out.head())
