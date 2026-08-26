# AutoETS — What It Is, How It Works, and What Not to Confuse

## 1. The big idea

`AutoETS` is a tool in the **StatsForecast** library that automatically selects and fits an appropriate model from the **ETS family of exponential-smoothing models**.

A useful mental model is:

```text
Historical time-series data
        ↓
     AutoETS
        ↓
Looks for numerical structure such as
level, trend, and seasonality
        ↓
Fits and compares suitable ETS models
        ↓
Selects an appropriate ETS specification
        ↓
Produces forecasts
```

Important: AutoETS models **patterns in the numbers**. It does not inherently understand the real-world causes of those patterns.

---

## 2. What does ETS mean?

ETS stands for:

- **E — Error**: how random deviations around the model are represented.
- **T — Trend**: whether the underlying level is moving upward or downward over time.
- **S — Seasonality**: whether a pattern tends to repeat after a fixed number of observations.

ETS is therefore not just one single equation. It is a **family of related forecasting models**.

`AutoETS` automates the job of choosing and fitting a suitable member of that family.

---

## 3. What is “level”?

The **level** is the model's estimate of where the time series is currently centered.

Suppose monthly sales are:

```text
98, 102, 99, 101, 100, 103
```

The observations move around, but we might say sales are currently around **100–101**.

That underlying current value is the idea of the level.

```text
Actual observations = noisy values we observe
Level               = estimated underlying current value
```

The level is not necessarily equal to the latest observation.

---

## 4. How is the level updated?

In simple exponential smoothing, a simplified level update is:

$$
\ell_t = \alpha y_t + (1-\alpha)\ell_{t-1}
$$

where:

- `y_t` = newest actual observation
- `ℓ_(t-1)` = previous estimated level
- `α` = smoothing parameter between 0 and 1
- `ℓ_t` = new estimated level

Example:

```text
Previous level = 100
New observation = 110
α = 0.20
```

Then:

```text
new level = 0.20 × 110 + 0.80 × 100
          = 102
```

So the model does not immediately change its level from 100 to 110. It updates its estimate to 102.

### Meaning of alpha

A **small `α`** makes the level change slowly. Older information retains more influence.

A **large `α`** makes the level react more strongly to recent observations.

```text
Small α → smoother / slower reaction
Large α → faster reaction to new data
```

AutoETS estimates smoothing parameters rather than requiring you to guess them manually in normal use.

---

## 5. What is trend?

Consider:

```text
Jan  100
Feb  110
Mar  120
Apr  130
May  140
```

There is more than a current level. The series is also moving upward.

Conceptually:

```text
Level ≈ where the series is now
Trend ≈ how the underlying series is moving
```

For a simple illustration:

```text
Current level ≈ 140
Trend ≈ +10 per month
```

A trend-aware model may therefore forecast values above the current level.

ETS has different ways of representing trend, including models without trend and models with damped trend. AutoETS can consider appropriate alternatives.

---

## 6. What is seasonality?

Seasonality means a pattern tends to repeat after a fixed number of observations.

For monthly data with a yearly cycle:

```text
Jan Feb Mar ... Dec | Jan Feb Mar ... Dec
<---- 12 values ---> <---- 12 values --->
```

If certain positions in each 12-month cycle tend to be systematically high or low, an ETS model may represent that as seasonality.

This is where `season_length` matters.

```python
AutoETS(season_length=12)
```

means that **12 observations make up one seasonal cycle** for candidate seasonal models.

It does **not** mean:

- forecast 12 periods;
- there are 12 seasons;
- the data are automatically monthly.

---

## 7. `freq` vs `season_length` vs `h`

These three are easy to confuse.

### `freq="MS"`

Answers:

> How often do observations occur?

```python
freq="MS"
```

means observations are at **month starts** — monthly data.

### `season_length=12`

Answers:

> How many observations are in one seasonal cycle?

With monthly observations and yearly seasonality:

```text
12 observations × 1 month each = 12 months = 1 year
```

so:

```python
season_length=12
```

### `h=6`

Answers:

> How many future observations should be forecast?

For monthly data:

```python
h=6
```

means forecast the next **6 months**.

Together:

```python
sf = StatsForecast(
    models=[AutoETS(season_length=12)],
    freq="MS"
)

forecast = sf.forecast(df=data, h=6)
```

Read this as:

> “My observations are monthly. Allow ETS models with a 12-observation seasonal cycle, and forecast the next 6 observations.”

---

## 8. What does AutoETS actually see?

Suppose sales look like this for several years:

```text
Position:  1   2   3   4   5   6   7   8   9  10  11  12
Year 1:   100 105 110 120 130 160 200 190 150 130 120 180
Year 2:   102 108 112 123 135 165 205 195 155 133 125 185
```

A human might say:

> “Position 7 is July and sales are high because summer tourism increases demand.”

AutoETS does not inherently know that explanation.

It can detect something like:

```text
Position 7 tends to be high.
Position 8 tends to be high.
Position 1 tends to be low.
The pattern appears to repeat every 12 observations.
```

Therefore:

> **AutoETS detects/models numerical patterns; it does not understand their real-world causes.**

---

## 9. Why does the distinction between pattern and cause matter?

Imagine July sales have been high for four years because a large annual festival occurs every July.

```text
2022 July → high
2023 July → high
2024 July → high
2025 July → high
```

The historical data tell AutoETS that this position in the seasonal cycle tends to be high.

Now suppose the festival is permanently cancelled before July 2026.

A human with that information knows an important cause has changed.

AutoETS, if given only historical sales, does not automatically know that the festival was cancelled. It may continue forecasting a strong July because that is the numerical pattern in the history.

This is one of the most important limitations to remember.

---

## 10. What happens behind the scenes?

A simplified view is:

```text
1. Receive historical time-series data
                ↓
2. Consider suitable ETS model structures
                ↓
3. Estimate model parameters
   (including smoothing parameters)
                ↓
4. Estimate/update internal states
   such as level, trend, seasonality
                ↓
5. Compare suitable candidate models
   using statistical model-selection criteria
                ↓
6. Select an appropriate ETS specification
                ↓
7. Extend its estimated structure forward
                ↓
8. Produce forecasts
```

So `AutoETS` is doing more than simply calculating an average.

---

## 11. Is AutoETS a model?

In the StatsForecast API, `AutoETS` is provided as a forecasting model class.

Conceptually, however, it is helpful to be more precise:

- **ETS** = a family of exponential-smoothing models.
- **AutoETS** = an automatic procedure that selects and fits an appropriate ETS specification from that family.

So saying “AutoETS is a model” is acceptable in normal library usage, but saying “AutoETS automatically selects and fits an ETS model” gives a better understanding of what is happening.

---

## 12. What is StatsForecast then?

Do not confuse `StatsForecast` with `AutoETS`.

```text
StatsForecast
    ↓
manages/runs forecasting models

AutoETS
    ↓
automatically selects and fits an ETS model

ETS model
    ↓
mathematical model of patterns such as
level, trend and seasonality
```

Example:

```python
from statsforecast import StatsForecast
from statsforecast.models import AutoETS

sf = StatsForecast(
    models=[AutoETS(season_length=12)],
    freq="MS"
)
```

Here:

- `StatsForecast(...)` manages the forecasting workflow.
- `AutoETS(...)` tells it which forecasting approach to use.
- `season_length=12` describes the seasonal-cycle length.
- `freq="MS"` describes the observation frequency.

---

## 13. When is AutoETS worth considering?

AutoETS is a natural candidate when:

- you have a time series with historical observations;
- level, trend and/or repeating seasonality contain useful predictive information;
- it is reasonable to expect those historical patterns to continue sufficiently into the forecast horizon;
- you mainly need accurate forecasts rather than a causal explanation;
- external predictors are unavailable, unnecessary, or not expected to add enough value.

Examples might include stable operational series with recurring seasonal behavior.

---

## 14. When should you be cautious about AutoETS?

Be cautious when future values depend heavily on information that is not contained in the historical target series.

Examples:

```text
Sales depend heavily on a future price change.
Demand depends heavily on future temperature.
A new law will change customer behavior.
A competitor has just entered the market.
A major festival responsible for seasonality was cancelled.
A business permanently changed its operating model.
```

In such cases, historical level/trend/seasonality may not be enough. A forecasting approach using relevant predictor variables or judgment may be more appropriate.

---

## 15. What AutoETS does NOT mean

### Wrong: “AutoETS understands why sales increased.”

Better:

> AutoETS models numerical patterns associated with the increase.

### Wrong: “`season_length=12` means my data are monthly.”

Better:

> `freq="MS"` tells StatsForecast the observations are monthly; `season_length=12` says one seasonal cycle contains 12 observations.

### Wrong: “`season_length=12` means forecast 12 months.”

Better:

> `h` controls how many future observations are forecast.

### Wrong: “AutoETS knows July is summer.”

Better:

> It can model a recurring effect at a position in a 12-observation cycle without understanding the real-world reason.

### Wrong: “AutoETS is always good when data are seasonal.”

Better:

> It is a candidate model. Forecasting models should be evaluated on appropriate holdout/test data and against reasonable alternatives.

### Wrong: “AutoETS predicts the future because the past always repeats.”

Better:

> It relies on the assumption that useful aspects of the historical structure will continue sufficiently into the future.

---

## 16. The mental model to remember

```text
                    REAL WORLD
                       │
       temperature, holidays, prices,
       promotions, competitors, etc.
                       │
                       ▼
                 Actual sales
                       │
                       ▼
              Historical numbers
                       │
                       ▼
                    AutoETS
                       │
           models numerical structure
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
      Level          Trend        Seasonality
        └──────────────┼──────────────┘
                       ▼
                 ETS forecast
```

If AutoETS receives only the historical sales series, it sees the **resulting numerical history**, not all of the real-world causal variables above it.

---

## 17. One-sentence definition

> **AutoETS automatically selects and fits an exponential-smoothing model that forecasts a time series by modeling numerical structures such as its current level, trend and repeating seasonal behavior, without inherently knowing the real-world causes behind those patterns.**

---

## 18. Quick decision question

Before using AutoETS, ask:

> **“Is there useful information about the future in the historical level, trend and seasonal behavior of this series, and are those patterns reasonably likely to continue?”**

If yes, AutoETS is worth testing.

If important future changes are driven by external information that the historical series cannot reveal, consider models with predictors, judgmental adjustments, or other forecasting approaches as well.
