# Time-Series Fundamentals

## Goal

Understand the terminology and patterns used in forecasting/time-series projects.

```text
Observed Time Series
        │
        ├── Trend
        ├── Seasonality
        ├── Cycles
        └── Noise
        │
        ↓
 Historical behavior
        │
        ├── Lags
        └── Rolling statistics
        │
        ↓
 Feature Engineering
        ↓
 Forecasting Model
        ↓
 Future Values
```

## 1. Time Series

A time series is a sequence of observations ordered by time.

```text
Date        Sales
Jan 1       100
Jan 2       120
Jan 3       110
Jan 4       130
```

Unlike many ordinary ML datasets, the ordering of observations matters.

## 2. Frequency

**Frequency = how often observations are recorded.**

Examples:

```text
Hourly
Daily
Weekly
Monthly
Yearly
```

Example:

```text
Jan 1 → 100
Jan 2 → 120
Jan 3 → 110
```

Frequency = **Daily**.

## 3. Granularity

**Granularity = what one row represents.**

Examples:

```text
date + sales
    → Day

date + product_id + sales
    → Product × Day

month + product_id + sales
    → Product × Month
```

Frequency and granularity are different:

```text
Frequency
    → How often observations occur?

Granularity
    → What does one row represent?
```

## 4. Trend

**Trend = the long-term direction of a time series.**

Upward trend:

```text
100
110
120
130
140
150
```

Downward trend:

```text
200
180
160
140
120
```

A series can move down temporarily while still having an overall upward trend.

```text
100 → 110 → 105 → 120 → 115 → 130
```

Overall direction = upward trend with fluctuations.

## 5. Seasonality

**Seasonality = a pattern that repeats at a predictable interval.**

Example:

```text
Monday    → low
Tuesday   → low
Wednesday → medium
Thursday  → medium
Friday    → high
Saturday  → very high
Sunday    → high

Monday    → low
Tuesday   → low
...
Saturday  → very high
Sunday    → high
```

The pattern repeats approximately every 7 days.

Common seasonal periods:

```text
24 hours  → daily pattern
7 days    → weekly pattern
12 months → yearly pattern
```

Key distinction:

```text
Trend
    → What direction is the series moving?

Seasonality
    → Does a pattern repeat at a predictable interval?
```

Trend and seasonality can occur together.

## 6. Cycles

A cycle is a longer-term rise and fall where the duration is not necessarily fixed.

Example:

```text
Economic expansion
      ↓
Slowdown
      ↓
Recession
      ↓
Recovery
      ↓
Expansion
```

Unlike seasonality, the interval is not necessarily predictable.

```text
Seasonality
    → predictable repeating period

Cycle
    → longer irregular fluctuations
```

## 7. Noise

**Noise = unpredictable variation that isn't explained by systematic patterns.**

Example:

```text
95
103
98
105
97
101
```

If the underlying level remains around 100, these fluctuations can be noise/natural variation.

Important:

```text
Noise ≠ Bad Data
```

Noise can represent genuine unpredictable behavior.

A wildly abnormal value such as:

```text
Typical sales → 100–500
One day        → 999,999,999
```

may instead indicate a data-quality problem or extreme outlier.

## 8. Conceptual Decomposition

A useful mental model is:

```text
Observed Sales
      =
Trend
+
Seasonality
+
Cycle
+
Noise
```

Not every time series contains every component.

## 9. Lag

A lag is a previous observation of a time series.

```text
Date        Sales

Jan 1       100
Jan 2       120
Jan 3       110
Jan 4       130
```

For Jan 4:

```text
lag_1 = 110
lag_2 = 120
lag_3 = 100
```

Mental model:

```text
Current value
      │
      ├── lag_1 → previous observation
      ├── lag_2 → 2 observations ago
      └── lag_3 → 3 observations ago
```

Pandas:

```python
df["lag_1"] = df["sales"].shift(1)
```

PostgreSQL:

```sql
LAG(sales, 1) OVER (
    PARTITION BY product_id
    ORDER BY date
)
```

## 10. Useful Forecasting Lags

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

Interpretation:

```text
lag_1  → previous observation
lag_7  → 7 observations ago
lag_30 → 30 observations ago
```

Important:

> `shift(7)` means 7 rows backward, not necessarily exactly 7 calendar days.

Missing dates can make this distinction important.

## 11. Lag and Seasonality

If daily sales have weekly seasonality, `lag_7` can be useful because it represents the same day of the week from the previous week, assuming daily continuous data.

```text
This Monday
     ↑
   lag_7
     ↑
Previous Monday
```

`lag_7` does not create seasonality. If weekly seasonality exists, it may contain useful information about it.

## 12. Difference vs Lag

Lag:

```python
df["lag_1"] = df["sales"].shift(1)
```

Difference:

```python
df["difference"] = (
    df["sales"] - df["sales"].shift(1)
)
```

Example:

```text
sales       lag_1       difference

100         NaN         NaN
120         100         20
110         120         -10
130         110         20
```

Lag = previous value.

Difference = change from previous value.

## 13. Autocorrelation

**Autocorrelation measures how related a time series is to its own previous values.**

Examples:

```text
Lag 1:
Today's sales ↔ Yesterday's sales

Lag 7:
Today's sales ↔ Sales 7 periods ago
```

Mental model:

```text
Autocorrelation at lag N
        ↓
How related is the current value
to the value N periods ago?
```

Positive autocorrelation:

```text
high → high
low  → low
```

Negative autocorrelation:

```text
high → low
low  → high
```

High autocorrelation can suggest a lag is useful, but it does not guarantee that the feature improves a model. Proper validation/backtesting is still required.

Also:

> Autocorrelation indicates statistical dependence, not causation.

## 14. Stationarity

### Good to Know for Now

A time series is intuitively stationary when its statistical behavior is reasonably stable over time.

Example:

```text
100
102
98
101
99
103
100
```

Non-stationary example:

```text
100
120
140
160
180
200
```

The trend causes the level to change.

Mental model:

```text
Stationary
    → behavior is relatively stable over time

Non-stationary
    → behavior changes over time
```

## 15. Differencing

Differencing calculates changes between consecutive observations:

```python
df["difference"] = (
    df["sales"] - df["sales"].shift(1)
)
```

Example:

```text
Original:
100 → 110 → 120 → 130 → 140

Differences:
+10 → +10 → +10 → +10
```

Differencing can help remove a trend and make a series more stationary.

It becomes important when learning ARIMA.

For the crash course, skip the mathematics of ADF, KPSS, unit roots, and formal stationarity proofs.

## 16. Forecast Horizon

**Forecast horizon = how far into the future we want to predict.**

Examples:

```text
Tomorrow
    → 1-day horizon

Next 7 days
    → 7-day horizon

Next 30 days
    → 30-day horizon

Next 12 months
    → 12-month horizon
```

Example:

```text
Frequency:
Daily

Forecast horizon:
7 days
```

Frequency tells us the spacing between observations/predictions.

Forecast horizon tells us how far ahead we predict.

## 17. Univariate Forecasting

Univariate forecasting primarily uses the historical values of one time series.

```text
Past sales
    ↓
Forecast future sales
```

Example:

```text
date
sales
```

## 18. Multivariate Forecasting

Multivariate forecasting uses multiple variables/predictors.

```text
Historical sales
+
Price
+
Promotion
+
Holiday
+
Day of week
        ↓
Future sales
```

This connects directly to regression:

```text
X1 + X2 + X3 → y
```

A forecasting regression dataset might be:

```text
lag_1
lag_7
rolling_mean_7
price
promotion
holiday
day_of_week
        ↓
      sales
```

## 19. Project Example

For:

> Forecast daily product sales for the next 7 days.

We might have:

```text
Frequency:
Daily

Granularity:
Product × Day

Forecast horizon:
7 days

Target:
Sales
```

## 20. Time-Series Mental Model

```text
Daily Product Sales
        │
        ├── Trend
        ├── Weekly Seasonality
        ├── Possible Cycles
        └── Noise
        │
        ↓
Historical observations
        │
        ├── lag_1
        ├── lag_7
        ├── lag_30
        ├── rolling mean
        └── calendar features
        │
        ↓
Feature Engineering
        ↓
Regression / Forecasting Model
        ↓
Next 7 Days
```

## 21. Priority

### 🔴 MUST KNOW

```text
Time series
Frequency
Granularity
Trend
Seasonality
Noise
Lag
Autocorrelation
Forecast horizon
Univariate vs multivariate
```

### 🟡 GOOD TO KNOW

```text
Cycles
Stationarity
Differencing
```

### 🟢 SKIP FOR NOW

```text
ADF mathematics
KPSS mathematics
Unit-root theory
Formal stationarity proofs
Advanced decomposition mathematics
```

## 22. Final Mental Model

When looking at a forecasting dataset, ask:

```text
What does one row represent?
    → Granularity

How often are observations recorded?
    → Frequency

Is the series moving up/down over time?
    → Trend

Does a pattern repeat at a predictable interval?
    → Seasonality

Are there longer irregular fluctuations?
    → Cycle

What variation is unpredictable?
    → Noise

Does the past relate to the present?
    → Autocorrelation

How far ahead are we predicting?
    → Forecast Horizon

Are we using one series or additional variables?
    → Univariate / Multivariate
```

The most important distinctions:

```text
Trend
    → long-term direction

Seasonality
    → predictable repeating pattern

Lag
    → previous value

Autocorrelation
    → relationship with previous values

Frequency
    → how often observations occur

Granularity
    → what one row represents

Forecast Horizon
    → how far ahead we predict
```

## Next Lesson

Feature Engineering for Forecasting:

```text
lag_1
lag_7
lag_30
rolling mean
rolling std
expanding statistics
day/week/month
holidays
promotions
external variables
        ↓
Supervised regression
        ↓
Data leakage
```
