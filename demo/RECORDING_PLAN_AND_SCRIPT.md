# Gridbricks UK Wind Forecast Platform — YouTube Demo Plan & Script
**Duration:** Maximum 10 minutes (Split into two distinct 5-minute parts)
**Target Audience:** Energy Traders, Day-Ahead Procurement Teams, and Technical Reviewers / Assessors
**Live Production Deployments:**
- **Frontend (Vercel):** https://gridbricks-wind-forecast-analytics.vercel.app/
- **Backend (Render):** https://gridbricks-wind-forecast-analytics.onrender.com
- **API Documentation (Swagger UI):** https://gridbricks-wind-forecast-analytics.onrender.com/docs
- **API Base URL:** `https://gridbricks-wind-forecast-analytics.onrender.com/api/v1`

---

## Recording Checklist

### Pre-Recording Setup
- [ ] Screen resolution set to **1920x1080 (100% zoom)**.
- [ ] Browser window prepared with the following pre-loaded tabs:
  1. **Production Dashboard:** `https://gridbricks-wind-forecast-analytics.vercel.app/` (Executive Dashboard)
  2. **Procurement Decision Support:** Pre-opened in a second tab or ready to click in navigation
  3. **Forecast Explorer:** Pre-opened in a third tab (paginated table view)
  4. **FastAPI OpenAPI Swagger UI:** `https://gridbricks-wind-forecast-analytics.onrender.com/docs`
  5. **VS Code / IDE:** Open to project root with `backend/` and `frontend/` visible
- [ ] Local environment running as hot standby:
  - Backend: `uvicorn app.main:app --port 8000`
  - Frontend: `npm run dev` in `frontend/` on `http://localhost:5173`
- [ ] Microphone check: clear voice capture, input gain balanced, background noise suppressed.
- [ ] Dual-timer check:
  - **Timer 1 (Customer Presentation):** Strict 5:00 limit.
  - **Timer 2 (Technical Review):** Strict 5:00 limit.

---

## Part 1: Customer Presentation (5 Minutes Max)

### Goal
Demonstrate how the application solves the UK electricity utility day-ahead power procurement problem using real Elexon BMRS data without look-ahead bias, highlighting actionable volume risks and analytical guardrails.

---

### Demonstration Sequence & Spoken Script

#### 0:00 – 1:00 | The Business Problem & GB Wholesale Market Context
- **Visual:** Executive Dashboard home screen (`https://gridbricks-wind-forecast-analytics.vercel.app/`). Highlight the Header with the live connection badge, the date filter (`2026-01-01` to `2026-01-31`), and the default Decision Cutoff (`Day-Ahead 11:00 UK Time`).
- **Screen Actions:** Smooth cursor movement across the header, pointing to the cutoff dropdown and the Elexon BMRS badge.
- **Spoken Script:**
  > *"Hello and welcome. Today I am presenting the Gridbricks UK Wind Forecast and Day-Ahead Procurement Intelligence Platform.
  >
  > As a Great Britain electricity utility, our day-ahead procurement desk must commit to wholesale power purchases on power exchanges like EPEX SPOT and Nord Pool to balance customer demand. Because wind generation in the UK is highly volatile, our single biggest financial and operational exposure is volume uncertainty.
  >
  > In the GB market, day-ahead auction order books close strictly at 11:00 AM on day D-1. A procurement team cannot rely on forecasts published after that gate closure—doing so introduces look-ahead bias and invalidates backtesting.
  >
  > Our platform solves this exact challenge. It ingests official Elexon BMRS market data, matches historical actuals with the latest eligible wind forecasts published prior to decision cutoffs, and quantifies prospective physical imbalance risks for power traders."*

---

#### 1:00 – 2:30 | The Executive Dashboard, KPIs & Point-in-Time Correctness
- **Visual:** KPI Summary Cards: Data Coverage (100%), MAE (2,122.81 MW), RMSE (2,616.69 MW), Mean Bias (+1,840.30 MW), WAPE (18.33%).
- **Screen Actions:** Hover over each metric card. Open the Decision Cutoff dropdown to show supported presets (`DA_1100`, `DA_1200`, `DA_1700`, `DA_2300`, and Rolling 24h/12h/6h/2h). Click on `DA_1200` to show instantaneous updates, then switch back to `DA_1100`.
- **Spoken Script:**
  > *"Looking at the executive dashboard for the full month of January 2026—encompassing all 744 hourly delivery intervals—every metric is computed dynamically from official Elexon FUELHH actuals and WINDFOR forecasts.
  >
  > Notice the decision cutoff selector. We default to 'Day-Ahead 11:00 UK Time'—the auction gate closure. The platform guarantees strict point-in-time correctness: any forecast published after 11:00 AM on D-1 is excluded.
  >
  > Examining our headline KPIs:
  > - Our **Mean Absolute Error (MAE)** is **2,122.8 MW**, with a **Weighted Absolute Percentage Error (WAPE)** of **18.33%**.
  > - Most crucially, our **Mean Bias is +1,840.3 MW**.
  >
  > This reveals a persistent, systematic overforecasting tendency across January 2026. On average, the national wind forecast anticipated 1.84 Gigawatts more wind generation than actually materialized on the GB grid."*

---

#### 2:30 – 3:45 | Time-Series Analytics, Interactive Zoom & Error Distribution
- **Visual:** Actual vs Forecast Generation chart, interactive Brush slider, and Signed Error Bar Chart.
- **Screen Actions:**
  1. Click the 'Actual' and 'Forecast' visibility toggles to isolate lines.
  2. Drag the handles on the bottom Brush slider to zoom into the storm event between January 8th and 14th.
  3. Hover over the signed error bars to reveal tooltip details (amber = overforecast / short position, cyan = underforecast / long position).
  4. Scroll down to show the 3 secondary charts: Daily Forecasting Accuracy, Error Histogram Distribution, and Diurnal Hour-of-Day Profile.
- **Spoken Script:**
  > *"Below the summary cards is our time-series view. The emerald line represents actual national wind generation from Elexon FUELHH, while the cyan line is the selected point-in-time WINDFOR forecast.
  >
  > Using the interactive slider, a trader can zoom into specific operational events—such as this high-generation storm week around January 10th where generation ramped past 18 Gigawatts.
  >
  > Directly underneath is the Signed Forecast Error chart around zero baseline.
  > - **Amber bars** above zero represent **overforecasting** (a generation shortfall).
  > - **Cyan bars** below zero represent **underforecasting** (excess wind).
  >
  > Notice the asymmetry: overforecasting occurred in **84.4% of intervals** (628 out of 744 hours), peaking at over 6,800 MW of overprediction.
  > In our diurnal breakdown, we can also see intraday bias patterns, showing whether morning and evening ramp periods carry distinct forecasting risks."*

---

#### 3:45 – 5:00 | Procurement Decision Support, Imbalance Risks & Guardrails
- **Visual:** Click navigation tab to switch to **'Procurement Decision Support'**.
- **Screen Actions:**
  1. Walk through the Short Physical Position Risk vs Long Physical Position Risk breakdown.
  2. Highlight the 1,474,276 MWh short volume exposure.
  3. Point out the Procurement Guidance Notes and Regulatory Guardrail banner.
  4. Open the **Methodology Modal** from the top header button to show transparency.
- **Spoken Script:**
  > *"Now let's examine the Procurement Decision Support tab. This screen bridges the gap between raw data science and commercial utility trading.
  >
  > When a utility commits day-ahead purchases assuming 13.4 GW of wind, but only 11.5 GW delivers, the utility is left **physically short**. In January 2026, this overforecasting generated **1,474,276 MWh** of prospective short volume exposure.
  >
  > If a desk fails to adjust for this bias, that deficit drops into the Balancing Mechanism, cashed out at National Grid ESO's volatile System Buy Price (SBP) or covered at intraday premiums.
  >
  > Conversely, in the 15.6% of intervals where underforecasting occurred, utilities face long positions where surplus wind spills at discounted System Sell Prices (SSP).
  >
  > Crucially, our platform enforces an explicit **Procurement Guardrail**: wind generation alone does not equal net procurement. A utility's total position must account for consumer demand profiles, solar, baseload thermal contracts, and interconnectors. Our platform delivers transparent, mathematically uncorrupted wind volume intelligence without fabricating synthetic demand or prices."*

---

## Part 2: Technical Review (5 Minutes Max)

### Goal
Walk through the technical architecture, official Elexon data pipeline, point-in-time selection algorithm, backend performance optimization, automated test suite, and production deployment on Render and Vercel.

---

### Demonstration Sequence & Spoken Script

#### 5:00 – 6:00 | System Architecture & Technology Stack
- **Visual:** VS Code editor showing the project structure (`backend/` and `frontend/`) and the live OpenAPI Swagger UI at `https://gridbricks-wind-forecast-analytics.onrender.com/docs`.
- **Screen Actions:** Expand `backend/app/` folders (`api`, `core`, `repositories`, `schemas`, `services`) in the sidebar; scroll through Swagger UI endpoints.
- **Spoken Script:**
  > *"Moving to the technical review: the platform is built with a production-grade full-stack architecture designed for high-performance time-series analytics.
  >
  > - **Backend:** Python 3.11 with FastAPI, Pydantic v2 data models, and vectorized Pandas/NumPy.
  > - **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, and Recharts.
  > - **Deployments:** The backend runs in a containerized environment on Render, and the frontend is continuously deployed on Vercel.
  >
  > The API is fully typed and adheres to OpenAPI standards. It provides REST endpoints for summary metrics, time series, daily breakdowns, diurnal profiles, error histograms, paginated table views, and CSV exports."*

---

#### 6:00 – 7:00 | Elexon Data Ingestion & Half-Hour to Hourly Alignment
- **Visual:** Open `backend/app/services/ingestion.py` and `backend/app/services/elexon_client.py`.
- **Screen Actions:** Highlight `fetch_fuelhh_wind_stream()`, `fetch_windfor_stream()`, and the hourly aggregation logic in `IngestionService`.
- **Spoken Script:**
  > *"Let's look at the data ingestion pipeline. We connect to official Elexon BMRS stream endpoints:
  > - `FUELHH/stream` for half-hourly generation by fuel type, filtered strictly for `fuelType == 'WIND'`.
  > - `WINDFOR/stream` for rolling national wind generation forecasts.
  >
  > A key challenge in UK power analytics is resolution mismatch: FUELHH reports actuals at **30-minute settlement periods**, whereas WINDFOR native forecasts are published on **1-hour delivery intervals**.
  >
  > To compare like-for-like power in Megawatts without fabricating data, our ingestion pipeline groups settlement periods by hour and calculates the arithmetic mean of the two half-hours.
  > All timestamps are strictly parsed into timezone-aware UTC (`datetime64[ns, UTC]`), completely avoiding naive timezone ambiguities."*

---

#### 7:00 – 8:15 | Point-in-Time Algorithm & High-Performance Optimization
- **Visual:** Open `backend/app/repositories/data_store.py` (`_rebuild_indexes`), `backend/app/services/ingestion.py` (`match_intervals`), and terminal showing benchmark results.
- **Screen Actions:** Highlight the pre-sorted dictionary index and `np.searchsorted()` binary search.
- **Spoken Script:**
  > *"Now let's examine the core algorithm and our backend performance optimization.
  >
  > In naive implementations, matching 744 delivery intervals against 20,221 forecast records causes a severe bottleneck: repeatedly scanning and sorting the entire DataFrame for every hour executes over 2.1 million function calls and takes ~10 seconds per request.
  >
  > We solved this through an efficient algorithm:
  > 1. In `DataStore`, forecasts are pre-sorted once by `[startTime, publishTime, generation]` ascending and grouped into NumPy arrays per delivery interval.
  > 2. In `match_intervals`, for each delivery hour, we calculate the cutoff timestamp using market presets—such as D-1 11:00 UTC.
  > 3. We use `numpy.searchsorted(pub_times, cutoff, side='right') - 1`. This $O(\log K)$ binary search identifies the latest eligible publication in microseconds.
  > 4. Because ties were pre-sorted by generation ascending, equal publication timestamps automatically select the highest generation record.
  > 5. An in-memory query cache ensures concurrent dashboard requests resolve in less than 1 millisecond.
  >
  > This reduced end-to-end matching time from **10.2 seconds down to 22 milliseconds**—a **500× speedup** while guaranteeing 100% bit-for-bit mathematical equivalence."*

---

#### 8:15 – 9:00 | Health-Check Decoupling & Dashboard Resilience
- **Visual:** Open `backend/app/services/elexon_client.py` (`ping_health`), `backend/app/api/routes.py` (`/health/live`), and `frontend/src/App.tsx` (`loadAnalytics`).
- **Screen Actions:** Highlight the 60-second TTL upstream cache, the dedicated `/health/live` route, and `Promise.allSettled()` in the frontend.
- **Spoken Script:**
  > *"We also diagnosed and resolved the upstream health check latency.
  >
  > Previously, `/api/v1/health` synchronously queried the live Elexon API on every request. On Render cold starts, upstream timeouts caused 58-second delays and spurious health warnings.
  >
  > We decoupled application liveness from external dependencies:
  > - Added `/api/v1/health/live` for instantaneous container liveness checks in under 6 milliseconds.
  > - Bounded external Elexon pings to strict 2.0s connect timeouts and cached results for 60 seconds. If Elexon is unreachable, liveness never fails, and the dashboard seamlessly serves cached data.
  > - On the frontend, `App.tsx` uses `Promise.allSettled()`. If any single secondary endpoint experiences network latency, all other dashboard charts remain fully interactive rather than failing blank."*

---

#### 9:00 – 10:00 | Automated Tests, Docker & Verification
- **Visual:** Terminal executing `pytest backend/tests -v` and `npm test` in `frontend/`. Show Docker Compose files.
- **Screen Actions:** Run the test commands live in terminal; show 37 backend tests passing in ~3.5s and 4 frontend tests passing in ~8s.
- **Spoken Script:**
  > *"Quality assurance is enforced across both backend and frontend:
  > - In `backend/tests/`, our test suite contains **37 automated pytest tests**, covering point-in-time correctness, tie-breaking rules, missing interval classifications, date boundaries, API regression, and graceful degradation during external outages. All 37 tests pass in 3.5 seconds.
  > - In `frontend/src/test/`, our Vitest suite validates filter controls, summary cards, and decision support calculations. The TypeScript build compiles cleanly with zero errors.
  > - For deployment, the system is fully containerized via multi-stage Dockerfiles and `docker-compose.yml`, allowing a complete local spin-up with a single command: `docker compose up --build`.
  >
  > In conclusion, the Gridbricks platform delivers a robust, high-performance, and mathematically disciplined system that turns volatile wind generation into actionable commercial procurement intelligence.
  >
  > Thank you for your time."*

---

## Technical Appendix & Benchmark Reference Card

Keep this quick reference open during recording for spontaneous questions or quick verification:

```text
======================================================================
GRIDBRICKS WIND FORECAST ANALYTICS — PERFORMANCE BENCHMARK SUMMARY
======================================================================
Dataset: 1,497 actual FUELHH records, 20,221 WINDFOR records
Period:  Jan 1–31, 2026 (744 hourly delivery intervals)
Preset:  DA_1100 (Day-Ahead 11:00 UK Time Auction Gate Closure)

Key Analytics Metrics:
- Total Intervals:              744 (100% data coverage)
- Mean Absolute Error (MAE):    2,122.81 MW
- Root Mean Square Error (RMSE):2,616.69 MW
- Mean Bias:                    +1,840.30 MW (systematic overforecast)
- WAPE:                         18.33%
- Mean Actual Wind Generation:  11,580.74 MW
- Mean Selected Forecast:       13,421.03 MW
- Overforecasting Frequency:    84.41% (628 intervals)
- Underforecasting Frequency:   15.59% (116 intervals)
- Prospective Short Volume:     1,474,276.0 MWh
- Prospective Long Volume:      105,095.5 MWh
- Net Physical Imbalance:       +1,369,180.5 MWh

Latency Benchmarks:
- Liveness Check (/health/live):    6.26 ms (was 58,200 ms)
- Health Check (/health):           8.13 ms (was 1,050 ms)
- Summary (/summary):               9.46 ms (was ~10,200 ms)
- Timeseries (/timeseries):        22.83 ms (was ~10,000 ms)
- Daily Summary (/daily):          44.45 ms (was ~9,800 ms)
- Forecast Table (/forecast-table): 9.76 ms (was ~10,000 ms)
- Peak Memory Traced:              490.3 KB
======================================================================
```
