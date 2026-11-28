# SQL for Forecasting — PostgreSQL

## Goal

Use PostgreSQL to extract, aggregate, validate, and prepare time-series data for forecasting.

Core pipeline:

```text
Raw transactional data
        ↓
      SQL
        ↓
Time-series dataset
        ↓
Feature engineering
        ↓
Forecast model
```

---

# 1. Forecasting Dataset and Granularity

## Granularity

**Granularity = what one row represents.**

Examples:

| Columns | Granularity |
|---|---|
| `date, sales` | Day |
| `date, product_id, sales` | Product × Day |
| `month, sales` | Month |
| `month, product_id, sales` | Product × Month |

Always determine the desired granularity before writing the query.

Example business requirement:

> Forecast sales for each product every day.

Therefore:

```text
Granularity = Product × Day
```

---

# 2. SELECT and WHERE

## `SELECT`

Choose the columns/calculations needed.

```sql
SELECT
    product_id,
    quantity
FROM orders;
```

## `WHERE`

Filters rows.

```sql
SELECT
    product_id,
    quantity
FROM orders
WHERE order_date >= DATE '2026-01-01';
```

Mental model:

```text
WHERE
  ↓
Which rows do I want?
```

For forecasting, filtering is often used to:

- select the historical training period
- exclude irrelevant records
- reduce the amount of data processed

Example:

```sql
WHERE order_date >= DATE '2024-01-01'
```

---

# 3. GROUP BY and Aggregations

Forecasting often starts with transactional data.

Example `orders`:

```text
id | product_id | order_date | quantity
---|------------|------------|---------
1  | 101        | 2026-01-01 | 2
2  | 101        | 2026-01-01 | 3
3  | 102        | 2026-01-01 | 5
4  | 101        | 2026-01-02 | 4
```

We want daily sales per product.

```sql
SELECT
    order_date,
    product_id,
    SUM(quantity) AS sales
FROM orders
GROUP BY
    order_date,
    product_id;
```

Result:

```text
date        product_id   sales
2026-01-01  101          5
2026-01-01  102          5
2026-01-02  101          4
```

Key distinction:

```text
WHERE
    ↓
filters rows

GROUP BY
    ↓
defines groups / granularity

SUM / AVG / COUNT
    ↓
calculates values for each group
```

---

# 4. Date/Time Aggregation with DATE_TRUNC

Raw orders often contain timestamps:

```text
2026-01-01 10:32:15
2026-01-01 14:21:08
2026-01-02 09:15:42
```

For daily forecasting, exact time may not matter.

PostgreSQL:

```sql
DATE_TRUNC('day', order_date)
```

Daily aggregation:

```sql
SELECT
    DATE_TRUNC('day', order_date) AS date,
    product_id,
    SUM(quantity) AS sales
FROM orders
GROUP BY
    DATE_TRUNC('day', order_date),
    product_id
ORDER BY
    date,
    product_id;
```

Other useful PostgreSQL frequencies:

```sql
DATE_TRUNC('hour', order_date)
DATE_TRUNC('day', order_date)
DATE_TRUNC('week', order_date)
DATE_TRUNC('month', order_date)
DATE_TRUNC('year', order_date)
```

Example monthly aggregation:

```sql
SELECT
    DATE_TRUNC('month', order_date) AS month,
    product_id,
    SUM(quantity) AS sales
FROM orders
GROUP BY
    DATE_TRUNC('month', order_date),
    product_id
ORDER BY
    month,
    product_id;
```

---

# 5. JOINs

Forecasting datasets often need information from multiple tables.

Example:

```text
orders
-------
product_id
order_date
quantity

products
--------
product_id
category
price
```

Join using the shared key:

```sql
SELECT
    o.product_id,
    p.category,
    p.price,
    o.quantity
FROM orders AS o
JOIN products AS p
    ON o.product_id = p.product_id;
```

## INNER JOIN

Keeps matching records from both tables.

```sql
FROM orders AS o
JOIN products AS p
    ON o.product_id = p.product_id
```

If Product 103 doesn't exist in `products`, its order will not appear in the result.

## LEFT JOIN

Keeps every row from the left table.

```sql
FROM orders AS o
LEFT JOIN products AS p
    ON o.product_id = p.product_id
```

If Product 103 has no matching product:

```text
product_id | category
-----------|---------
103        | NULL
```

This is useful for **data-quality investigation**.

Mental model:

```text
LEFT JOIN
    ↓
Preserve every row from the left table
    ↓
Unmatched right-side values become NULL
```

---

# 6. CTE — Common Table Expression

A CTE is a named intermediate result used within a query.

Syntax:

```sql
WITH name AS (
    SELECT ...
)
SELECT ...
FROM name;
```

Think of it like a Python variable:

```python
daily_sales = create_daily_sales(...)
result = enrich(daily_sales)
```

SQL:

```sql
WITH daily_sales AS (
    SELECT ...
)
SELECT ...
FROM daily_sales;
```

## Forecasting example

First create the desired Product × Day granularity:

```sql
WITH daily_sales AS (
    SELECT
        DATE_TRUNC('day', order_date) AS date,
        product_id,
        SUM(quantity) AS sales
    FROM orders
    WHERE order_date >= DATE '2026-01-01'
    GROUP BY
        DATE_TRUNC('day', order_date),
        product_id
)

SELECT
    ds.date,
    ds.product_id,
    p.category,
    p.price,
    ds.sales
FROM daily_sales AS ds
JOIN products AS p
    ON ds.product_id = p.product_id
ORDER BY
    ds.date,
    ds.product_id;
```

A CTE:

- is not a permanent table
- exists within the query
- helps break complex transformations into logical stages

Example multi-stage pipeline:

```sql
WITH daily_sales AS (
    ...
),
daily_promotions AS (
    ...
),
daily_holidays AS (
    ...
),
forecasting_dataset AS (
    ...
)
SELECT *
FROM forecasting_dataset;
```

Mental model:

```text
orders
  ↓
daily_sales
  ↓
daily_promotions
  ↓
daily_holidays
  ↓
forecasting_dataset
```

---

# 7. Window Functions

A window function calculates across related rows **without collapsing the rows**.

## GROUP BY vs Window Function

`GROUP BY`:

```sql
SELECT
    product_id,
    SUM(sales) AS total_sales
FROM daily_sales
GROUP BY product_id;
```

Produces one row per product.

A window function:

```sql
SELECT
    date,
    product_id,
    sales,
    SUM(sales) OVER (
        PARTITION BY product_id
    ) AS total_product_sales
FROM daily_sales;
```

Keeps the original rows:

```text
date   product   sales   total_product_sales
Jan 1  101       100     460
Jan 2  101       120     460
Jan 3  101       110     460
Jan 4  101       130     460
```

Mental model:

```text
GROUP BY
    ↓
collapse rows

Window function
    ↓
calculate across related rows
while keeping original rows
```

---

# 8. LAG()

`LAG()` looks backward.

Example:

```sql
SELECT
    date,
    product_id,
    sales,
    LAG(sales, 1) OVER (
        PARTITION BY product_id
        ORDER BY date
    ) AS lag_1
FROM daily_sales;
```

Result:

```text
date   product   sales   lag_1
Jan 1  101       100     NULL
Jan 2  101       120     100
Jan 3  101       110     120
Jan 4  101       130     110
```

`PARTITION BY product_id` means:

> Calculate the lag independently for each product.

`ORDER BY date` defines the time order.

### Forecasting use

Create `lag_1`:

```sql
LAG(sales, 1) OVER (
    PARTITION BY product_id
    ORDER BY date
) AS lag_1
```

Create `lag_7`:

```sql
LAG(sales, 7) OVER (
    PARTITION BY product_id
    ORDER BY date
) AS lag_7
```

Important:

> `LAG(sales, 7)` means 7 rows backward, not necessarily exactly 7 calendar days.

Missing dates can therefore cause problems.

---

# 9. LEAD()

`LEAD()` looks forward.

```sql
SELECT
    date,
    sales,
    LEAD(sales, 1) OVER (
        PARTITION BY product_id
        ORDER BY date
    ) AS next_day_sales
FROM daily_sales;
```

Example:

```text
date   sales   next_day_sales
Jan 1  100     120
Jan 2  120     110
Jan 3  110     130
Jan 4  130     NULL
```

Forecasting warning:

`LEAD()` can expose future information.

Using future sales as a model feature can create **data leakage**.

---

# 10. Rolling Averages

A rolling average summarizes a moving window of observations.

Example:

```text
sales:
100
120
110
130
140
```

Three-row rolling averages:

```text
Jan 3 → (100 + 120 + 110) / 3 = 110
Jan 4 → (120 + 110 + 130) / 3 = 120
Jan 5 → (110 + 130 + 140) / 3 = 126.667
```

PostgreSQL:

```sql
SELECT
    date,
    sales,
    AVG(sales) OVER (
        ORDER BY date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS rolling_3_day_avg
FROM daily_sales
ORDER BY date;
```

Important:

```sql
ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
```

means:

```text
[2 PRECEDING, CURRENT ROW]
```

Both endpoints are included.

That's 3 rows total.

---

# 11. Historical Rolling Features and Leakage

When predicting the current day's sales, we don't know the current value yet.

Therefore, using the current value in the feature can cause leakage.

For a 3-row historical average excluding the current row:

```sql
AVG(sales) OVER (
    PARTITION BY product_id
    ORDER BY date
    ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
) AS rolling_mean_3
```

For Jan 4:

```text
Jan 1 → 100
Jan 2 → 120
Jan 3 → 110
Jan 4 → 130  ← being predicted
```

The feature uses:

```text
100, 120, 110
```

not `130`.

---

# 12. BETWEEN in Window Frames

In:

```sql
ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
```

`BETWEEN` is inclusive.

Conceptually:

```text
[3 PRECEDING, 1 PRECEDING]
```

For the current Jan 4 row:

```text
Jan 1 → 3 PRECEDING ✓
Jan 2 → 2 PRECEDING ✓
Jan 3 → 1 PRECEDING ✓
Jan 4 → CURRENT ROW ✗
```

Useful patterns:

```sql
-- Current + previous 2 rows
ROWS BETWEEN 2 PRECEDING AND CURRENT ROW

-- Previous 3 rows, excluding current
ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING

-- Previous 7 rows, excluding current
ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
```

---

# 13. Missing Dates

A time series may contain:

```text
Jan 1
Jan 2
Jan 3
Jan 5
Jan 6
```

Jan 4 is missing.

Important:

> **Missing row does not automatically mean zero sales.**

Possible meanings:

```text
No row
  ↓
Could mean zero activity
OR
Could mean missing data
OR
Could mean pipeline failure
```

Business/data rules must determine the meaning.

Keep these concepts distinct:

```text
No row
NULL value
0 value
```

They are not automatically equivalent.

---

# 14. generate_series()

PostgreSQL's `generate_series()` can generate a continuous date range.

```sql
SELECT
    generate_series(
        DATE '2026-01-01',
        DATE '2026-01-05',
        INTERVAL '1 day'
    )::date AS date;
```

Result:

```text
2026-01-01
2026-01-02
2026-01-03
2026-01-04
2026-01-05
```

This is useful for identifying missing dates.

A common pattern is:

```text
Complete calendar
       ↓
LEFT JOIN
       ↓
Actual observations
       ↓
Identify missing dates
```

Example:

```sql
WITH calendar AS (
    SELECT
        generate_series(
            DATE '2026-01-01',
            DATE '2026-01-07',
            INTERVAL '1 day'
        )::date AS date
)
SELECT
    c.date,
    ds.sales
FROM calendar AS c
LEFT JOIN daily_sales AS ds
    ON ds.date = c.date
ORDER BY c.date;
```

Now missing dates become visible as `NULL`.

Do not automatically replace them with zero without confirming the business meaning.

---

# 15. Complete Forecasting SQL Example

Suppose:

```text
orders
-------
product_id
order_date
quantity
```

and:

```text
products
--------
product_id
category
price
```

We want daily sales per product, with product metadata and historical lag features.

```sql
WITH daily_sales AS (
    SELECT
        DATE_TRUNC('day', o.order_date)::date AS date,
        o.product_id,
        SUM(o.quantity) AS sales
    FROM orders AS o
    WHERE o.order_date >= DATE '2026-01-01'
    GROUP BY
        DATE_TRUNC('day', o.order_date)::date,
        o.product_id
),

forecasting_dataset AS (
    SELECT
        ds.date,
        ds.product_id,
        p.category,
        p.price,
        ds.sales,

        LAG(ds.sales, 1) OVER (
            PARTITION BY ds.product_id
            ORDER BY ds.date
        ) AS lag_1,

        LAG(ds.sales, 7) OVER (
            PARTITION BY ds.product_id
            ORDER BY ds.date
        ) AS lag_7,

        AVG(ds.sales) OVER (
            PARTITION BY ds.product_id
            ORDER BY ds.date
            ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
        ) AS rolling_mean_7

    FROM daily_sales AS ds
    JOIN products AS p
        ON ds.product_id = p.product_id
)

SELECT *
FROM forecasting_dataset
ORDER BY
    product_id,
    date;
```

Conceptually:

```text
orders
  ↓
daily aggregation
  ↓
Product × Day
  ↓
JOIN product metadata
  ↓
LAG features
  ↓
Rolling features
  ↓
Forecasting dataset
```

---

# 16. Forecasting SQL Checklist

When reading SQL in a forecasting project, ask:

### Data source

- Which tables are being used?
- What does each table represent?

### Granularity

- What does one row represent?
- Product × Day?
- Product × Week?
- Region × Month?

### Time

- What date column is being used?
- What forecasting frequency is being created?
- Is the data continuous?

### Aggregation

- What is being summed/averaged?
- Could aggregation accidentally change the intended granularity?

### JOINs

- What keys are being joined?
- Is it `INNER JOIN` or `LEFT JOIN`?
- Could rows be silently dropped?
- Could a JOIN duplicate rows?

### Window functions

- Is `PARTITION BY` correct?
- What defines the ordering?
- Does `LAG()` represent the intended historical period?

### Leakage

- Does any feature use future information?
- Does a rolling feature include the current/future target?

### Missing data

- Are missing dates handled?
- Does missing mean zero according to the business/data contract?
- Could missing data indicate a pipeline failure?

---

# 17. Must-Know SQL Concepts for Forecasting

🔴 **MUST KNOW**

```text
SELECT
WHERE
GROUP BY
Aggregations
JOIN
CTE
DATE_TRUNC
Window functions
LAG
LEAD
Rolling calculations
Missing dates
generate_series
Granularity
Data leakage
```

🟡 **GOOD TO KNOW LATER**

```text
Advanced window frames
FILTER
DATE_PART / EXTRACT
Complex CTE optimization
Query planning
Indexes for large analytical workloads
Materialized views
```

🟢 **SKIP FOR NOW**

```text
Advanced PostgreSQL internals
Query planner internals
Partitioning strategies
Advanced indexing
Database performance tuning
```

---

# 18. Key Mental Model

```text
Raw transactions
       ↓
      WHERE
       ↓
Selected historical data
       ↓
DATE_TRUNC
       ↓
GROUP BY
       ↓
Desired time-series granularity
       ↓
JOIN
       ↓
Additional information
       ↓
Window functions
       ↓
LAG / rolling features
       ↓
Forecasting dataset
```

The most important question throughout the process is:

> **"What does one row represent, and is every feature available at prediction time?"**
