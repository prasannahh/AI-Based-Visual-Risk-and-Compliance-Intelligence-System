"""
database.py
Handles all PostgreSQL connectivity, schema creation, CRUD operations,
and lightweight analytics queries for Digital Twin AI.

Database: digital_twin (PostgreSQL)
Connection is configured via .streamlit/secrets.toml (preferred) or
environment variables (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD).
No Docker is used - connect directly to a local/remote PostgreSQL server.
"""

import os
from contextlib import contextmanager
from datetime import date, timedelta

import pandas as pd
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
import streamlit as st


# --------------------------------------------------------------------------- #
# Connection handling
# --------------------------------------------------------------------------- #
def _get_config():
    """Read DB config from st.secrets first, then environment, then defaults."""
    try:
        s = st.secrets["postgres"]
        return dict(
            host=s.get("host", "localhost"),
            port=s.get("port", 5432),
            dbname=s.get("dbname", "digital_twin"),
            user=s.get("user", "postgres"),
            password=s.get("password", "postgres"),
        )
    except Exception:
        return dict(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "digital_twin"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
        )


@st.cache_resource(show_spinner=False)
def get_pool():
    cfg = _get_config()
    return psycopg2.pool.SimpleConnectionPool(1, 10, **cfg)


@contextmanager
def get_cursor(commit: bool = False):
    """Context manager yielding a RealDictCursor from the pool."""
    conn_pool = get_pool()
    conn = conn_pool.getconn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn_pool.putconn(conn)


def test_connection() -> tuple[bool, str]:
    try:
        with get_cursor() as cur:
            cur.execute("SELECT 1;")
        return True, "Connected"
    except Exception as e:
        return False, str(e)

def _floatify(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    """psycopg2 returns PostgreSQL NUMERIC columns as Python Decimal objects.
    pandas keeps those as object-dtype, and mixing Decimal with float in
    arithmetic raises TypeError (e.g. 'Decimal / float', 'float + Decimal').
    Cast the given numeric columns to plain float64 right after fetching so
    every downstream calculation works with normal floats."""
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype(float)
    return df


# --------------------------------------------------------------------------- #
# Schema initialization
# --------------------------------------------------------------------------- #
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS Users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(160) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    gender VARCHAR(10) CHECK (gender IN ('Male', 'Female')) NOT NULL,
    age INT,
    occupation VARCHAR(120),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS Financial_Records (
    record_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    category VARCHAR(80) NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    transaction_type VARCHAR(20) CHECK (transaction_type IN ('Income','Expense','Savings')) NOT NULL,
    date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS Study_Activities (
    activity_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    subject VARCHAR(120) NOT NULL,
    hours_logged NUMERIC(5,2) NOT NULL,
    performance_score NUMERIC(5,2),
    date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS Habits (
    habit_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    habit_name VARCHAR(120) NOT NULL,
    status VARCHAR(20) CHECK (status IN ('Done','Missed','Partial')) NOT NULL,
    completion_rate NUMERIC(5,2) NOT NULL,
    date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS Goals (
    goal_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    goal_name VARCHAR(120) NOT NULL,
    target_amount NUMERIC(12,2) NOT NULL,
    current_progress NUMERIC(12,2) DEFAULT 0,
    target_date DATE
);

CREATE TABLE IF NOT EXISTS Daily_Schedule (
    schedule_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    activity_name VARCHAR(150) NOT NULL,
    planned_time TIME,
    actual_time TIME,
    status VARCHAR(20) DEFAULT 'Upcoming',
    date DATE NOT NULL
);
"""


def init_db():
    with get_cursor(commit=True) as cur:
        cur.execute(SCHEMA_SQL)


# --------------------------------------------------------------------------- #
# Users / Auth
# --------------------------------------------------------------------------- #
def create_user(name, email, password_hash, gender, age, occupation):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO Users (name, email, password_hash, gender, age, occupation)
               VALUES (%s,%s,%s,%s,%s,%s) RETURNING user_id;""",
            (name, email, password_hash, gender, age, occupation),
        )
        return cur.fetchone()["user_id"]


def get_user_by_email(email):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM Users WHERE email = %s;", (email,))
        return cur.fetchone()


def get_user(user_id):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM Users WHERE user_id = %s;", (user_id,))
        return cur.fetchone()


def update_user_profile(user_id, **fields):
    if not fields:
        return
    cols = ", ".join(f"{k} = %s" for k in fields)
    with get_cursor(commit=True) as cur:
        cur.execute(
            f"UPDATE Users SET {cols} WHERE user_id = %s;",
            (*fields.values(), user_id),
        )


def get_days_active(user_id) -> int:
    """Distinct calendar days on which the user logged any activity."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(DISTINCT d) FROM (
                SELECT date AS d FROM Financial_Records WHERE user_id=%s
                UNION SELECT date FROM Study_Activities WHERE user_id=%s
                UNION SELECT date FROM Habits WHERE user_id=%s
                UNION SELECT date FROM Daily_Schedule WHERE user_id=%s
            ) t;
            """,
            (user_id, user_id, user_id, user_id),
        )
        row = cur.fetchone()
        return int(row["count"]) if row and row["count"] else 0


# --------------------------------------------------------------------------- #
# Financial Records
# --------------------------------------------------------------------------- #
def add_financial_record(user_id, category, amount, transaction_type, date_):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO Financial_Records (user_id, category, amount, transaction_type, date)
               VALUES (%s,%s,%s,%s,%s);""",
            (user_id, category, amount, transaction_type, date_),
        )


def get_financial_records(user_id) -> pd.DataFrame:
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM Financial_Records WHERE user_id=%s ORDER BY date DESC;",
            (user_id,),
        )
        rows = cur.fetchall()
    return _floatify(pd.DataFrame(rows), ["amount"])


def update_financial_record(record_id, **fields):
    if not fields:
        return
    cols = ", ".join(f"{k} = %s" for k in fields)
    with get_cursor(commit=True) as cur:
        cur.execute(
            f"UPDATE Financial_Records SET {cols} WHERE record_id = %s;",
            (*fields.values(), record_id),
        )


def delete_financial_record(record_id):
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM Financial_Records WHERE record_id=%s;", (record_id,))


# --------------------------------------------------------------------------- #
# Study Activities
# --------------------------------------------------------------------------- #
def add_study_activity(user_id, subject, hours_logged, performance_score, date_):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO Study_Activities (user_id, subject, hours_logged, performance_score, date)
               VALUES (%s,%s,%s,%s,%s);""",
            (user_id, subject, hours_logged, performance_score, date_),
        )


def get_study_activities(user_id) -> pd.DataFrame:
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM Study_Activities WHERE user_id=%s ORDER BY date DESC;",
            (user_id,),
        )
        rows = cur.fetchall()
    return _floatify(pd.DataFrame(rows), ["hours_logged", "performance_score"])


def update_study_activity(activity_id, **fields):
    if not fields:
        return
    cols = ", ".join(f"{k} = %s" for k in fields)
    with get_cursor(commit=True) as cur:
        cur.execute(
            f"UPDATE Study_Activities SET {cols} WHERE activity_id = %s;",
            (*fields.values(), activity_id),
        )


def delete_study_activity(activity_id):
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM Study_Activities WHERE activity_id=%s;", (activity_id,))


# --------------------------------------------------------------------------- #
# Habits
# --------------------------------------------------------------------------- #
def add_habit(user_id, habit_name, status, completion_rate, date_):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO Habits (user_id, habit_name, status, completion_rate, date)
               VALUES (%s,%s,%s,%s,%s);""",
            (user_id, habit_name, status, completion_rate, date_),
        )


def get_habits(user_id) -> pd.DataFrame:
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM Habits WHERE user_id=%s ORDER BY date DESC;", (user_id,)
        )
        rows = cur.fetchall()
    return _floatify(pd.DataFrame(rows), ["completion_rate"])



def update_habit(habit_id, **fields):
    if not fields:
        return
    cols = ", ".join(f"{k} = %s" for k in fields)
    with get_cursor(commit=True) as cur:
        cur.execute(
            f"UPDATE Habits SET {cols} WHERE habit_id = %s;",
            (*fields.values(), habit_id),
        )


def delete_habit(habit_id):
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM Habits WHERE habit_id=%s;", (habit_id,))


def get_habit_names(user_id) -> list:
    """Distinct habit names actually logged by this user_id in the database
    (includes custom habits) - used to render Habit Predictions / Dashboard
    dynamically instead of a hardcoded category list."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT DISTINCT habit_name FROM Habits WHERE user_id=%s ORDER BY habit_name;",
            (user_id,),
        )
        rows = cur.fetchall()
    return [r["habit_name"] for r in rows]


# --------------------------------------------------------------------------- #
# Goals
# --------------------------------------------------------------------------- #
def add_goal(user_id, goal_name, target_amount, current_progress, target_date):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO Goals (user_id, goal_name, target_amount, current_progress, target_date)
               VALUES (%s,%s,%s,%s,%s);""",
            (user_id, goal_name, target_amount, current_progress, target_date),
        )


def get_goals(user_id) -> pd.DataFrame:
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM Goals WHERE user_id=%s ORDER BY goal_id;", (user_id,)
        )
        rows = cur.fetchall()
    return _floatify(pd.DataFrame(rows), ["target_amount", "current_progress"])


def update_goal_progress(goal_id, current_progress):
    with get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE Goals SET current_progress=%s WHERE goal_id=%s;",
            (current_progress, goal_id),
        )


def delete_goal(goal_id):
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM Goals WHERE goal_id=%s;", (goal_id,))


# --------------------------------------------------------------------------- #
# Daily Schedule
# --------------------------------------------------------------------------- #
def get_schedule(user_id, date_) -> pd.DataFrame:
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM Daily_Schedule WHERE user_id=%s AND date=%s ORDER BY planned_time;",
            (user_id, date_),
        )
        rows = cur.fetchall()
    return pd.DataFrame(rows)


def replace_schedule(user_id, date_, rows: list[dict]):
    """Replace all schedule rows for a given user/date with the provided rows."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            "DELETE FROM Daily_Schedule WHERE user_id=%s AND date=%s;",
            (user_id, date_),
        )
        for r in rows:
            if not r.get("activity_name"):
                continue
            cur.execute(
                """INSERT INTO Daily_Schedule
                   (user_id, activity_name, planned_time, actual_time, status, date)
                   VALUES (%s,%s,%s,%s,%s,%s);""",
                (
                    user_id,
                    r.get("activity_name"),
                    r.get("planned_time") or None,
                    r.get("actual_time") or None,
                    r.get("status") or "Upcoming",
                    date_,
                ),
            )


def update_schedule_status(schedule_id, status):
    """Update just the status of a single Daily_Schedule row - used by the
    'Today's Checklist' checkboxes so checking an item doesn't require
    resaving the whole schedule editor."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE Daily_Schedule SET status=%s WHERE schedule_id=%s;",
            (status, schedule_id),
        )


def get_schedule_history(user_id) -> pd.DataFrame:
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM Daily_Schedule WHERE user_id=%s ORDER BY date;", (user_id,)
        )
        rows = cur.fetchall()
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Analytics helpers (used by Milestone 1 behavioral widget & Milestone 2 forecasts)
# --------------------------------------------------------------------------- #
def compute_behavioral_patterns(user_id, today: date) -> dict:
    """
    Returns a dict of {pattern_name: {"value": str, "trend_pct": float}}.
    Crucial logic: on the user's first active day, only today's data is used
    (trend shown as 0%). From day 2 onward, today is compared against the
    historical average of all prior days.
    """
    fin = get_financial_records(user_id)
    study = get_study_activities(user_id)
    sched = get_schedule_history(user_id)

    active_days = get_days_active(user_id)
    is_first_day = active_days <= 1

    patterns = {}

    # Dining Out - from Financial_Records where category ~ 'Dining' / 'Food'
    if not fin.empty:
        fin["date"] = pd.to_datetime(fin["date"]).dt.date
        dining = fin[fin["category"].str.contains("Din|Food|Restaurant", case=False, na=False)]
        today_val = dining[dining["date"] == today]["amount"].sum()
        if is_first_day or dining.empty:
            patterns["Dining Out"] = {"value": f"₹{today_val:,.0f} today", "trend_pct": 0.0}
        else:
            hist = dining[dining["date"] < today]
            hist_avg = hist["amount"].sum() / max(hist["date"].nunique(), 1)
            trend = ((today_val - hist_avg) / hist_avg * 100) if hist_avg else 0.0
            patterns["Dining Out"] = {"value": f"₹{today_val:,.0f} today", "trend_pct": round(trend, 1)}
    else:
        patterns["Dining Out"] = {"value": "No data", "trend_pct": 0.0}

    # Study Time - from Study_Activities
    if not study.empty:
        study["date"] = pd.to_datetime(study["date"]).dt.date
        today_hours = study[study["date"] == today]["hours_logged"].astype(float).sum()
        if is_first_day:
            patterns["Study Time"] = {"value": f"{today_hours:.1f}h today", "trend_pct": 0.0}
        else:
            hist = study[study["date"] < today]
            hist_avg = hist.groupby("date")["hours_logged"].sum().mean() if not hist.empty else 0
            trend = ((today_hours - hist_avg) / hist_avg * 100) if hist_avg else 0.0
            patterns["Study Time"] = {"value": f"{today_hours:.1f}h today", "trend_pct": round(trend, 1)}
    else:
        patterns["Study Time"] = {"value": "No data", "trend_pct": 0.0}

    # Sleep Pattern - from Daily_Schedule where activity contains 'sleep'
    if not sched.empty:
        sched["date"] = pd.to_datetime(sched["date"]).dt.date
        sleep_rows = sched[sched["activity_name"].str.contains("Sleep", case=False, na=False)]
        today_sleep = sleep_rows[sleep_rows["date"] == today]
        today_status = "Logged" if not today_sleep.empty else "Not logged"
        if is_first_day or sleep_rows.empty:
            patterns["Sleep Pattern"] = {"value": today_status, "trend_pct": 0.0}
        else:
            hist_days = sleep_rows[sleep_rows["date"] < today]["date"].nunique()
            total_days = max(active_days - 1, 1)
            consistency = hist_days / total_days * 100
            trend = consistency - 100  # deviation from perfectly consistent
            patterns["Sleep Pattern"] = {"value": today_status, "trend_pct": round(trend, 1)}
    else:
        patterns["Sleep Pattern"] = {"value": "No data", "trend_pct": 0.0}

    return patterns


def get_savings_forecast(user_id):
    """Returns (history_df[date, cumulative_savings], projected_1yr_value, monthly_rate)."""
    fin = get_financial_records(user_id)
    if fin.empty:
        return pd.DataFrame(columns=["date", "cumulative_savings"]), 0.0, 0.0

    fin["date"] = pd.to_datetime(fin["date"])
    fin["net"] = fin.apply(
        lambda r: r["amount"] if r["transaction_type"] in ("Income", "Savings") else -r["amount"],
        axis=1,
    )
    daily = fin.groupby("date")["net"].sum().sort_index()
    cumulative = daily.cumsum().reset_index()
    cumulative.columns = ["date", "cumulative_savings"]

    if len(cumulative) < 2:
        current = float(cumulative["cumulative_savings"].iloc[-1]) if not cumulative.empty else 0.0
        return cumulative, current, 0.0

    span_days = max((cumulative["date"].iloc[-1] - cumulative["date"].iloc[0]).days, 1)
    total_change = cumulative["cumulative_savings"].iloc[-1] - cumulative["cumulative_savings"].iloc[0]
    daily_rate = total_change / span_days
    monthly_rate = daily_rate * 30
    projected_1yr = float(cumulative["cumulative_savings"].iloc[-1]) + daily_rate * 365
    return cumulative, projected_1yr, monthly_rate


def get_weekly_study_hours(user_id) -> pd.DataFrame:
    study = get_study_activities(user_id)
    if study.empty:
        return pd.DataFrame(columns=["day", "hours"])
    study["date"] = pd.to_datetime(study["date"])
    last_7 = study[study["date"] >= (pd.Timestamp.today() - pd.Timedelta(days=7))]
    if last_7.empty:
        last_7 = study
    day_names = last_7["date"].dt.day_name().rename("day")
    grouped = last_7.groupby(day_names)["hours_logged"].sum()
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    grouped = grouped.reindex(order).fillna(0)
    result = grouped.reset_index()
    result.columns = ["day", "hours"]
    return result


def get_peak_focus_time(user_id) -> str:
    """Most common planned hour among Study/Focus/Work schedule entries.
    If two or more hours are tied for most frequent, the tie is broken by
    date: whichever tied hour appears in the most recently logged entry
    wins, rather than always defaulting to the smallest hour."""
    sched = get_schedule_history(user_id)
    if sched.empty:
        return "Not enough data"
    study_rows = sched[sched["activity_name"].str.contains("Study|Focus|Work", case=False, na=False)]
    study_rows = study_rows.dropna(subset=["planned_time"]).copy()
    if study_rows.empty:
        return "Not enough data"

    study_rows["hour"] = study_rows["planned_time"].apply(lambda t: t.hour if hasattr(t, "hour") else 0)
    study_rows["date"] = pd.to_datetime(study_rows["date"])

    counts = study_rows["hour"].value_counts()
    if counts.empty:
        return "Not enough data"

    top_count = counts.max()
    tied_hours = counts[counts == top_count].index.tolist()

    if len(tied_hours) == 1:
        h = int(tied_hours[0])
    else:
        # Tie: use the date entry to decide - pick the hour from whichever
        # tied hour's most recent entry is the latest overall.
        tied_rows = study_rows[study_rows["hour"].isin(tied_hours)]
        latest_row = tied_rows.sort_values("date").iloc[-1]
        h = int(latest_row["hour"])

    return f"{h % 12 or 12}:00 {'AM' if h < 12 else 'PM'}"


def get_habit_prediction(user_id, keyword) -> dict:
    """Returns {'rate': float, 'trend_pct': float, 'insight': str} for a habit category."""
    habits = get_habits(user_id)
    if habits.empty:
        return {"rate": 0.0, "trend_pct": 0.0, "insight": "No data logged yet."}
    matches = habits[habits["habit_name"].str.contains(keyword, case=False, na=False)]
    if matches.empty:
        return {"rate": 0.0, "trend_pct": 0.0, "insight": "No data logged yet."}
    matches = matches.sort_values("date")
    rate = float(matches["completion_rate"].astype(float).mean())
    recent = matches.tail(3)["completion_rate"].astype(float).mean()
    earlier = matches.head(max(len(matches) - 3, 1))["completion_rate"].astype(float).mean()
    trend = ((recent - earlier) / earlier * 100) if earlier else 0.0

    if rate >= 75:
        insight = f"Strong consistency on {keyword.lower()} — keep the streak going."
    elif rate >= 45:
        insight = f"Moderate consistency on {keyword.lower()} — small nudges could help."
    else:
        insight = f"Risk of slipping on {keyword.lower()} — consider a lighter, easier target."
    return {"rate": round(rate, 1), "trend_pct": round(trend, 1), "insight": insight}


def get_habit_prediction_by_name(user_id, habit_name) -> dict:
    """Same as get_habit_prediction, but matches the habit_name exactly
    rather than by keyword substring. Used so custom/user-defined habits
    (which may not contain any of the default keywords) still get a
    prediction card on the Habit Tracker and Dashboard pages."""
    habits = get_habits(user_id)
    if habits.empty:
        return {"rate": 0.0, "trend_pct": 0.0, "insight": "No data logged yet."}
    matches = habits[habits["habit_name"] == habit_name]
    if matches.empty:
        return {"rate": 0.0, "trend_pct": 0.0, "insight": "No data logged yet."}
    matches = matches.sort_values("date")
    rate = float(matches["completion_rate"].astype(float).mean())
    recent = matches.tail(3)["completion_rate"].astype(float).mean()
    earlier = matches.head(max(len(matches) - 3, 1))["completion_rate"].astype(float).mean()
    trend = ((recent - earlier) / earlier * 100) if earlier else 0.0

    label = habit_name.lower()
    if rate >= 75:
        insight = f"Strong consistency on {label} — keep the streak going."
    elif rate >= 45:
        insight = f"Moderate consistency on {label} — small nudges could help."
    else:
        insight = f"Risk of slipping on {label} — consider a lighter, easier target."
    return {"rate": round(rate, 1), "trend_pct": round(trend, 1), "insight": insight}
