import pandas as pd
from pathlib import Path

# ---------- paths --------------------
BASE_DIR = Path(__file__).resolve().parents[1]

# Make sure this name matches the XLSX file in data/
RAW_XLSX = BASE_DIR / "data" / "scb_cpif_components_total_and_energy_raw.xlsx"
OUT_CSV  = BASE_DIR / "data" / "scb_cpif_components.csv"

# ---------- read the Excel file ------------
# You may need: pip install openpyxl
df = pd.read_excel(RAW_XLSX, engine="openpyxl")

print("Shape of raw Excel:", df.shape)
print(df.head())

# The structure is:
# row 0: all NaN
# row 1: month labels in columns 1..N (1980M01, 1980M02, ...)
# row 2: "TOTALT" + total KPI values across columns
# row 3: "BOSTÄDER, VATTEN, ELEKTRICITET, GAS OCH ANDRA BRÄNSLEN" + energy values

# --- extract rows we need ---
row_dates  = df.iloc[1, 1:]   # months
row_total  = df.iloc[2, 1:]   # TOTALT values
row_energy = df.iloc[3, 1:]   # energy values

# Build a tidy dataframe
merged = pd.DataFrame({
    "date_raw":         row_dates.values,
    "kpi_total_index":  row_total.values.astype(float),
    "kpi_energy_index": row_energy.values.astype(float),
})

# --- parse date and sort ---
# Convert "1980M01" -> 1980-01-01
merged["date"] = pd.to_datetime(
    merged["date_raw"].astype(str).str.replace("M", "-") + "-01",
    format="%Y-%m-%d"
)

merged = merged.sort_values("date")

# --- compute year-on-year % changes ---
merged["cpi_yoy"]        = merged["kpi_total_index"].pct_change(12) * 100
merged["cpi_energy_yoy"] = merged["kpi_energy_index"].pct_change(12) * 100

# (optional) drop first 12 months where YoY is NaN
merged = merged[merged["date"] >= merged["date"].min() + pd.DateOffset(years=1)]

# --- select final columns and save ---
out = merged[["date", "kpi_total_index", "kpi_energy_index", "cpi_yoy", "cpi_energy_yoy"]]

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
out.to_csv(OUT_CSV, index=False)

print(f"Saved cleaned file to: {OUT_CSV}")
print(out.head())
