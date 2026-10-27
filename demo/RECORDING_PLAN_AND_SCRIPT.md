# Gridbricks UK Wind Forecast Platform — YouTube Demo Plan & Script
**Duration:** Maximum 10 minutes (Split into two 5-minute parts)  
**Target Audience:** Energy Traders, Day-Ahead Procurement Teams, and Technical Reviewers / Assessors

---

## Recording Checklist

### Pre-Recording Setup
- [ ] Backend running (`uvicorn app.main:app --port 8000`).
- [ ] Frontend running (`npm run dev` in `frontend/` on `http://localhost:5173`).
- [ ] Browser set to 1920x1080 (100% zoom).
- [ ] Clean browser window with tabs:
  1. Main Dashboard (`http://localhost:5173`)
  2. Procurement Decision Support tab
  3. Forecast Explorer tab
  4. Methodology Modal open
  5. FastAPI OpenAPI Swagger UI (`http://localhost:8000/docs`)
- [ ] Microphone tested, clear audio with noise suppression.
- [ ] Timer running to strictly adhere to the 5-minute + 5-minute constraint.

---

## Part 1: Customer Presentation (5 Minutes Max)

### Goal
Demonstrate how the application solves the UK electricity utility day-ahead power procurement problem using real Elexon data without lookahead bias.

### Demonstration Sequence & Script

#### 0:00 – 1:00 | The Business Problem & Market Context
- **Visual:** Executive Dashboard with Header, Date Range (Jan 1–31, 2026), and Default Cutoff (Day-Ahead 11:00 UK Time).
- **Spoken Script:**
  > *"Welcome. Today I'm presenting the Gridbricks UK Wind Forecast and Day-Ahead Procurement Intelligence Platform. As a UK electricity utility, our day-ahead procurement team must purchase enough power on the wholesale exchange to meet consumer demand. Because wind is weather-dependent and volatile, our biggest day-ahead risk is volume uncertainty.
  > In the GB market, day-ahead power auctions at EPEX SPOT and Nord Pool close order books at 11:00 AM on day D-1. A procurement team needs to know: what was the latest wind forecast available before that 11:00 AM cutoff? How did that forecast actually perform? And what are the prospective volume risks if wind under-delivers or over-delivers?"*

#### 1:00 – 2:30 | The Executive Dashboard & Point-in-Time Cutoff
- **Visual:** Hover over KPI Summary Cards (MAE: 2,122.81 MW, RMSE: 2,616.69 MW, Bias: +1,840.3 MW, WAPE: 18.25%, Coverage: 100%).
- **Spoken Script:**
  > *"Here on the executive dashboard, we see the complete performance across all 744 hours of January 2026. Every metric is computed dynamically from official Elexon FUELHH actuals and WINDFOR forecasts.
  > Notice the decision cutoff selector at the top. We default to 'Day-Ahead 11:00 UK Time'—the official GB auction gate closure. The platform guarantees strict point-in-time correctness: any forecast published after 11:00 AM on D-1 is strictly excluded, ensuring zero lookahead bias.
  > Looking at the KPIs: Our Mean Absolute Error across January is 2,122 MW, with a Weighted Absolute Percentage Error of 18.3%. Importantly, the Mean Bias is +1,840 MW. This reveals a systematic overforecasting tendency across January 2026—the forecasting models predicted 1,840 MW more wind power than actually materialized on average."*

#### 2:30 – 3:45 | Time-Series Analytics & Error Distribution
- **Visual:** Zooming in with the interactive Brush slider on the Actual vs Forecast chart; hovering over the signed error bars (amber = overforecast, cyan = underforecast).
- **Spoken Script:**
  > *"Below the KPIs, we have the Actual versus Selected Forecast time series. The green line is actual national wind generation from Elexon FUELHH; the dashed blue line is the selected point-in-time forecast. Using the interactive slider at the bottom, a trader can zoom into individual storm events or calm high-pressure periods.
  > Directly beneath is the signed error chart around a zero baseline. Amber bars indicate overforecasting; cyan bars indicate underforecasting. Notice how overforecasting occurred in nearly 70% of intervals throughout the month. In our error distribution histogram, we see the spread centered in the positive error band with occasional severe misses exceeding 4 GW during rapid front movements."*

#### 3:45 – 5:00 | Procurement Decision Support & Operational Implications
- **Visual:** Switch to 'Procurement Decision Support' tab. Highlight the Short Position Risk vs Long Position Risk breakdown and the Regulatory Guardrail.
- **Spoken Script:**
  > *"Now let's switch to the Procurement Decision Support view. When a forecast overpredicts wind by 1,840 MW, a utility that relied on that forecast will face a physical short position. In January 2026, this generated over 1.3 million MWh of prospective deficit that had to be covered through intraday markets or National Grid ESO's Balancing Mechanism at volatile System Buy Prices.
  > Conversely, underforecasting creates long positions where surplus wind is spilled or sold at discounted System Sell Prices.
  > Crucially, our platform provides a clear analytical guardrail: wind generation alone does not determine total power procurement. Net procurement must also incorporate customer demand profiles, solar, baseload contracts, and storage. Our tool empowers the procurement team to quantify wind volume uncertainty without fabricating unverified market prices or demand schedules."*

---

## Part 2: Technical Review (5 Minutes Max)

### Goal
Walk through the software architecture, Elexon BMRS data pipeline, point-in-time selection algorithm, automated testing, and Docker deployment.

### Demonstration Sequence & Script

#### 5:00 – 6:00 | Architecture & Technology Stack
- **Visual:** Code editor showing directory tree (`backend/` and `frontend/`), plus OpenAPI Swagger docs (`/docs`).
- **Spoken Script:**
  > *"Turning to the technical implementation: the platform is built with a production full-stack architecture.
  > The backend is written in Python 3.11 with FastAPI, Pydantic v2 schemas, and Pandas for analytical processing.
  > The frontend is built in React 18, TypeScript, and Vite with Tailwind CSS and Recharts.
  > The API is fully typed and OpenAPI-documented, providing REST endpoints for summary metrics, time series, daily rollups, diurnal profiles, error histograms, and CSV exports."*

#### 6:00 – 7:15 | Elexon Data Ingestion & Interval Alignment
- **Visual:** Open `backend/app/services/ingestion.py` and `backend/app/services/forecast_selection.py`.
- **Spoken Script:**
  > *"Let's look at the data ingestion layer. We integrate directly with Elexon BMRS's stream endpoints: FUELHH for half-hourly generation by fuel type, and WINDFOR for rolling wind forecasts.
  > One key technical challenge we identified during Phase 1: FUELHH provides actual generation at 30-minute settlement period resolution, while WINDFOR provides forecasts at 1-hour resolution.
  > To match like-for-like power in Megawatts, our ingestion service aligns observations to hourly delivery intervals by calculating the arithmetic mean of the two half-hourly settlement periods in each hour. All timestamps are strictly normalized to timezone-aware UTC.
  > To eliminate latency and avoid spamming Elexon, data is persisted in a local disk cache (`backend/data/cache`), allowing sub-50ms API responses while supporting on-demand re-syncs."*

#### 7:15 – 8:30 | Point-in-Time Selection Algorithm (`select_forecast_as_of`)
- **Visual:** Highlight `select_forecast_as_of` in `forecast_selection.py` and its corresponding unit tests in `tests/test_forecast_selection.py`.
- **Spoken Script:**
  > *"Here is the core analytical algorithm: `select_forecast_as_of`.
  > For every hourly delivery interval $T$, we first compute the applicable decision cutoff—for example, D-1 at 11:00 UTC for the day-ahead auction.
  > Next, we filter the forecast dataset for records matching the delivery interval and exclude all forecasts where `publishTime > cutoff`.
  > Finally, we select the latest eligible forecast via `max(publishTime)`. If two runs share the same publication timestamp, ties are broken deterministically.
  > In `backend/app/services/analysis.py`, we implement MAE, RMSE, Mean Bias, and Weighted Absolute Percentage Error (WAPE), with rigorous zero-denominator handling so zero-generation intervals never trigger divide-by-zero crashes."*

#### 8:30 – 9:30 | Test Suite & Validation
- **Visual:** Terminal showing `pytest --cov=app backend/tests` and `npm test` in `frontend/`.
- **Spoken Script:**
  > *"Quality assurance is enforced across both backend and frontend.
  > Running `pytest` across our backend suite executes 27 automated tests covering point-in-time filtering, cutoff calculations, duplicate handling, WAPE edge cases, and all API endpoints with zero network dependencies. Test coverage is 76% overall and over 90% across analytical services.
  > On the frontend, our Vitest suite validates component rendering, KPI cards, filter controls, and procurement volume calculations. The TypeScript build is strictly checked with zero compilation errors."*

#### 9:30 – 10:00 | Docker & Deployment Architecture
- **Visual:** Open `docker-compose.yml` and `Dockerfile`.
- **Spoken Script:**
  > *"For deployment and local execution, we provide multi-stage Dockerfiles and a Docker Compose file. The backend runs on Uvicorn in a Python 3.11-slim container with built-in healthchecks, and the frontend is compiled and served through high-performance Alpine Nginx with automatic reverse-proxying for `/api/`.
  > The application starts with a single command: `docker compose up --build`.
  > In summary, we have delivered a complete, fully tested, mathematically sound platform that translates complex GB market data into actionable procurement intelligence. Thank you."*
