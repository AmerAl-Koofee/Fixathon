import re
import pandas as pd
from pathlib import Path

# ---------- paths --------------------
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_XLSX = BASE_DIR / "data" / "ki_price_plans_total_business.xlsx"
OUT_CSV  = BASE_DIR / "data" / "ki_price_plans.csv"

# ---------- read raw Excel (no header) ------------
# (pip install openpyxl if needed)
df = pd.read_excel(RAW_XLSX, header=None, engine="openpyxl")

print("Raw shape:", df.shape)
print(df.iloc[:6, :10])   # first 6 rows, 10 cols just for debugging

# ---------- find the row with quarter labels (2002Q1, 2002Q2, ...) ----
quarter_pattern = re.compile(r"^\d{4}Q[1-4]$")

header_row_idx = None
for i in range(len(df)):
    row = df.iloc[i]
    if any(isinstance(v, str) and quarter_pattern.match(v.strip()) for v in row):
        header_row_idx = i
        break

if header_row_idx is None:
    raise ValueError("Could not find a row with quarter labels like '2002Q1'")

header_row = df.iloc[header_row_idx]

# column indices that contain quarter codes
quarter_cols = [
    j for j, v in header_row.items()
    if isinstance(v, str) and quarter_pattern.match(v.strip())
]

if not quarter_cols:
    raise ValueError("Found header row but no quarter columns")

start_col = min(quarter_cols)

print("Header row index:", header_row_idx)
print("Quarter columns (indexes):", quarter_cols)

# ---------- find the data row (first row below header that has numbers) ----
data_row_idx = None
for i in range(header_row_idx + 1, len(df)):
    row = df.iloc[i]
    if any(pd.notnull(row[j]) for j in quarter_cols):
        data_row_idx = i
        break

if data_row_idx is None:
    raise ValueError("Could not find data row with values under quarter headers")

data_row = df.iloc[data_row_idx]

print("Data row index:", data_row_idx)

# ---------- build tidy dataframe ----------------------------------------
periods = header_row[quarter_cols].astype(str).str.strip().values
values = pd.to_numeric(data_row[quarter_cols], errors="coerce").values

price_plans_df = pd.DataFrame({
    "period_raw": periods,
    "price_plans_total": values,
})

# drop any columns that were empty / NaN
price_plans_df = price_plans_df.dropna(subset=["price_plans_total"])

# ---------- convert 2002Q1 -> proper date (quarter end) -----------------
period_index = pd.PeriodIndex(price_plans_df["period_raw"], freq="Q")
price_plans_df["date"] = period_index.to_timestamp(how="end")  # e.g. 2002Q1 -> 2002-03-31

# sort and keep tidy columns
price_plans_df = price_plans_df.sort_values("date")
out = price_plans_df[["date", "price_plans_total"]]

# ---------- save --------------------------------------------------------
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
out.to_csv(OUT_CSV, index=False)

print(f"Saved cleaned KI price plans to: {OUT_CSV}")
print(out.head())
