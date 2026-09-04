# Digital Twin AI - Personal Life Simulation & Decision Assistant

An AI-powered personal analytics and decision-assistance application that builds
a **living digital representation** of your finances, study habits, routines,
fitness and goals - then uses forecasting, simulation and a conversational AI
assistant to help you make better decisions *before* you make them in real life.

Built with **Streamlit + PostgreSQL + Plotly**, with **Gemini** as the primary
conversational AI and a fully-offline built-in rule-based assistant as automatic
fallback.

---

## 1. Project Overview

Digital Twin AI collects and stores your personal behavioural and financial
data, runs predictive analytics and forecasting, lets you simulate "what-if"
decisions across multiple future scenarios, scores and compares those scenarios,
generates personalised recommendations, and finally lets you **ask questions in
natural language** through a Conversational AI assistant that is grounded
entirely in *your own* data.

The application is organised as four milestones:

| Milestone | Focus |
|-----------|-------|
| **1** | Data collection, user profiling, PostgreSQL storage |
| **2** | AI Core Layer - forecasting & predictive analytics (finance, study, habits, fitness, health) |
| **3** | Digital Twin Simulation Engine - scenario generation, scoring, comparison, recommendation engine |
| **4** | Conversational AI assistant + interactive Plotly dashboard (this milestone) |

---

## 2. Architecture

```
Streamlit UI (app.py + pages_app/*)
      |
      +-- Milestone 1  --  PostgreSQL (database.py, psycopg2 pool)
      +-- Milestone 2  --  ai_models/*  (finance / study / fitness / health / habits)
      +-- Milestone 3  --  simulation/* (engine, scenarios, comparator, recommendation)
      +-- Milestone 4  --  ai/* (conversational AI) + pages_app/dashboard.py, ai_chat.py
                              |
                              +-- conversation_service.py
                              +-- context_builder.py  --> db / simulation / ai_models
                              +-- llm_client.py       (gemini | rule_based)
                              +-- response_formatter.py
```

**AI Provider Architecture:**

```
                    AI ASSISTANT
                         |
              +----------+----------+
              |                     |
       Gemini API available     Gemini unavailable
              |                     |
              v                     v
          GEMINI AI            RULE-BASED AI
              |                     |
              +----------+----------+
                         |
                         v
                Response to User
```

**Key principle:** the deterministic engines (database analytics, forecasting,
simulation, recommendation) are the **source of truth**. The LLM only explains
and personalises the already-computed results - it never re-does calculations or
invents data.

---

## 3. Features

- **User profiling & data collection** (finance, study, habits, schedule, goals, health, fitness).
- **Financial forecasting** - savings projections, spending analysis, budget recommendations.
- **Study & productivity analytics** - weekly patterns, performance prediction, weak-subject detection, planners.
- **Habit & fitness analytics** - completion rates, fitness score, workout recommendations, activity trends, health risk.
- **Goals tracking** with progress visualisation.
- **What-if simulation engine** across financial, study and habit/fitness domains.
- **Scenario comparison & scoring** with transparent score breakdowns.
- **Personalised recommendation engine** (category, priority, reason, benefits, risks, next actions).
- **Conversational AI assistant** - answers grounded in your real Digital Twin data; works with Gemini (primary) or a fully-offline rule-based assistant (automatic fallback).
- **Interactive Plotly dashboard** - KPI cards + tabs across every domain.
- **JWT-based authentication** with PBKDF2-SHA256 password hashing.

---

## 4. Installation

Requires **Python 3.9+** and a **PostgreSQL** server (local or remote).

```bash
# 1. Clone / enter the project
cd digital-twin-ai

# 2. (Recommended) create a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) install the Gemini SDK if you want to use the Gemini AI provider:
# pip install google-genai
```

---

## 5. Environment Variables

Create a `.env` file (or export the variables in your shell). Copy from the
provided template:

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | PostgreSQL connection |
| `JWT_SECRET` | Secret used to sign login tokens (long/random in production) |
| `JWT_EXPIRES_HOURS` | Login token lifetime (default 24) |
| `LLM_PROVIDER` | `gemini` (primary) or `rule_based` (default `gemini`) |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Used when `LLM_PROVIDER=gemini` |
| `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`, `LLM_TIMEOUT_SECONDS`, `LLM_RATE_LIMIT_RETRIES` | LLM tuning |

> **Security:** You may also place DB and LLM values in `.streamlit/secrets.toml`
> (see `.streamlit/secrets.toml.example`), which take precedence over the
> environment. **Never commit real secrets.** `.gitignore` excludes `.env` and
> `.streamlit/secrets.toml`.

---

## 6. Database Setup

1. Ensure PostgreSQL is running.
2. Create the database:

```sql
CREATE DATABASE digital_twin;
```

3. The application **creates all tables automatically** on first start
   (`database.init_db()` in `app.py`). No manual schema work is required.
4. (Optional) SQL migrations for milestones are provided under `sql/`.

Default connection values are `localhost:5432`, database `digital_twin`,
user `postgres`. Override via `.streamlit/secrets.toml` or environment
variables as described above.

---

## 7. Run Locally

```bash
# From the project root
python run.py
```

This launches Streamlit (`streamlit run app.py`). Alternatively:

```bash
streamlit run app.py
```

Then open the printed URL (usually `http://localhost:8501`). Register a new
account to create your digital twin, then start logging data.

---

## 8. Run Streamlit

```bash
streamlit run app.py --server.port 8501
```

Streamlit reads `.streamlit/config.toml` for theming and behaviour. To reach the
app from other machines, you can set `[server] headless = true` and
`address = "0.0.0.0"` in that file.

---

## 9. Configure AI Provider

The Conversational AI assistant supports two provider modes:

### Gemini (PRIMARY) - `gemini`
Uses Google's Gemini API for intelligent, conversational responses grounded in
your Digital Twin data.

```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-3.7-flash
```

Ensure `pip install google-genai` is done.

**Automatic Fallback:** When Gemini is unavailable (missing key, API error,
timeout, network failure, rate limit, quota exceeded), the application
**automatically** falls back to the built-in rule-based assistant without
crashing. You will see a notice in the chat that the fallback was used.

### Built-in assistant (no key) - `rule_based`
Works out of the box with no LLM API key. It is a deterministic assistant that
answers Digital Twin questions directly from your data. Great for demos, offline
use, and testing.

```bash
LLM_PROVIDER=rule_based
```

### Fallback Behavior

| Scenario | Behavior |
|----------|----------|
| `LLM_PROVIDER=gemini` + valid key | Gemini responds |
| `LLM_PROVIDER=gemini` + missing key | Automatic rule-based fallback |
| `LLM_PROVIDER=gemini` + API error | Automatic rule-based fallback |
| `LLM_PROVIDER=gemini` + timeout | Automatic rule-based fallback |
| `LLM_PROVIDER=gemini` + rate limit | Automatic rule-based fallback |
| `LLM_PROVIDER=gemini` + no network | Automatic rule-based fallback |
| `LLM_PROVIDER=rule_based` | Rule-based responds directly |

The application **never crashes** because Gemini is unavailable.

---

## 10. Testing

```bash
# Run the full test suite (Milestones 1-4)
python -m pytest -q
```

Test coverage includes:

- **Milestone 1-3:** finance, study, fitness, health models, simulation engine,
  comparator, recommendation engine.
- **Milestone 4 (`tests/test_ai.py`):** LLM configuration (Gemini + rule_based),
  missing-key handling, context generation, conversation service, empty-user-data
  handling, LLM failure handling, Gemini automatic fallback, response
  formatting/validation, dashboard imports, simulation integration, and a
  simulation performance check (< 5s).

> The Milestone 4 tests monkeypatch the database and use the keyless rule-based
> client, so they run **without a live PostgreSQL or an LLM API key**.

---

## 11. Deployment

### Local / VM
```bash
pip install -r requirements.txt
JWT_SECRET=<long-random> LLM_PROVIDER=rule_based streamlit run app.py --server.headless true
```

### Streamlit Community Cloud
1. Push the repository to GitHub (make sure `.env` and
   `.streamlit/secrets.toml` are **not** committed).
2. In Streamlit Cloud -> *Settings -> Secrets* add:
   ```toml
   [postgres]
   host="..."
   port=5432
   dbname="digital_twin"
   user="..."
   password="..."
   ```
   and (optional):
   ```toml
   [llm]
   provider="gemini"
   GEMINI_API_KEY="..."
   GEMINI_MODEL="gemini-3.7-flash"
   ```
3. Set the main script path to `app.py`.

### Docker (example)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
```

> **Important:** Use Streamlit secrets / environment variables for credentials.
> The app never logs API keys and never displays raw stack traces to users.

---

## 12. Security

- `.env` and `.streamlit/secrets.toml` are in `.gitignore` and never committed.
- API keys are read from environment variables / Streamlit secrets, never hard-coded.
- API keys are never logged, printed, or exposed in the UI.
- User data is strictly isolated by `user_id` - User A never receives User B's data.
- User input is treated as untrusted; prompt injection rules are enforced in the system prompt.
- Passwords are hashed with PBKDF2-SHA256.
- Session tokens use HMAC-SHA256 JWT.
- Database credentials are never exposed in error messages.
- Raw stack traces are never shown to end users.

---

## 13. Known Limitations

- The **LLM is an explanation layer**, not a computation engine. It does not
  perform calculations itself; it narrates the app's deterministic results.
- The **rule-based assistant** covers the main Digital Twin question categories
  (finance, study, habits, fitness, goals, simulations, recommendations). More
  nuanced open-ended questions may yield a more detailed answer with Gemini.
- The **simulation engine** uses linear/proportional models with an optional ML
  performance predictor for study; it is a planning aid, not financial/fitness
  advice.
- Forecasts and simulations are **not guaranteed outcomes** - they are
  projections based on the current simulation.
- The app requires a reachable PostgreSQL server; analytics and simulation
  features need logged data to display meaningful results.
- `google-genai` SDK versions may vary; if the Gemini
  provider is selected without an installed SDK, the app reports the missing
  dependency and uses the built-in assistant as fallback.
