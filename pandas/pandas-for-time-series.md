# Pandas for Time-Series Forecasting

## Goal

Use Pandas to transform SQL-extracted data into a clean, time-aware forecasting dataset.

```text
PostgreSQL
    ↓
Pandas DataFrame
    ↓
Datetime handling
    ↓
Sorting
    ↓
Resampling / aggregation
    ↓
Lag features
    ↓
Rolling features
    ↓
Calendar features
    ↓
ML-ready forecasting dataset
```

## 1. Datetime

Convert strings to datetime:

```python
df["date"] = pd.to_datetime(df["date"])
```

Useful datetime properties:

```python
df["date"].dt.year
df["date"].dt.month
df["date"].dt.day
df["date"].dt.dayofweek
```

Example:

```python
df["day_of_week"] = df["date"].dt.dayofweek
```

Monday = 0, Sunday = 6.

## 2. Sort by Time

Time-series operations depend on chronological order.

```python
df = df.sort_values("date")
```

For multiple products:

```python
df = df.sort_values(["product_id", "date"])
```

Always pay attention to ordering before `shift()` and `rolling()`.

## 3. Datetime Index

```python
df = df.set_index("date")
```

A datetime index makes Pandas time-series operations such as `resample()` natural.

## 4. resample()

`resample()` changes time frequency and usually aggregates.

Daily → weekly:

```python
weekly_sales = df["sales"].resample("W").sum()
```

Daily → monthly:

```python
monthly_sales = df["sales"].resample("ME").sum()
```

Common frequencies:

```text
"D"  → day
"W"  → week
"ME" → month-end
"H"  → hour
```

SQL equivalent concept:

```sql
DATE_TRUNC('month', order_date)
```

## 5. groupby()

Groups by values/categories.

```python
df.groupby("product_id")["sales"].sum()
```

Multiple columns:

```python
df.groupby(["date", "product_id"])["sales"].sum()
```

Conceptually equivalent to SQL `GROUP BY`.

`groupby()` groups by values; `resample()` groups by time intervals.

They can be combined:

```python
daily_sales = (
    df.groupby("product_id")
      .resample("D")["quantity"]
      .sum()
)
```

## 6. shift() — Pandas Equivalent of LAG()

PostgreSQL:

```sql
LAG(sales, 1) OVER (
    PARTITION BY product_id
    ORDER BY date
)
```

Pandas:

```python
df["lag_1"] = (
    df.groupby("product_id")["sales"]
      .shift(1)
)
```

Example:

```text
date   product   sales   lag_1
Jan 1  101       100     NaN
Jan 2  101       120     100
Jan 3  101       110     120
Jan 4  101       130     110
```

## 7. Multiple Lag Features

Common forecasting features:

```python
df["lag_1"] = (
    df.groupby("product_id")["sales"].shift(1)
)

df["lag_7"] = (
    df.groupby("product_id")["sales"].shift(7)
)

df["lag_30"] = (
    df.groupby("product_id")["sales"].shift(30)
)
```

Important:

> `shift(7)` means 7 observations backward, not necessarily exactly 7 calendar days.

Missing dates can make this distinction important.

## 8. rolling()

A rolling window calculates statistics over a moving window.

```python
df["rolling_mean_3"] = (
    df["sales"].rolling(3).mean()
)
```

For:

```text
100
120
110
130
140
```

the result is:

```text
100 → NaN
120 → NaN
110 → 110
130 → 120
140 → 126.667
```

Other useful statistics:

```python
df["rolling_mean_7"] = df["sales"].rolling(7).mean()
df["rolling_std_7"] = df["sales"].rolling(7).std()
df["rolling_min_7"] = df["sales"].rolling(7).min()
df["rolling_max_7"] = df["sales"].rolling(7).max()
df["rolling_sum_7"] = df["sales"].rolling(7).sum()
```

## 9. Rolling Features Per Product

```python
df["rolling_mean_3"] = (
    df.groupby("product_id")["sales"]
      .rolling(3)
      .mean()
      .reset_index(level=0, drop=True)
)
```

The rolling calculation should operate independently for each forecasting entity.

## 10. Preventing Leakage in Rolling Features

Suppose we predict Jan 5:

```text
Jan 1 → 100
Jan 2 → 120
Jan 3 → 110
Jan 4 → 130
Jan 5 → 140  ← target
```

This can leak the target:

```python
df["rolling_mean_3"] = df["sales"].rolling(3).mean()
```

For a historical feature, exclude the current observation:

```python
df["rolling_mean_3"] = (
    df["sales"]
      .shift(1)
      .rolling(3)
      .mean()
)
```

Mental model:

```text
sales
  ↓
shift(1)
  ↓
exclude current target
  ↓
rolling(3)
  ↓
historical rolling feature
```

This is one of the most important forecasting feature-engineering patterns.

## 11. Missing Dates

Example:

```text
Jan 1 → 100
Jan 2 → 120
Jan 3 → 110
Jan 5 → 130
Jan 6 → 140
```

Jan 4 is missing.

Do not automatically assume:

```text
missing row = zero
```

Possible meanings:

```text
No row
  ↓
Could mean zero activity
OR
Could mean missing data
OR
Could indicate a pipeline failure
```

Business/data rules determine the meaning.

Keep these distinct:

```text
No row
NULL
0
```

## 12. pd.date_range()

Create an expected continuous date range:

```python
date_range = pd.date_range(
    start="2026-01-01",
    end="2026-01-06",
    freq="D"
)
```

This is conceptually similar to PostgreSQL `generate_series()`.

## 13. reindex()

First:

```python
df = df.set_index("date")
```

Then:

```python
df = df.reindex(date_range)
```

A missing Jan 4 becomes explicit:

```text
            sales
Jan 1       100
Jan 2       120
Jan 3       110
Jan 4       NaN
Jan 5       130
Jan 6       140
```

Do not immediately do:

```python
df["sales"] = df["sales"].fillna(0)
```

First confirm the business meaning.

## 14. reindex() vs resample()

`reindex()`:

> Make sure a specific expected index exists.

```python
df.reindex(pd.date_range(...))
```

`resample()`:

> Aggregate data at a time frequency.

```python
df.resample("D").sum()
```

They solve different problems.

## 15. merge() — Pandas Equivalent of SQL JOIN

```python
result = daily_sales.merge(
    products,
    on="product_id",
    how="inner"
)
```

SQL equivalent:

```sql
SELECT
    ds.date,
    ds.product_id,
    p.category,
    ds.sales
FROM daily_sales AS ds
JOIN products AS p
    ON ds.product_id = p.product_id;
```

Mapping:

```text
SQL              Pandas
INNER JOIN       how="inner"
LEFT JOIN        how="left"
RIGHT JOIN       how="right"
FULL OUTER JOIN  how="outer"
ON product_id    on="product_id"
```

## 16. Beware Duplicate Merge Keys

If the right-side table contains duplicate `product_id` values, a merge can duplicate forecasting observations.

Before merging, ask:

> Is the merge key unique on the side being joined?

This is a common real-world data engineering issue.

## 17. Calendar Features

```python
df["date"] = pd.to_datetime(df["date"])

df["day_of_week"] = df["date"].dt.dayofweek
df["month"] = df["date"].dt.month
df["day"] = df["date"].dt.day
df["week"] = df["date"].dt.isocalendar().week

df["is_weekend"] = (
    df["date"].dt.dayofweek >= 5
).astype(int)
```

These allow models to learn calendar effects.

## 18. End-to-End Feature Preparation

Start with:

```text
date
product_id
sales
```

Sort:

```python
df = df.sort_values(["product_id", "date"])
```

Create lags:

```python
df["lag_1"] = (
    df.groupby("product_id")["sales"].shift(1)
)

df["lag_7"] = (
    df.groupby("product_id")["sales"].shift(7)
)
```

Create a historical rolling mean:

```python
df["rolling_mean_7"] = (
    df.groupby("product_id")["sales"]
      .transform(
          lambda x: x.shift(1).rolling(7).mean()
      )
)
```

Calendar features:

```python
df["day_of_week"] = df["date"].dt.dayofweek

df["is_weekend"] = (
    df["day_of_week"] >= 5
).astype(int)
```

Result:

```text
date
product_id
sales
lag_1
lag_7
rolling_mean_7
day_of_week
is_weekend
```

This is much closer to a supervised ML dataset.

## 19. SQL ↔ Pandas Cheat Sheet

| Concept | PostgreSQL | Pandas |
|---|---|---|
| Convert datetime | `CAST(... AS timestamp)` | `pd.to_datetime()` |
| Sort | `ORDER BY date` | `sort_values()` |
| Group | `GROUP BY` | `groupby()` |
| Time aggregation | `DATE_TRUNC()` | `resample()` |
| Previous row | `LAG()` | `shift()` |
| Next row | `LEAD()` | `shift(-1)` |
| Partition | `PARTITION BY` | `groupby()` |
| Rolling | Window frame | `rolling()` |
| JOIN | `JOIN` | `merge()` |
| Generate dates | `generate_series()` | `pd.date_range()` |
| Fill expected index | Calendar + `LEFT JOIN` | `reindex()` |

## 20. Forecasting Pandas Checklist

### Datetime
- Is the date actually datetime?
- Is the data sorted chronologically?

### Granularity
- What does one row represent?
- Product × Day?
- Product × Week?

### Lag
- Is `shift()` performed within the correct entity?
- Is the data continuous?
- Does `shift(7)` really represent 7 days?

### Rolling
- Does the rolling feature include the current target?
- Should `.shift(1)` be applied first?
- Is the rolling calculation performed per product?

### Missing data
- Are missing dates present?
- Are missing values actually zero?
- Was the business meaning confirmed?

### Merge
- Is the merge key unique?
- Can the merge duplicate observations?
- Is the correct join type being used?

### Leakage
- Does any feature use information unavailable at prediction time?

## 21. Priority

### 🔴 MUST KNOW

```text
pd.to_datetime()
sort_values()
set_index()
groupby()
resample()
shift()
rolling()
date_range()
reindex()
merge()
calendar features
lag features
historical rolling features
time-series leakage
```

### 🟡 GOOD TO KNOW

```text
MultiIndex
transform()
Advanced resampling
Time zones
Advanced merge validation
```

### 🟢 SKIP FOR NOW

```text
Pandas internals
NumPy optimization
Custom extension arrays
Advanced indexing internals
Performance micro-optimization
```

## 22. Key Mental Model

```text
SQL extraction
      ↓
Pandas DataFrame
      ↓
Convert datetime
      ↓
Sort chronologically
      ↓
Set datetime index when useful
      ↓
Resample / aggregate
      ↓
Create continuous time index
      ↓
Investigate missing dates
      ↓
Merge external data
      ↓
Create lag features
      ↓
Create historical rolling features
      ↓
Create calendar features
      ↓
ML-ready forecasting dataset
```

Most important rule:

> **Every feature must represent information that would actually be available at the time the prediction is made.**
