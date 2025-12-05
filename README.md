# Fixathon

1️⃣ scb_cpif_components.csv  – Official inflation backbone
Columns
date
What: First day of each month (e.g. 1981-01-01), representing that calendar month.
Frequency: Monthly.
Used for:
Time axis for all other series (this is your main monthly index).
Merge key when you join the other datasets.
kpi_total_index
What: Level of the consumer price index for the whole economy (KPI/CPIF index, base year = 100).
Units: Index points (e.g. 153.2 with 1995=100 or similar).
Economic meaning: Average price level of the full consumer basket at that time.
Used for:
Raw price-level series for plotting “price level over time”.
Basis for computing cpi_yoy.
Optional: converting wages or electricity into real terms.
kpi_energy_index
What: Index level for the energy-related CPI component (housing/water/electricity/gas/other fuels).
Units: Index points, same base as kpi_total_index.
Economic meaning: How energy prices for households move over time.
Used for:
Tracking how much of inflation is driven by energy.
Comparing with Nord Pool electricity prices.
Basis for cpi_energy_yoy.
cpi_yoy
What: Year-on-year percentage change in the total CPI/KPI index.
Computed as (kpi_total_index / kpi_total_index_12_months_ago - 1) * 100.
Units: Percent (%).
Economic meaning: This is your headline inflation rate – what people mean when they say “inflationen är X procent”.
Used for:
Main target variable for your nowcast/forecast model.
KPI in the dashboard (“Current inflation”).
Comparison against expectations (infl_exp_households_1y).
cpi_energy_yoy
What: Year-on-year % change in the energy CPI component.
Same formula but applied to kpi_energy_index.
Units: Percent (%).
Economic meaning: Energy inflation – how quickly energy-related consumer prices are rising.
Used for:
Building an “Energy pressure” chart or tile.
Comparing against Nord Pool elec_price_yoy to show link from wholesale prices → consumer prices.
Feature in the model if you want to separate energy vs non-energy.


2️⃣ mi_wages.csv – Wage pressure / cost-push inflation
Columns
date
Monthly date (YYYY-MM-01), aligned to the same month grid as SCB.
Merge key with the other datasets.
wage_index
What: Nominal wage index for the whole economy (likely 1995=100 base, seasonally adjusted).
Units: Index points.
Economic meaning: Level of average nominal wages in Sweden over time. Higher index → higher pay.
Used for:
Visual “wage level” chart.
Optional conversion to real wages if you divide by CPI.
Base series for wage_yoy.
wage_yoy
What: Year-on-year percentage change in the wage index.
Units: Percent (%).
Economic meaning: Nominal wage growth – core driver of underlying inflation in most models.
Used for:
“Wage pressure index” tile: is wage growth normal, low, or high vs history / target-consistent level.
Feature in your model for predicting cpi_yoy (especially non-energy inflation).
Explaining Riksbank scenarios (Riksbanken often talks about wages needing to stay below some level).


3️⃣ ki_price_plans.csv – Firms’ price plans (early warning)
Columns
date
What: Quarter-end timestamp (e.g. 2002-03-31 23:59:59.999999999), representing Q1, Q2, etc.
Frequency: Quarterly (Konjunkturbarometern is quarterly for this aggregated series).
Used for:
Aligning the quarterly barometer with monthly data.
In the merge step you can:
Forward-fill each quarter’s value to its three months, or
Keep it as a quarterly feature (used only on quarter months).
price_plans_total
What: The “Medel” indicator for:
Total business sector (“Totala näringslivet”)
Question: “Försäljningspriser (kommande 3 månader)”
Units: Barometer index / net balance (here the values are around 9.0 – in your sample they all happen to be 9).
Economic meaning: Survey-based measure of how firms expect their selling prices to change over the next three months.
Positive and high → many firms expect price increases.
Low or negative → more firms expect stable or falling prices.
Used for:
“Price pressure index” tile: indicating if firms’ planned price changes are above/below normal.
Leading feature in your model: tends to move before actual CPI.
Storytelling: “Our early-warning indicator shows firms are signaling higher price increases ahead.”
4️⃣ ki_inflation_expectations.csv – Households’ inflation expectations
Columns
date
Monthly date (YYYY-MM-01).
Frequency: Monthly.
Aligns directly with SCB inflation and wages.
infl_exp_households_1y
What: Households’ expected inflation 12 months ahead, Medelvärde (mean) from the KI survey.
Units: Percent (%), as reported in the barometer.
Economic meaning: How much inflation households think there will be over the next year.
If it drifts up and stays high, it suggests de-anchored expectations, which central banks care a lot about.
Used for:
Comparing with actual cpi_yoy (to see whether expectations are above or below current inflation).
Model feature: expectations sometimes help forecast future CPI, especially for services and wages via wage bargaining.
Dashboard chart: “Expected vs actual inflation”, plus a text explanation from the LLM.


5️⃣ nordpool_electricity_monthly.csv – Energy shock / real-time signal
Columns
date
What: Month-end date (e.g. 2023-01-31), representing that month’s average electricity price.
Frequency: Monthly; derived from daily spot prices.
Used for:
Time axis and merge key with SCB CPI and other monthly series.
price_se3
What: Monthly average daily spot price in SE3 (central Sweden), in SEK/MWh.
Source: Nord Pool “Daily aggregate” series aggregated by your script.
Economic meaning: Wholesale electricity price for a large part of Sweden’s population and industry.
Used for:
Visualizing regional electricity prices.
Possible feature in a more detailed model that distinguishes regions.
price_se4
What: Same as price_se3 but for SE4 (southern Sweden). Often more volatile and expensive.
Used for:
Comparing price dynamics between zones.
Part of the average used in elec_price_avg.
elec_price_avg
What: Simple average of price_se3 and price_se4 for each month.
Units: SEK/MWh.
Economic meaning: A single, easy-to-understand measure of national electricity price level.
Used for:
Basis for building elec_price_index.
“Energy cost level” plot.
Feature in the inflation model (electricity shocks).
elec_price_index
What: Index of elec_price_avg scaled relative to a base period (average of the first year in your sample = 100).
Units: Index (100 = base-year average).
Economic meaning: Relative electricity price level.
150 means “50% higher than the base-year average”; 50 means “half as high”.
Used for:
“Electricity price shock index” tile with color coding.
Easier comparison over time and across charts (index ~ CPI style).
elec_price_yoy
What: Year-on-year percentage change in elec_price_index.
Units: Percent (%).
Economic meaning: Electricity price inflation at the wholesale level.
Used for:
Early-warning: spikes here usually lead CPI energy inflation (cpi_energy_yoy).
Model feature: helps explain short-term moves in CPI.
LLM explanations: “Electricity prices are X% higher than a year ago, signalling strong energy inflation pressure.”


6️⃣ Big picture – how the pieces fit together
Putting it all together:
SCB (scb_cpif_components.csv)
→ Ground truth for inflation: what has happened to prices (headline & energy).
Medlingsinstitutet (mi_wages.csv)
→ Underlying cost pressure from wages, especially relevant for services & core inflation.
KI price plans (ki_price_plans.csv)
→ Firms’ planned price changes in the next three months – a strong leading indicator.
KI expectations (ki_inflation_expectations.csv)
→ Households’ beliefs about future inflation – expectations channel.
Nord Pool (nordpool_electricity_monthly.csv)
→ High-frequency energy shocks feeding into CPI energy and headline inflation.
These together give you a really coherent story:
Past realized inflation (SCB)
Structural cost pressure (wages)
Forward-looking behavior (price plans, expectations)
Real-time shocks (electricity)
→ Early-warning and short-term forecast of Swedish inflation.
