import re
import pandas as pd
from pathlib import Path

# -------------------------------------------------
# Paths
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]

RAW_XLSX = BASE_DIR / "data" / "ki_inflation_expectations_households.xlsx"
OUT_CSV  = BASE_DIR / "data" / "ki_inflation_expectations.csv"

# -------------------------------------------------
# Read raw Excel (no header)
# -------------------------------------------------
# You might need: pip install openpyxl
df = pd.read_excel(RAW_XLSX, header=None, engine="openpyxl")

print("Raw shape:", df.shape)
print(df.iloc[:6, :8])  # first 6 rows, 8 cols for a quick peek

# -------------------------------------------------
# Find the row that contains the period labels: 2000M01, 2000M02, ...
# -------------------------------------------------
month_pattern = re.compile(r"^\d{4}M(0[1-9]|1[0-2])$")

header_row_idx = None
for i in range(len(df)):
    row = df.iloc[i]
    if any(isinstance(v, str) and month_pattern.match(v.strip()) for v in row):
        header_row_idx = i
        break

if header_row_idx is None:
    raise ValueError("Could not find a row with month labels like '2000M01'")

header_row = df.iloc[header_row_idx]

# Which columns have those period labels?
month_cols = [
    j for j, v in header_row.items()
    if isinstance(v, str) and month_pattern.match(v.strip())
]

if not month_cols:
    raise ValueError("Found header row but no month columns")

print("Header row index:", header_row_idx)
print("Month column indices:", month_cols[:10])

# -------------------------------------------------
# Find the data row: first row below header that has numbers in those month columns
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
# Build tidy dataframe
# -------------------------------------------------
periods = header_row[month_cols].astype(str).str.strip().values
values  = pd.to_numeric(data_row[month_cols], errors="coerce").values

exp_df = pd.DataFrame({
    "period_raw": periods,
    "infl_exp_households_1y": values,
})

# Drop any columns that were empty / NaN
exp_df = exp_df.dropna(subset=["infl_exp_households_1y"])

# -------------------------------------------------
# Convert 2000M01 -> proper monthly date (use first day of month)
# -------------------------------------------------
exp_df["date"] = pd.to_datetime(
    exp_df["period_raw"].str.replace("M", "-") + "-01",
    format="%Y-%m-%d"
)

exp_df = exp_df.sort_values("date")

# Keep only the columns we want
out = exp_df[["date", "infl_exp_households_1y"]]

# -------------------------------------------------
# Save to CSV
# -------------------------------------------------
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
out.to_csv(OUT_CSV, index=False)

print(f"Saved cleaned KI inflation expectations to: {OUT_CSV}")
print(out.head())
