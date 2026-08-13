# 🧬 Digital Twin AI

**Your data-driven digital twin — track it, understand it, predict it.**

Digital Twin AI is a personal life simulation and decision-assistant app. It builds a living profile of you from the data you log — finances, study habits, daily routines, and personal habits — then turns that history into forecasts and insights you can actually act on.

Built with **Streamlit** and **PostgreSQL**.

---

## ✨ Features

### 🏠 Dashboard
A single-glance overview of your digital twin: a profile summary card (name, occupation, age, goal score, days active), a savings trend mini-chart with a 1-year projection, weekly study hours, and a snapshot of your habit predictions.

### 🧑‍💼 Personal Data & Profile
- Set and track personal **goals** with live progress bars
- Log new personal data and manage your **daily schedule**
- A **Behavioral Patterns** widget that compares today against your historical average once you have more than a day of data

### 💰 Financial Analyst
- Full CRUD on your financial records
- A savings projection chart plotting actual vs. forecasted savings
- Key metrics: current savings, monthly savings rate, projected savings in 1 year

### 📚 Study & Productivity
- Log study sessions with subject, hours, and performance score
- Weekly study-hours chart
- Insights on peak focus time, completion rate, and average performance

### ✅ Habit Tracker
- Log habits with status (Done / Partial / Missed) and completion rate
- Automatic **habit predictions** — consistency rate and trend direction for every habit you've logged, including custom ones
- Full habit log with history

### 🔐 Authentication
- Secure registration and login
- Passwords stored as salted **PBKDF2-SHA256** hashes — never in plain text
- A "Forgot Password" flow with privacy-safe generic responses

### 🧠 AI Core Layer (Milestone 2)
- Health, fitness, study and finance AI tabs inside the existing pages
- Models live in the sibling `Milestone 2/ai_models` folder (single source of truth)
- Every prediction is logged to the `digital_twin` database for traceability

---

## 🗂️ Project Structure

```
digital_twin_ai/
├── app.py                  # Entry point — routing, sidebar, header/footer
├── ai_bridge.py            # Links this app to the Milestone 2 AI Core Layer
├── database.py              # PostgreSQL connection pool, schema, CRUD, analytics
├── utils.py                 # Theme CSS, password hashing, session helpers
├── ui_components.py         # Header, footer, profile summary block
├── auth.py                  # Login / register / forgot-password screens
├── requirements.txt
├── .streamlit/
│   └── secrets.toml.example
└── pages_app/
    ├── dashboard.py          # Overview page
    ├── profile.py            # Profile, goals, data entry, schedule
    ├── financial.py          # Financial Analyst: CRUD + savings forecast
    ├── study.py               # Study & Productivity: CRUD + weekly hours
    └── habits.py              # Habit Tracker: CRUD + habit predictions
```

The AI Core Layer (Milestone 2) is kept in the sibling `Milestone 2/ai_models`
folder and is imported through `ai_bridge.py`, so both milestones run as one
application against the same `digital_twin` database.

---

## 🗃️ Database Schema

On first run, the app automatically creates the following tables:

| Table | Purpose |
|---|---|
| `Users` | Account info, credentials, and profile details |
| `Financial_Records` | Income, expenses, and savings entries |
| `Study_Activities` | Study sessions, hours, and performance scores |
| `Habits` | Habit logs with status and completion rate |
| `Goals` | Personal goals and progress tracking |
| `Daily_Schedule` | Daily schedule entries |

---

## 🚀 Getting Started

### 1. Install PostgreSQL

Install PostgreSQL locally (or use a managed instance), then create the database:

```sql
CREATE DATABASE digital_twin;
```

Tables are created automatically the first time the app runs.

### 2. Configure the connection

Copy the example secrets file and fill in your credentials:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

```toml
[postgres]
host = "localhost"
port = 5432
dbname = "digital_twin"
user = "postgres"
password = "your_password"
```

Alternatively, set the environment variables `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` — these are used automatically if `secrets.toml` is absent.

### 3. Install dependencies & run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL Streamlit prints (usually `http://localhost:8501`), register a new account, and start logging your data.

### Linked execution (Milestone 1 + Milestone 2)

From the **project root** (`project/`), launch both milestones as one app:

```bash
python run.py          # or .\run.ps1
```

`run.py` starts the Streamlit UI and verifies the Milestone 2 AI Core Layer is
present at `project/Milestone 2/ai_models`. The UI imports the AI core through
`ai_bridge.py`; both milestones share the same `digital_twin` database. To run
only the AI-core unit tests: `cd ../Milestone 2 && python -m pytest tests -q`.

---

## 🧠 How the Forecasting Works

Forecasts — savings projections, weekly study hours, and habit predictions — are computed directly from your logged data using trend and linear extrapolation logic in `database.py`. Since every page calls the same `db.get_*` functions, you can swap in a more sophisticated ML model later without touching any page-level code.

---

## 🛠️ Tech Stack

- **[Streamlit](https://streamlit.io/)** — UI framework
- **PostgreSQL** — data storage (via `psycopg2`)
- **Pandas** — data wrangling
- **Plotly** — interactive charts

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).