"""
api.py
FastAPI backend service for Digital Twin AI.
Exposes REST endpoints for the React modern SaaS frontend while preserving
the existing Python business logic and PostgreSQL database as the source of truth.
"""

from __future__ import annotations

import datetime
from datetime import date, time, timezone
import logging
import os
from typing import Any, Literal, Optional

logger = logging.getLogger("api")

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pydantic import BaseModel, Field

import ai_bridge  # noqa: F401 - ensure ai_models is on sys.path
import ai.prompt_templates as templates
import database as db
from ai.config import get_llm_config, has_valid_api_key
from ai.conversation_service import ConversationError, ConversationService
from simulation.comparator import ScenarioResult, compare_scenarios, get_comparison_table
from simulation.engine import SimulationRequest, _compute_fitness_score, run_simulation
from ai_models.study import predict as study_ai
from ai_models.study import model as study_model
from ai_models.finance import predict as fin_ai
from ai_models.fitness import predict as fitness_ai
from ai_models.health import predict as health_ai
from utils import create_token, hash_password, validate_token, verify_password

app = FastAPI(
    title="Digital Twin Decision Intelligence API",
    description="Backend API serving the modern React dashboard while preserving Python source of truth.",
    version="1.0.0",
)

# Enable CORS for the React/Vite development server and preview
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Bootstrap database schema if tables do not exist yet."""
    try:
        db.init_db()
    except Exception as e:
        print(f"Warning: Database init failed on API startup: {e}")


# --------------------------------------------------------------------------- #
# Auth Models & Dependency
# --------------------------------------------------------------------------- #
class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., min_length=3, max_length=160)
    password: str = Field(..., min_length=6)
    gender: str = Field(default="Male", pattern="^(Male|Female)$")
    age: int = Field(default=25, ge=10, le=100)
    occupation: Optional[str] = Field(default="Professional", max_length=120)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=160)
    password: str


class ChatAskRequest(BaseModel):
    message: str = Field(..., min_length=1)


class LegacyChatRequest(BaseModel):
    user_id: str
    message: str


class TaskCreateRequest(BaseModel):
    activity_name: str = Field(..., min_length=1, max_length=150)
    date: Optional[str] = None  # YYYY-MM-DD
    planned_time: Optional[str] = None  # HH:MM or HH:MM:SS
    actual_time: Optional[str] = None
    status: Optional[str] = Field(default="Upcoming", pattern="^(Upcoming|In Progress|Completed|Missed)$")


class TaskUpdateRequest(BaseModel):
    activity_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    date: Optional[str] = None
    planned_time: Optional[str] = None
    actual_time: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(Upcoming|In Progress|Completed|Missed)$")


class TaskStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(Upcoming|In Progress|Completed|Missed)$")


class StudyActivityCreateRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=120)
    hours_logged: float = Field(..., ge=0.1, le=24.0)
    performance_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    date: Optional[str] = None  # YYYY-MM-DD, defaults to today


class StudyActivityUpdateRequest(BaseModel):
    subject: Optional[str] = Field(default=None, min_length=1, max_length=120)
    hours_logged: Optional[float] = Field(default=None, ge=0.1, le=24.0)
    performance_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    date: Optional[str] = None


class StudyPredictRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=120)
    hours_logged: float = Field(default=2.0, ge=0.0, le=24.0)
    days_to_exam: int = Field(default=30, ge=1, le=365)
    study_consistency: float = Field(default=0.6, ge=0.0, le=1.0)
    prior_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)


class SuggestionItem(BaseModel):
    id: str
    category: str
    priority: str
    title: str
    description: str
    reason: Optional[str] = None
    benefits: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    action: Optional[str] = None
    action_route: Optional[str] = None
    action_label: Optional[str] = None
    evidence: Optional[dict[str, Any]] = None
    created_at: Optional[str] = None


class UnlockAction(BaseModel):
    title: str
    description: str
    route: str
    label: str


class CalibrationState(BaseModel):
    is_calibrated: bool
    message: str
    missing_data: list[str]
    unlock_actions: list[UnlockAction]


class SuggestionsResponse(BaseModel):
    has_data: bool
    total_count: int
    categories: list[str]
    priority_counts: dict[str, int]
    suggestions: list[SuggestionItem]
    calibration_state: CalibrationState


class TransactionCreateRequest(BaseModel):
    category: str = Field(..., min_length=1, max_length=60)
    amount: float = Field(..., gt=0.0)
    transaction_type: str = Field(..., pattern="^(Income|Expense|Savings)$")
    date: Optional[str] = None


class TransactionUpdateRequest(BaseModel):
    category: Optional[str] = Field(default=None, min_length=1, max_length=60)
    amount: Optional[float] = Field(default=None, gt=0.0)
    transaction_type: Optional[str] = Field(default=None, pattern="^(Income|Expense|Savings)$")
    date: Optional[str] = None


class ExpenseClassifyRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=200)


class ForecastSimulateRequest(BaseModel):
    horizon_months: int = Field(default=12, ge=1, le=36)
    extra_monthly_savings: float = Field(default=0.0, ge=0.0)


class TransactionItem(BaseModel):
    record_id: int
    user_id: int
    category: str
    amount: float
    transaction_type: str
    date: str


class FinancialSummary(BaseModel):
    total_income: Optional[float]
    total_expenses: Optional[float]
    net_cash_flow: Optional[float]
    total_savings: Optional[float]
    monthly_rate: Optional[float]
    savings_rate_pct: Optional[float]
    transaction_count: int
    months_active: int


class SpendingCategoryPoint(BaseModel):
    category: str
    spent: float
    percentage: float


class SpendingMonthlyPoint(BaseModel):
    month: str
    spent: float


class SpendingAnalysisData(BaseModel):
    total_spent: Optional[float]
    top_category: Optional[str]
    top_category_amount: Optional[float]
    category_wise: list[SpendingCategoryPoint]
    monthly: list[SpendingMonthlyPoint]


class SavingsTrendPoint(BaseModel):
    date: str
    cumulative_savings: float


class SavingsTrendData(BaseModel):
    history: list[SavingsTrendPoint]
    forecast_1yr: Optional[float]
    monthly_rate: Optional[float]


class BudgetCategoryLimit(BaseModel):
    category: str
    limit: float


class BudgetRecommendationData(BaseModel):
    has_budget: bool
    monthly_budget: Optional[float]
    weekly_budget: Optional[float]
    emergency_fund: Optional[float]
    savings_goal: Optional[float]
    basis: str
    category_limits: list[BudgetCategoryLimit]


class WealthOverviewResponse(BaseModel):
    has_data: bool
    summary: FinancialSummary
    transactions: list[TransactionItem]
    spending_analysis: SpendingAnalysisData
    savings_trend: SavingsTrendData
    budget_recommendation: BudgetRecommendationData
    supported_categories: list[str]
    supported_types: list[str]


class ExpenseClassifyResponse(BaseModel):
    description: str
    category: str
    confidence: float
    is_prediction: bool


class ForecastTimelinePoint(BaseModel):
    month: int
    date: str
    projected_savings: float


class ForecastSimulateResponse(BaseModel):
    current_savings: float
    baseline_monthly_rate: float
    effective_monthly_rate: float
    horizon_months: int
    projected_final_savings: float
    projected_timeline: list[ForecastTimelinePoint]


# --------------------------------------------------------------------------- #
# Analytics Models
# --------------------------------------------------------------------------- #
class AnalyticsOverviewMetrics(BaseModel):
    productivity_score: Optional[float]
    tasks_completed: int
    tasks_total: int
    study_hours: Optional[float]
    avg_study_score: Optional[float]
    net_cash_flow: Optional[float]
    total_savings: Optional[float]
    habit_consistency: Optional[float]
    avg_sleep_hours: Optional[float]
    active_goals_count: int
    avg_goal_progress: Optional[float]


class ProductivityPoint(BaseModel):
    date: str
    completed: int
    total: int
    completion_rate: float


class ProductivityTrendData(BaseModel):
    has_data: bool
    series: list[ProductivityPoint]


class StudyDailyPoint(BaseModel):
    date: str
    hours: float
    avg_score: Optional[float]


class StudySubjectPoint(BaseModel):
    subject: str
    hours: float
    percentage: float
    avg_score: Optional[float]


class StudyAnalyticsData(BaseModel):
    has_data: bool
    total_hours: float
    sessions_count: int
    avg_performance_score: Optional[float]
    peak_focus_time: str
    daily_trend: list[StudyDailyPoint]
    subject_breakdown: list[StudySubjectPoint]


class FinancialCashflowPoint(BaseModel):
    period: str
    income: float
    expenses: float
    net: float


class FinancialAnalyticsData(BaseModel):
    has_data: bool
    total_income: float
    total_expenses: float
    net_savings: float
    spending_by_category: list[SpendingCategoryPoint]
    cashflow_trend: list[FinancialCashflowPoint]


class HabitMetricPoint(BaseModel):
    habit_name: str
    rate: float
    trend_pct: float
    insight: str


class SleepActivityPoint(BaseModel):
    date: str
    sleep_hours: Optional[float]
    steps: Optional[float]
    exercise_minutes: Optional[float]


class HabitLifestyleAnalyticsData(BaseModel):
    has_data: bool
    overall_consistency: Optional[float]
    habits: list[HabitMetricPoint]
    sleep_activity_trend: list[SleepActivityPoint]


class GoalAnalyticsPoint(BaseModel):
    goal_id: int
    goal_name: str
    target_amount: float
    current_progress: float
    progress_pct: float
    target_date: Optional[str]


class GoalsAnalyticsData(BaseModel):
    has_data: bool
    goals: list[GoalAnalyticsPoint]


class TwinInsight(BaseModel):
    domain: str
    title: str
    message: str
    type: str  # 'positive' | 'neutral' | 'attention'


class AnalyticsResponse(BaseModel):
    range: str
    start_date: str
    end_date: str
    has_data: bool
    overview_metrics: AnalyticsOverviewMetrics
    productivity_trend: ProductivityTrendData
    study_analytics: StudyAnalyticsData
    financial_analytics: FinancialAnalyticsData
    habit_lifestyle_analytics: HabitLifestyleAnalyticsData
    goals_progress: GoalsAnalyticsData
    twin_insights: list[TwinInsight]


# --------------------------------------------------------------------------- #
# Milestone 3 — What-If Simulator Schemas
# --------------------------------------------------------------------------- #
class FinancialGoalItem(BaseModel):
    goal_id: int
    goal_name: str
    target_amount: float
    current_progress: float
    target_date: Optional[str] = None


class SimulationBaselineFinancial(BaseModel):
    has_data: bool
    monthly_income: float
    monthly_expenses: float
    monthly_savings: float
    total_savings: float
    goals: list[FinancialGoalItem]


class SimulationBaselineStudy(BaseModel):
    has_data: bool
    avg_hours_per_day: float
    avg_performance_score: float
    subjects: list[str]
    days_active: int


class SimulationBaselineHabits(BaseModel):
    has_data: bool
    avg_completion_rate: float
    exercise_frequency: int
    avg_steps: float
    avg_sleep_hours: float
    avg_exercise_minutes: float
    habit_names: list[str]


class SimulationBaselineResponse(BaseModel):
    financial: SimulationBaselineFinancial
    study: SimulationBaselineStudy
    habits: SimulationBaselineHabits


class CustomScenarioInput(BaseModel):
    name: str
    description: Optional[str] = None
    monthly_saving: Optional[float] = None
    monthly_expenses: Optional[float] = None
    hours_per_day: Optional[float] = None
    completion_rate: Optional[float] = None
    exercise_frequency: Optional[int] = None


class RunSimulationRequest(BaseModel):
    domain: Literal["finance", "study", "habits"]
    horizon_months: int = Field(default=12, ge=1, le=60)
    consistency: Optional[float] = Field(default=0.6, ge=0.0, le=1.0)
    custom_scenarios: Optional[list[CustomScenarioInput]] = None


class ScenarioResultSchema(BaseModel):
    name: str
    description: str
    is_baseline: bool
    input_params: dict[str, Any]
    output_metrics: dict[str, Any]
    score: float
    score_breakdown: dict[str, float]
    time_series: list[dict[str, Any]]


class SimulationRecommendationSchema(BaseModel):
    recommended_scenario: str
    score: float
    reason: str
    benefits: list[str]
    risks: list[str]
    next_actions: list[str]
    baseline_comparison: dict[str, Any]


class RunSimulationResponse(BaseModel):
    domain: str
    horizon_months: int
    has_baseline_data: bool
    scenarios: list[ScenarioResultSchema]
    comparison_table: list[dict[str, Any]]
    recommendation: Optional[SimulationRecommendationSchema] = None
    assumptions: list[str]
    disclaimer: str


class SaveSimulationRequest(BaseModel):
    domain: Literal["finance", "study", "habits"]
    title: str
    horizon_months: int = Field(default=12, ge=1, le=60)
    scenarios: list[ScenarioResultSchema]
    recommendation: Optional[SimulationRecommendationSchema] = None
    parameters: Optional[dict[str, Any]] = None


class SaveSimulationResponse(BaseModel):
    simulation_id: int
    message: str


class SimulationHistoryItem(BaseModel):
    simulation_id: int
    simulation_type: str
    title: str
    horizon_months: int
    created_at: str
    parameters: Optional[dict[str, Any]] = None


# --------------------------------------------------------------------------- #
# Milestone 1 — User Profile & Goals Schemas
# --------------------------------------------------------------------------- #
class UserProfileResponse(BaseModel):
    user_id: int
    name: str
    email: str
    gender: Optional[str] = None
    age: Optional[int] = None
    occupation: Optional[str] = None
    created_at: str
    days_active: int
    active_goals_count: int
    completed_goals_count: int
    avg_goal_progress: float
    latest_health: Optional[dict[str, Any]] = None


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    gender: Optional[Literal["Male", "Female"]] = None
    age: Optional[int] = Field(None, ge=10, le=120)
    occupation: Optional[str] = Field(None, max_length=120)


class GoalResponse(BaseModel):
    goal_id: int
    user_id: int
    goal_name: str
    target_amount: float
    current_progress: float
    target_date: Optional[str] = None
    progress_pct: float
    is_completed: bool
    status: str  # 'completed' | 'overdue' | 'active'
    days_remaining: Optional[int] = None


class GoalsListResponse(BaseModel):
    goals: list[GoalResponse]
    active_count: int
    completed_count: int
    avg_progress_pct: float


class CreateGoalRequest(BaseModel):
    goal_name: str = Field(..., min_length=1, max_length=120)
    target_amount: float = Field(..., gt=0)
    current_progress: Optional[float] = Field(default=0.0, ge=0)
    target_date: Optional[str] = None


class UpdateGoalRequest(BaseModel):
    goal_name: Optional[str] = Field(None, min_length=1, max_length=120)
    target_amount: Optional[float] = Field(None, gt=0)
    current_progress: Optional[float] = Field(None, ge=0)
    target_date: Optional[str] = None


# --------------------------------------------------------------------------- #
# Milestone 1 — Settings & Preferences Schemas
# --------------------------------------------------------------------------- #
class UserPreferences(BaseModel):
    currency: str = Field("INR", pattern="^(INR|USD|EUR|GBP)$")
    timezone: str = Field("Asia/Kolkata", min_length=2, max_length=60)
    date_format: str = Field("YYYY-MM-DD", pattern="^(YYYY-MM-DD|DD/MM/YYYY|MM/DD/YYYY)$")
    theme: str = Field("light", pattern="^(light|dark|system)$")
    ai_suggestions_enabled: bool = True
    weekly_digest_enabled: bool = False


class UpdatePreferencesRequest(BaseModel):
    currency: Optional[str] = Field(None, pattern="^(INR|USD|EUR|GBP)$")
    timezone: Optional[str] = Field(None, min_length=2, max_length=60)
    date_format: Optional[str] = Field(None, pattern="^(YYYY-MM-DD|DD/MM/YYYY|MM/DD/YYYY)$")
    theme: Optional[str] = Field(None, pattern="^(light|dark|system)$")
    ai_suggestions_enabled: Optional[bool] = None
    weekly_digest_enabled: Optional[bool] = None


class AISystemConfig(BaseModel):
    provider: str
    model: str
    has_api_key: bool
    temperature: float
    max_tokens: int
    offline_fallback_active: bool


class AccountSecurityInfo(BaseModel):
    user_id: int
    email: str
    name: str
    created_at: Optional[str] = None
    auth_method: str = "JWT (HS256)"
    password_encryption: str = "PBKDF2-SHA256 (100,000 iterations)"
    session_duration_hours: int = 24


class SettingsResponse(BaseModel):
    preferences: UserPreferences
    ai_config: AISystemConfig
    account_security: AccountSecurityInfo


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Extract and validate the HS256 JWT from the Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed authorization header. Expected 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    claims = validate_token(token)
    if not claims or "user_id" not in claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or token is invalid. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.get_user(int(claims["user_id"]))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account does not exist or has been removed.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# --------------------------------------------------------------------------- #
# Health Check Endpoint
# --------------------------------------------------------------------------- #
@app.get("/api/health")
def health_check():
    db_ok, db_msg = db.test_connection()
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": {"connected": db_ok, "detail": db_msg},
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


# --------------------------------------------------------------------------- #
# Authentication Endpoints
# --------------------------------------------------------------------------- #
@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register_endpoint(req: RegisterRequest):
    clean_email = req.email.strip().lower()
    existing = db.get_user_by_email(clean_email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    try:
        user_id = db.create_user(
            name=req.name.strip(),
            email=clean_email,
            password_hash=hash_password(req.password),
            gender=req.gender,
            age=req.age,
            occupation=(req.occupation or "").strip(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {e}",
        )

    user_payload = {
        "user_id": user_id,
        "name": req.name.strip(),
        "email": clean_email,
        "gender": req.gender,
        "age": req.age,
        "occupation": (req.occupation or "").strip(),
    }
    token = create_token(user_payload)
    return {"token": token, "user": user_payload}


@app.post("/api/auth/login")
def login_endpoint(req: LoginRequest):
    clean_email = req.email.strip().lower()
    user = db.get_user_by_email(clean_email)
    if not user or not verify_password(req.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    user_payload = {
        "user_id": user["user_id"],
        "name": user["name"],
        "email": user["email"],
        "gender": user["gender"],
        "age": user.get("age"),
        "occupation": user.get("occupation") or "",
    }
    token = create_token(user_payload)
    return {"token": token, "user": user_payload}


@app.get("/api/auth/me")
def me_endpoint(current_user: dict = Depends(get_current_user)):
    return {
        "user": {
            "user_id": current_user["user_id"],
            "name": current_user["name"],
            "email": current_user["email"],
            "gender": current_user.get("gender"),
            "age": current_user.get("age"),
            "occupation": current_user.get("occupation") or "",
            "created_at": str(current_user.get("created_at", "")),
        }
    }


# --------------------------------------------------------------------------- #
# Milestone 1 — User Profile Endpoints
# --------------------------------------------------------------------------- #
@app.get("/api/profile", response_model=UserProfileResponse)
def get_profile_endpoint(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    days_active = db.get_days_active(user_id)
    goals_df = db.get_goals(user_id)

    active_goals = 0
    completed_goals = 0
    total_progress = 0.0

    if not goals_df.empty:
        for _, g in goals_df.iterrows():
            target = float(g.get("target_amount") or 0.0)
            curr = float(g.get("current_progress") or 0.0)
            pct = min((curr / target * 100.0) if target > 0 else 0.0, 100.0)
            total_progress += pct
            if curr >= target and target > 0:
                completed_goals += 1
            else:
                active_goals += 1
        avg_progress = round(total_progress / len(goals_df), 1)
    else:
        avg_progress = 0.0

    latest_health = db.get_latest_health(user_id)
    health_data = None
    if latest_health and (latest_health.get("height_cm") or latest_health.get("weight_kg")):
        h = latest_health.get("height_cm")
        w = latest_health.get("weight_kg")
        bmi_val = None
        bmi_cat = None
        if h and w and h > 0:
            bmi_val = round(w / ((h / 100.0) ** 2), 1)
            if bmi_val < 18.5:
                bmi_cat = "Underweight"
            elif bmi_val < 25:
                bmi_cat = "Normal"
            elif bmi_val < 30:
                bmi_cat = "Overweight"
            else:
                bmi_cat = "Obese"
        health_data = {
            "record_date": str(latest_health.get("record_date") or ""),
            "height_cm": h,
            "weight_kg": w,
            "bmi": bmi_val,
            "bmi_category": bmi_cat,
        }

    return UserProfileResponse(
        user_id=user_id,
        name=current_user["name"],
        email=current_user["email"],
        gender=current_user.get("gender"),
        age=current_user.get("age"),
        occupation=current_user.get("occupation") or "",
        created_at=str(current_user.get("created_at") or ""),
        days_active=days_active,
        active_goals_count=active_goals,
        completed_goals_count=completed_goals,
        avg_goal_progress=avg_progress,
        latest_health=health_data,
    )


@app.put("/api/profile", response_model=UserProfileResponse)
def update_profile_endpoint(
    req: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    fields_to_update = {}
    if req.name is not None:
        fields_to_update["name"] = req.name.strip()
    if req.gender is not None:
        fields_to_update["gender"] = req.gender
    if req.age is not None:
        fields_to_update["age"] = req.age
    if req.occupation is not None:
        fields_to_update["occupation"] = req.occupation.strip()

    if fields_to_update:
        db.update_user_profile(user_id, **fields_to_update)

    updated_user = db.get_user(user_id)
    return get_profile_endpoint(current_user=updated_user)


# --------------------------------------------------------------------------- #
# Milestone 1 — Goals Endpoints
# --------------------------------------------------------------------------- #
def _format_goal(g: dict, user_id: int) -> GoalResponse:
    target = float(g.get("target_amount") or 0.0)
    curr = float(g.get("current_progress") or 0.0)
    raw_pct = (curr / target * 100.0) if target > 0 else 0.0
    progress_pct = round(min(max(raw_pct, 0.0), 100.0), 1)
    is_completed = curr >= target and target > 0

    t_date_raw = g.get("target_date")
    t_date_str = str(t_date_raw).strip() if t_date_raw and not pd.isna(t_date_raw) else None
    days_remaining = None
    status_str = "active"

    if is_completed:
        status_str = "completed"
    elif t_date_str:
        try:
            t_date = datetime.date.fromisoformat(t_date_str)
            today = datetime.date.today()
            diff = (t_date - today).days
            days_remaining = diff
            if diff < 0:
                status_str = "overdue"
        except Exception:
            pass

    return GoalResponse(
        goal_id=int(g["goal_id"]),
        user_id=user_id,
        goal_name=str(g["goal_name"]),
        target_amount=target,
        current_progress=curr,
        target_date=t_date_str,
        progress_pct=progress_pct,
        is_completed=is_completed,
        status=status_str,
        days_remaining=days_remaining,
    )


@app.get("/api/goals", response_model=GoalsListResponse)
def get_goals_endpoint(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    goals_df = db.get_goals(user_id)
    if goals_df.empty:
        return GoalsListResponse(
            goals=[],
            active_count=0,
            completed_count=0,
            avg_progress_pct=0.0,
        )

    results: list[GoalResponse] = []
    active_count = 0
    completed_count = 0
    total_progress = 0.0

    for _, row in goals_df.iterrows():
        g_dict = row.to_dict()
        resp = _format_goal(g_dict, user_id)
        results.append(resp)
        if resp.is_completed:
            completed_count += 1
        else:
            active_count += 1
        total_progress += resp.progress_pct

    avg_progress = round(total_progress / len(results), 1) if results else 0.0

    return GoalsListResponse(
        goals=results,
        active_count=active_count,
        completed_count=completed_count,
        avg_progress_pct=avg_progress,
    )


@app.post("/api/goals", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal_endpoint(
    req: CreateGoalRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    t_date = None
    if req.target_date and req.target_date.strip():
        try:
            t_date = datetime.date.fromisoformat(req.target_date.strip())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid target_date format. Expected YYYY-MM-DD.",
            )

    goal_id = db.add_goal(
        user_id=user_id,
        goal_name=req.goal_name.strip(),
        target_amount=float(req.target_amount),
        current_progress=float(req.current_progress or 0.0),
        target_date=t_date,
    )
    if not goal_id:
        goals_df = db.get_goals(user_id)
        if not goals_df.empty:
            goal_id = int(goals_df.iloc[-1]["goal_id"])
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create goal.")

    new_goal = db.get_goal(goal_id, user_id=user_id)
    if not new_goal:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Goal creation succeeded but retrieval failed.")

    return _format_goal(new_goal, user_id)


@app.put("/api/goals/{goal_id}", response_model=GoalResponse)
def update_goal_endpoint(
    goal_id: int,
    req: UpdateGoalRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    existing = db.get_goal(goal_id, user_id=user_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goal with id {goal_id} not found for this user.",
        )

    fields_to_update = {}
    if req.goal_name is not None:
        fields_to_update["goal_name"] = req.goal_name.strip()
    if req.target_amount is not None:
        fields_to_update["target_amount"] = float(req.target_amount)
    if req.current_progress is not None:
        fields_to_update["current_progress"] = float(req.current_progress)
    if req.target_date is not None:
        if req.target_date.strip():
            try:
                fields_to_update["target_date"] = datetime.date.fromisoformat(req.target_date.strip())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid target_date format. Expected YYYY-MM-DD.",
                )
        else:
            fields_to_update["target_date"] = None

    if fields_to_update:
        db.update_goal(goal_id, user_id=user_id, **fields_to_update)

    updated = db.get_goal(goal_id, user_id=user_id)
    return _format_goal(updated, user_id)


@app.delete("/api/goals/{goal_id}")
def delete_goal_endpoint(
    goal_id: int,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    existing = db.get_goal(goal_id, user_id=user_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goal with id {goal_id} not found for this user.",
        )

    deleted = db.delete_goal(goal_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete goal.")

    return {"message": "Goal deleted successfully", "goal_id": goal_id}


# --------------------------------------------------------------------------- #
# Settings & Preferences Endpoints
# --------------------------------------------------------------------------- #
def _build_ai_config_response() -> AISystemConfig:
    try:
        cfg = get_llm_config()
        provider = cfg.provider
        model = cfg.model or "gemini-3.7-flash"
        has_key = has_valid_api_key(cfg) if provider == "gemini" else True
        temp = float(cfg.temperature)
        tokens = int(cfg.max_tokens)
    except Exception:
        provider = "rule_based"
        model = "deterministic-fallback"
        has_key = True
        temp = 0.3
        tokens = 600

    return AISystemConfig(
        provider=provider,
        model=model,
        has_api_key=has_key,
        temperature=temp,
        max_tokens=tokens,
        offline_fallback_active=True,
    )


def _build_account_security_response(current_user: dict) -> AccountSecurityInfo:
    jwt_exp_hours = int(os.getenv("JWT_EXPIRES_HOURS", "24"))
    return AccountSecurityInfo(
        user_id=current_user["user_id"],
        email=current_user["email"],
        name=current_user.get("name") or "",
        created_at=str(current_user.get("created_at", "")),
        auth_method="JWT (HS256)",
        password_encryption="PBKDF2-SHA256 (100,000 iterations)",
        session_duration_hours=jwt_exp_hours,
    )


@app.get("/api/settings", response_model=SettingsResponse)
def get_settings_endpoint(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    prefs_dict = db.get_user_settings(user_id)
    return SettingsResponse(
        preferences=UserPreferences(**prefs_dict),
        ai_config=_build_ai_config_response(),
        account_security=_build_account_security_response(current_user),
    )


@app.put("/api/settings", response_model=SettingsResponse)
def update_settings_endpoint(
    req: UpdatePreferencesRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    updates = req.model_dump(exclude_unset=True)
    updated_prefs = db.update_user_settings(user_id, **updates)

    return SettingsResponse(
        preferences=UserPreferences(**updated_prefs),
        ai_config=_build_ai_config_response(),
        account_security=_build_account_security_response(current_user),
    )


# --------------------------------------------------------------------------- #
# Tasks & Planner Endpoints
# --------------------------------------------------------------------------- #
def _format_task_time(val: Any) -> Optional[str]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, time):
        return val.strftime("%H:%M")
    s = str(val).strip()
    if not s or s.lower() in ("none", "nat"):
        return None
    if len(s) == 8 and s.count(":") == 2:
        return s[:5]
    return s


def _format_task_date(val: Any) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return str(date.today())
    if isinstance(val, (date, datetime.datetime)):
        return val.strftime("%Y-%m-%d")
    return str(val)[:10]


@app.get("/api/tasks")
def get_tasks_endpoint(
    task_date: Optional[str] = Query(None, alias="date"),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    query_date: Optional[date] = None

    if task_date and task_date.lower() != "all":
        try:
            query_date = date.fromisoformat(task_date.strip())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Expected YYYY-MM-DD or 'all'.",
            )
    elif not task_date:
        query_date = date.today()

    if task_date and task_date.lower() == "all":
        df = db.get_schedule_history(user_id)
        selected_date_str = "all"
    else:
        df = db.get_schedule(user_id, query_date)
        selected_date_str = str(query_date)

    tasks = []
    if not df.empty:
        for _, row in df.iterrows():
            tasks.append(
                {
                    "schedule_id": int(row["schedule_id"]),
                    "user_id": int(row["user_id"]),
                    "activity_name": str(row["activity_name"]),
                    "planned_time": _format_task_time(row.get("planned_time")),
                    "actual_time": _format_task_time(row.get("actual_time")),
                    "status": str(row.get("status") or "Upcoming"),
                    "date": _format_task_date(row.get("date")),
                }
            )

    total = len(tasks)
    completed = sum(1 for t in tasks if t["status"] == "Completed")
    upcoming = sum(1 for t in tasks if t["status"] == "Upcoming")
    in_progress = sum(1 for t in tasks if t["status"] == "In Progress")
    missed = sum(1 for t in tasks if t["status"] == "Missed")
    completion_rate = round((completed / total) * 100, 1) if total > 0 else 0.0
    peak_focus = db.get_peak_focus_time(user_id)

    return {
        "date": selected_date_str,
        "tasks": tasks,
        "summary": {
            "total_tasks": total,
            "completed_tasks": completed,
            "upcoming_tasks": upcoming,
            "in_progress_tasks": in_progress,
            "missed_tasks": missed,
            "completion_rate": completion_rate,
            "peak_focus_time": peak_focus,
        },
    }


@app.post("/api/tasks", status_code=status.HTTP_201_CREATED)
def create_task_endpoint(
    req: TaskCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    try:
        task_date = date.fromisoformat(req.date.strip()) if req.date else date.today()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Expected YYYY-MM-DD.",
        )

    sid = db.add_schedule_item(
        user_id=user_id,
        date_=task_date,
        activity_name=req.activity_name.strip(),
        planned_time=req.planned_time.strip() if req.planned_time else None,
        actual_time=req.actual_time.strip() if req.actual_time else None,
        status=req.status or "Upcoming",
    )
    return {
        "schedule_id": sid,
        "user_id": user_id,
        "activity_name": req.activity_name.strip(),
        "planned_time": req.planned_time,
        "actual_time": req.actual_time,
        "status": req.status or "Upcoming",
        "date": str(task_date),
    }


@app.patch("/api/tasks/{schedule_id}/status")
def update_task_status_endpoint(
    schedule_id: int,
    req: TaskStatusUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    ok = db.update_schedule_item(
        schedule_id=schedule_id,
        user_id=user_id,
        status=req.status,
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or access denied.",
        )
    return {"schedule_id": schedule_id, "status": req.status, "ok": True}


@app.put("/api/tasks/{schedule_id}")
def update_task_endpoint(
    schedule_id: int,
    req: TaskUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    parsed_date = None
    if req.date:
        try:
            parsed_date = date.fromisoformat(req.date.strip())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Expected YYYY-MM-DD.",
            )

    ok = db.update_schedule_item(
        schedule_id=schedule_id,
        user_id=user_id,
        activity_name=req.activity_name.strip() if req.activity_name else None,
        planned_time=req.planned_time.strip() if req.planned_time else None,
        actual_time=req.actual_time.strip() if req.actual_time else None,
        status=req.status,
        date_=parsed_date,
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or access denied.",
        )
    return {"schedule_id": schedule_id, "ok": True, "message": "Task updated successfully."}


@app.delete("/api/tasks/{schedule_id}")
def delete_task_endpoint(
    schedule_id: int,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    ok = db.delete_schedule_item(schedule_id=schedule_id, user_id=user_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or access denied.",
        )
    return {"ok": True, "message": "Task deleted successfully."}


# --------------------------------------------------------------------------- #
# Study & Academic Endpoints
# --------------------------------------------------------------------------- #
@app.get("/api/study")
def get_study_overview_endpoint(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    study_df = db.get_study_activities(user_id)
    has_data = not study_df.empty

    activities = []
    if has_data:
        for _, row in study_df.iterrows():
            score = (
                float(row["performance_score"])
                if row.get("performance_score") is not None and not pd.isna(row.get("performance_score"))
                else None
            )
            activities.append(
                {
                    "activity_id": int(row["activity_id"]),
                    "user_id": int(row["user_id"]),
                    "subject": str(row["subject"]),
                    "hours_logged": round(float(row["hours_logged"]), 1),
                    "performance_score": score,
                    "date": _format_task_date(row.get("date")),
                }
            )

    # Weekly study hours (only populated if real records exist)
    weekly_df = db.get_weekly_study_hours(user_id)
    weekly_hours = []
    weekly_total = 0.0
    if not weekly_df.empty and weekly_df["hours"].sum() > 0:
        weekly_hours = [
            {"day": str(r["day"]), "hours": round(float(r["hours"]), 1)}
            for _, r in weekly_df.iterrows()
        ]
        weekly_total = float(weekly_df["hours"].sum())

    # Summary metrics - honest null/unavailable when no data
    if has_data:
        total_hours = round(float(study_df["hours_logged"].astype(float).sum()), 1)
        total_sessions = len(activities)
        valid_scores = study_df["performance_score"].dropna()
        avg_score = round(float(valid_scores.mean()), 1) if not valid_scores.empty else None

        study_df_copy = study_df.copy()
        study_df_copy["date"] = pd.to_datetime(study_df_copy["date"])
        days_active = int(study_df_copy["date"].dt.date.nunique())
        avg_hours_day = round(total_hours / days_active, 1) if days_active > 0 else total_hours
        completion_rate = round(min(100.0, (weekly_total / 14.0 * 100)), 1) if weekly_total > 0 else 0.0

        # Per-subject breakdown
        subjects_summary = []
        for subj, group in study_df.groupby("subject"):
            subj_scores = group["performance_score"].dropna()
            subjects_summary.append(
                {
                    "subject": str(subj),
                    "total_hours": round(float(group["hours_logged"].sum()), 1),
                    "session_count": len(group),
                    "avg_score": round(float(subj_scores.mean()), 1) if not subj_scores.empty else None,
                }
            )
        subjects_summary.sort(key=lambda x: x["total_hours"], reverse=True)
    else:
        total_hours = None
        total_sessions = 0
        avg_score = None
        avg_hours_day = None
        days_active = 0
        completion_rate = None
        subjects_summary = []

    peak_focus = db.get_peak_focus_time(user_id)

    # Weak subjects detection via ML model
    weak_subjects = []
    if has_data:
        try:
            weak_subjects = study_ai.detect_weak_subjects(study_df)
        except Exception:
            weak_subjects = []

    # Study goals (only goals relating to study/learning)
    goals_df = db.get_goals(user_id)
    study_goals = []
    if not goals_df.empty:
        study_keywords = (
            "study",
            "academic",
            "exam",
            "course",
            "grade",
            "gpa",
            "learn",
            "book",
            "read",
            "degree",
        )
        for _, g in goals_df.iterrows():
            g_name = str(g.get("goal_name") or "")
            if any(kw in g_name.lower() for kw in study_keywords):
                target = float(g.get("target_amount") or 0)
                curr = float(g.get("current_progress") or 0)
                pct = round((curr / target * 100) if target > 0 else 0, 1)
                study_goals.append(
                    {
                        "goal_id": int(g["goal_id"]),
                        "goal_name": g_name,
                        "target_amount": target,
                        "current_progress": curr,
                        "target_date": str(g.get("target_date") or ""),
                        "progress_pct": min(pct, 100.0),
                    }
                )

    return {
        "has_data": has_data,
        "activities": activities,
        "summary": {
            "total_hours": total_hours,
            "total_sessions": total_sessions,
            "avg_performance_score": avg_score,
            "avg_hours_per_day": avg_hours_day,
            "days_active": days_active,
            "peak_focus_time": peak_focus,
            "completion_rate": completion_rate,
        },
        "weekly_hours": weekly_hours,
        "subjects_summary": subjects_summary,
        "weak_subjects": weak_subjects,
        "study_goals": study_goals,
        "supported_subjects": study_model.SUBJECTS,
    }


@app.post("/api/study/activities", status_code=status.HTTP_201_CREATED)
def create_study_activity_endpoint(
    req: StudyActivityCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    try:
        activity_date = date.fromisoformat(req.date.strip()) if req.date else date.today()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Expected YYYY-MM-DD.",
        )

    db.add_study_activity(
        user_id=user_id,
        subject=req.subject.strip(),
        hours_logged=req.hours_logged,
        performance_score=req.performance_score,
        date_=activity_date,
    )

    df = db.get_study_activities(user_id)
    new_act = df.iloc[0].to_dict() if not df.empty else {}

    return {
        "activity_id": int(new_act.get("activity_id", 0)),
        "user_id": user_id,
        "subject": req.subject.strip(),
        "hours_logged": req.hours_logged,
        "performance_score": req.performance_score,
        "date": str(activity_date),
    }


@app.put("/api/study/activities/{activity_id}")
def update_study_activity_endpoint(
    activity_id: int,
    req: StudyActivityUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    fields = {}
    if req.subject is not None:
        fields["subject"] = req.subject.strip()
    if req.hours_logged is not None:
        fields["hours_logged"] = req.hours_logged
    if req.performance_score is not None:
        fields["performance_score"] = req.performance_score
    if req.date is not None:
        try:
            fields["date"] = date.fromisoformat(req.date.strip())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Expected YYYY-MM-DD.",
            )

    if not fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update fields provided.",
        )

    ok = db.update_study_activity(activity_id=activity_id, user_id=user_id, **fields)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study activity not found or access denied.",
        )
    return {
        "activity_id": activity_id,
        "ok": True,
        "message": "Study activity updated successfully.",
    }


@app.delete("/api/study/activities/{activity_id}")
def delete_study_activity_endpoint(
    activity_id: int,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    ok = db.delete_study_activity(activity_id=activity_id, user_id=user_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study activity not found or access denied.",
        )
    return {"ok": True, "message": "Study activity deleted successfully."}


@app.post("/api/study/predict")
def predict_study_performance_endpoint(
    req: StudyPredictRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    prior = req.prior_score
    if prior is None:
        study_df = db.get_study_activities(user_id)
        if not study_df.empty and "subject" in study_df.columns and "performance_score" in study_df.columns:
            subj_scores = pd.to_numeric(
                study_df.loc[study_df["subject"] == req.subject.strip(), "performance_score"],
                errors="coerce",
            ).dropna()
            prior = float(subj_scores.mean()) if not subj_scores.empty else 70.0
        else:
            prior = 70.0

    result = study_ai.predict_performance(
        subject=req.subject.strip(),
        hours_logged=req.hours_logged,
        days_to_exam=req.days_to_exam,
        study_consistency=req.study_consistency,
        prior_score=prior,
    )

    try:
        db.log_study_prediction(
            user_id=user_id,
            prediction_type="performance_prediction",
            result_value=result["predicted_score"],
            result_category=result["band"],
            confidence=1.0,
            input_data={
                "subject": req.subject.strip(),
                "hours": req.hours_logged,
                "days_to_exam": req.days_to_exam,
                "consistency": req.study_consistency,
                "prior_score": prior,
            },
            output_data=result,
        )
    except Exception:
        pass

    return {
        "subject": req.subject.strip(),
        "predicted_score": result["predicted_score"],
        "predicted_gpa": result["predicted_gpa"],
        "band": result["band"],
        "prior_score": round(prior, 1),
        "is_prediction": True,
    }


# --------------------------------------------------------------------------- #
# Suggestions & Recommendations Endpoint
# --------------------------------------------------------------------------- #
@app.get("/api/suggestions", response_model=SuggestionsResponse)
def get_suggestions_endpoint(current_user: dict = Depends(get_current_user)):
    """Retrieve personalized recommendations grounded in real user data.

    Integrates saved simulation recommendations, academic weak subject analysis,
    50/30/20 budget guidance, habit and sleep assessments, and goal deadlines.
    When insufficient data exists, returns an honest uncalibrated state.
    """
    user_id = current_user["user_id"]
    suggestions: list[dict] = []

    # 1. Saved Recommendations from Simulation table
    try:
        recs_df = db.get_recommendations(user_id, limit=20)
        if recs_df is not None and not recs_df.empty:
            for _, r in recs_df.iterrows():
                rec_id = int(r.get("recommendation_id", 0))
                cat = str(r.get("category") or "Simulation").capitalize()
                priority = str(r.get("priority") or "Medium").capitalize()
                if priority not in ["Critical", "High", "Medium", "Low"]:
                    priority = "Medium"
                text = r.get("recommendation_text") or r.get("reason") or "Simulation recommendation"
                action_text = r.get("next_action") or "Review scenario in What-If Simulator"
                risks_list = [rk.strip() for rk in str(r.get("risks") or "").split(";") if rk.strip()]
                suggestions.append({
                    "id": f"sim_rec_{rec_id}",
                    "category": cat,
                    "priority": priority,
                    "title": f"Scenario Suggestion: {cat}",
                    "description": text,
                    "reason": r.get("reason"),
                    "benefits": [],
                    "risks": risks_list,
                    "action": action_text,
                    "action_route": "/simulation",
                    "action_label": "What-If Simulator",
                    "evidence": {"source": "Simulation Engine", "simulation_id": r.get("simulation_id")},
                    "created_at": str(r.get("created_at") or ""),
                })
    except Exception as e:
        logger.warning("Error reading saved recommendations: %s", e)

    # 2. Study activities
    study_df = None
    try:
        study_df = db.get_study_activities(user_id)
        if study_df is not None and not study_df.empty:
            # Weak subject analysis
            weak = study_ai.detect_weak_subjects(study_df)
            for item in weak:
                lvl = item.get("level", "Medium")
                sub = item.get("subject", "")
                sub_id = sub.lower().replace(" ", "_")
                if lvl in ["Critical", "High", "Medium"]:
                    suggestions.append({
                        "id": f"study_weak_{sub_id}",
                        "category": "Study",
                        "priority": lvl,
                        "title": f"Weak Subject Alert: {sub}",
                        "description": f"Average score in {sub} is {item.get('avg_score', 0):.1f}%. Machine learning models flag a performance risk score of {item.get('risk_score', 0):.1f}/100.",
                        "reason": f"Historical performance in {sub} falls below mastery threshold.",
                        "benefits": [f"Targeting {sub} yields the highest expected GPA improvement."],
                        "risks": ["Unaddressed weak topics compound in future examinations."],
                        "action": f"Schedule focused study sessions for {sub}.",
                        "action_route": "/study",
                        "action_label": "Study & Academic",
                        "evidence": {
                            "subject": sub,
                            "avg_score": round(float(item.get("avg_score", 0)), 1),
                            "risk_score": round(float(item.get("risk_score", 0)), 1),
                            "risk_level": lvl,
                        },
                        "created_at": None,
                    })

            # Study allocation optimization
            opt = study_ai.optimize_study_schedule(study_df, total_hours=20.0)
            if opt is not None and not opt.empty:
                top_sub = opt.iloc[0]
                rec_hrs = float(top_sub.get("recommended_hours", 0))
                if rec_hrs > 0:
                    sub_name = str(top_sub.get("subject", ""))
                    sub_id = sub_name.lower().replace(" ", "_")
                    suggestions.append({
                        "id": f"study_opt_{sub_id}",
                        "category": "Study",
                        "priority": "Medium",
                        "title": f"Study Hours Allocation: {sub_name}",
                        "description": f"Based on historical scores and curriculum weighting, allocate {rec_hrs:.1f} hours this week to {sub_name}.",
                        "reason": "Derived from priority scoring combining subject weakness and exam proximity.",
                        "benefits": ["Balances overall academic workload according to optimal learning distribution."],
                        "risks": [],
                        "action": f"Log focus sessions for {sub_name}.",
                        "action_route": "/study",
                        "action_label": "Study & Academic",
                        "evidence": {
                            "subject": sub_name,
                            "recommended_hours": rec_hrs,
                            "priority_score": round(float(top_sub.get("priority_score", 0)), 1),
                        },
                        "created_at": None,
                    })
    except Exception as e:
        logger.warning("Error evaluating study suggestions: %s", e)

    # 3. Financial records
    finance_df = None
    try:
        finance_df = db.get_financial_records(user_id)
        if finance_df is not None and not finance_df.empty:
            fin_summary = db.get_user_financial_summary(user_id)
            budget = fin_ai.recommend_budget(finance_df)
            income = float(fin_summary.get("monthly_income", 0.0) or 0.0)
            expense = float(fin_summary.get("monthly_expenses", 0.0) or 0.0)
            monthly_budget = float(budget.get("monthly_budget", 0.0) or 0.0)
            savings_goal = float(budget.get("savings_goal", 0.0) or 0.0)
            emergency_fund = float(budget.get("emergency_fund", 0.0) or 0.0)

            if expense > income and income > 0:
                suggestions.append({
                    "id": "fin_deficit_alert",
                    "category": "Finance",
                    "priority": "Critical",
                    "title": "Monthly Cash Flow Deficit",
                    "description": f"Monthly spending (₹{expense:,.0f}) exceeds monthly income (₹{income:,.0f}) by ₹{expense - income:,.0f}.",
                    "reason": "Outflows surpass total monthly inflows across logged transactions.",
                    "benefits": ["Eliminating spending deficits prevents capital depletion and debt accumulation."],
                    "risks": ["Sustained negative monthly cash flow drains savings and emergency reserves."],
                    "action": "Review high-expense categories in Wealth Planner.",
                    "action_route": "/wealth",
                    "action_label": "Wealth Planner",
                    "evidence": {
                        "monthly_income": income,
                        "monthly_expenses": expense,
                        "deficit": expense - income,
                    },
                    "created_at": None,
                })
            elif monthly_budget > 0:
                suggestions.append({
                    "id": "fin_budget_allocation",
                    "category": "Finance",
                    "priority": "Medium",
                    "title": "50/30/20 Budget & Savings Target",
                    "description": f"Recommended monthly spending cap: ₹{monthly_budget:,.0f}. Aim for savings of ₹{savings_goal:,.0f}/month with an emergency reserve of ₹{emergency_fund:,.0f}.",
                    "reason": "Standard 50/30/20 balanced budget rule applied to logged cash flow.",
                    "benefits": ["Maintains structured allocation across essential needs, wants, and savings."],
                    "risks": ["Operating without an emergency cushion leaves finances vulnerable to shocks."],
                    "action": "Inspect budget limits and savings forecast.",
                    "action_route": "/wealth",
                    "action_label": "Wealth Planner",
                    "evidence": {
                        "monthly_budget": monthly_budget,
                        "savings_goal": savings_goal,
                        "emergency_fund": emergency_fund,
                    },
                    "created_at": None,
                })
    except Exception as e:
        logger.warning("Error evaluating finance suggestions: %s", e)

    # 4. Habits & Wellness
    habits_df = None
    fitness_df = None
    try:
        habits_df = db.get_habits(user_id)
        fitness_df = db.get_fitness_records(user_id)
        habit_summary = db.get_user_habit_summary(user_id)
        comp_rate = float(habit_summary.get("avg_completion_rate", 0.0) or 0.0)
        sleep = float(habit_summary.get("avg_sleep_hours", 0.0) or 0.0)
        steps = float(habit_summary.get("avg_steps", 0.0) or 0.0)

        if sleep > 0 and sleep < 6.5:
            suggestions.append({
                "id": "health_sleep_deficiency",
                "category": "Health",
                "priority": "High",
                "title": "Restorative Sleep Deficit",
                "description": f"Average recorded sleep is {sleep:.1f} hours/night, which is below the 7–8 hour recommended restorative baseline.",
                "reason": "Sleep duration logged in habit records falls below healthy cognitive recovery levels.",
                "benefits": ["Improves executive function, memory consolidation, and daytime energy."],
                "risks": ["Chronic sleep debt impairs immune resistance and metabolic regulation."],
                "action": "Schedule an earlier wind-down routine in Daily Planner.",
                "action_route": "/tasks",
                "action_label": "Tasks & Planner",
                "evidence": {"avg_sleep_hours": sleep, "recommended_min": 7.0},
                "created_at": None,
            })

        if comp_rate > 0 and comp_rate < 50.0:
            suggestions.append({
                "id": "habits_completion_lag",
                "category": "Habits",
                "priority": "High",
                "title": "Daily Routine Consistency Lag",
                "description": f"Habit completion rate is currently {comp_rate:.0f}%. Focus on completing top-priority morning routines to build daily momentum.",
                "reason": "Fewer than half of scheduled daily routines are being marked complete.",
                "benefits": ["Consistent daily routines reduce decision fatigue and build discipline."],
                "risks": ["Inconsistent habits delay compound personal development milestones."],
                "action": "Review and check off daily activities in Tasks & Planner.",
                "action_route": "/tasks",
                "action_label": "Tasks & Planner",
                "evidence": {"completion_rate": comp_rate},
                "created_at": None,
            })

        if steps > 0 and steps < 5000:
            suggestions.append({
                "id": "fitness_low_steps",
                "category": "Fitness",
                "priority": "Medium",
                "title": "Physical Activity Below Active Baseline",
                "description": f"Average daily step count is {steps:,.0f} steps, below the 5,000-step active threshold.",
                "reason": "Activity tracking records show predominantly sedentary daily patterns.",
                "benefits": ["Supports cardiovascular health and sustained metabolic calorie burn."],
                "risks": ["Prolonged inactivity increases long-term cardiometabolic risk."],
                "action": "Schedule walking blocks in Tasks & Planner.",
                "action_route": "/tasks",
                "action_label": "Tasks & Planner",
                "evidence": {"avg_steps": steps, "target_baseline": 5000},
                "created_at": None,
            })
    except Exception as e:
        logger.warning("Error evaluating habit suggestions: %s", e)

    # 5. Goals tracking
    goals = []
    try:
        goals = db.get_user_goals(user_id)
        if goals:
            today = date.today()
            for g in goals:
                target = float(g.get("target_amount", 0) or 0)
                curr = float(g.get("current_progress", 0) or 0)
                pct = (curr / target * 100.0) if target > 0 else 0.0
                target_date_str = str(g.get("target_date") or "")
                goal_name = g.get("goal_name") or "Untitled Goal"
                gid = g.get("goal_id")
                if target > 0 and pct < 100.0 and target_date_str:
                    try:
                        target_dt = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").date()
                        days_left = (target_dt - today).days
                        if days_left < 0:
                            suggestions.append({
                                "id": f"goal_expired_{gid}",
                                "category": "Goals",
                                "priority": "High",
                                "title": f"Goal Deadline Expired: {goal_name}",
                                "description": f"'{goal_name}' reached target date {target_date_str} at {pct:.0f}% completion ({curr:,.0f}/{target:,.0f}).",
                                "reason": "Target completion date has passed without reaching target milestone.",
                                "benefits": ["Re-calibrating milestones restores achievable progress tracking."],
                                "risks": ["Unadjusted overdue goals lead to tracking fatigue."],
                                "action": "Update progress or extend deadline in Profile & Goals.",
                                "action_route": "/profile",
                                "action_label": "Profile & Goals",
                                "evidence": {
                                    "goal_name": goal_name,
                                    "progress_pct": round(pct, 1),
                                    "target_date": target_date_str,
                                    "days_overdue": abs(days_left),
                                },
                                "created_at": None,
                            })
                        elif days_left <= 14 and pct < 70.0:
                            suggestions.append({
                                "id": f"goal_deadline_{gid}",
                                "category": "Goals",
                                "priority": "High",
                                "title": f"Goal Approaching Deadline: {goal_name}",
                                "description": f"'{goal_name}' is at {pct:.0f}% completion with {days_left} day(s) remaining until {target_date_str}.",
                                "reason": "Progress pace is lagging behind the remaining time until target date.",
                                "benefits": ["Prioritizing this milestone avoids deadline slippage."],
                                "risks": ["Goal will fall short without immediate acceleration."],
                                "action": "Review milestone in Profile & Goals.",
                                "action_route": "/profile",
                                "action_label": "Profile & Goals",
                                "evidence": {
                                    "goal_name": goal_name,
                                    "progress_pct": round(pct, 1),
                                    "target_date": target_date_str,
                                    "days_remaining": days_left,
                                },
                                "created_at": None,
                            })
                    except Exception:
                        pass
    except Exception as e:
        logger.warning("Error evaluating goal suggestions: %s", e)

    # De-duplicate by ID while preserving order
    seen_ids = set()
    unique_suggestions = []
    for s in suggestions:
        if s["id"] not in seen_ids:
            seen_ids.add(s["id"])
            unique_suggestions.append(s)

    # Priority rank sort
    priority_rank = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    unique_suggestions.sort(key=lambda s: priority_rank.get(s["priority"], 99))

    priority_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for s in unique_suggestions:
        p = s["priority"]
        if p in priority_counts:
            priority_counts[p] += 1

    categories = sorted(list(set(s["category"] for s in unique_suggestions)))

    # Missing data detection for calibration
    missing_data = []
    if study_df is None or study_df.empty:
        missing_data.append("Study Activities")
    if finance_df is None or finance_df.empty:
        missing_data.append("Financial Transactions")
    if (habits_df is None or habits_df.empty) and (fitness_df is None or fitness_df.empty):
        missing_data.append("Habits & Routines")
    if not goals:
        missing_data.append("Personal Goals")

    has_data = len(unique_suggestions) > 0
    is_calibrated = has_data

    message = (
        f"Generated {len(unique_suggestions)} real-time recommendation(s) based on your active Digital Twin data."
        if has_data
        else "Your Twin is still learning. Keep logging activities across your workspace to unlock personalized recommendations."
    )

    unlock_actions = [
        {"title": "Log Study Session", "description": "Record subject hours and quiz scores", "route": "/study", "label": "Go to Study"},
        {"title": "Schedule Daily Tasks", "description": "Organize your daily routine and focus blocks", "route": "/tasks", "label": "Go to Planner"},
        {"title": "Define Personal Goals", "description": "Set targets for savings, GPA, or fitness", "route": "/profile", "label": "Go to Goals"},
    ]

    return {
        "has_data": has_data,
        "total_count": len(unique_suggestions),
        "categories": categories,
        "priority_counts": priority_counts,
        "suggestions": unique_suggestions,
        "calibration_state": {
            "is_calibrated": is_calibrated,
            "message": message,
            "missing_data": missing_data,
            "unlock_actions": unlock_actions,
        },
    }


# --------------------------------------------------------------------------- #
# Dashboard Summary Endpoint
# --------------------------------------------------------------------------- #
@app.get("/api/dashboard/summary")
def get_dashboard_summary(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]

    # 1. Fetch domain states from database
    fin_summary = db.get_user_financial_summary(user_id)
    study_summary = db.get_user_study_summary(user_id)
    habit_summary = db.get_user_habit_summary(user_id)
    goals_df = db.get_goals(user_id)
    history_df, projected_1yr, monthly_rate = db.get_savings_forecast(user_id)
    weekly_study_df = db.get_weekly_study_hours(user_id)
    peak_focus = db.get_peak_focus_time(user_id)
    recs_df = db.get_recommendations(user_id, limit=3)
    fitness_df = db.get_fitness_records(user_id)

    # 2. Derive Health & Vitality Score (0-100)
    # Uses deterministic simulation formula based on real exercise, steps, sleep and habit completion
    freq = int(habit_summary.get("exercise_frequency", 3) or 3)
    steps = float(habit_summary.get("avg_steps", 0) or (6500 if not fitness_df.empty else 5000))
    sleep = float(habit_summary.get("avg_sleep_hours", 0) or (7.2 if not fitness_df.empty else 7.0))
    comp_rate = float(habit_summary.get("avg_completion_rate", 0) or 0)
    has_fitness_data = not fitness_df.empty or comp_rate > 0
    if has_fitness_data:
        vitality_score = _compute_fitness_score(freq, steps, sleep, comp_rate)
    else:
        # Initial calibration baseline when no records exist yet
        vitality_score = 75.0

    # 3. Derive Cognitive Focus Score (0-100)
    avg_study_score = float(study_summary.get("avg_performance_score", 0) or 0)
    if avg_study_score > 0:
        cognitive_score = round(avg_study_score, 1)
    else:
        cognitive_score = 78.0  # Baseline indicator

    # 4. Compute Goals structure
    goals_list = []
    goal_percentages = []
    if not goals_df.empty:
        for _, g in goals_df.iterrows():
            target = float(g.get("target_amount") or 0)
            curr = float(g.get("current_progress") or 0)
            pct = round((curr / target * 100) if target > 0 else 0, 1)
            goal_percentages.append(pct)
            goals_list.append(
                {
                    "goal_id": int(g["goal_id"]),
                    "goal_name": g["goal_name"],
                    "target_amount": target,
                    "current_progress": curr,
                    "target_date": str(g.get("target_date") or ""),
                    "progress_pct": min(pct, 100.0),
                }
            )
    avg_goal_progress = (
        round(sum(goal_percentages) / len(goal_percentages), 1)
        if goal_percentages
        else 0.0
    )

    # 5. Build Savings Trend Time-Series
    trend_series = []
    if not history_df.empty:
        for _, r in history_df.iterrows():
            trend_series.append(
                {
                    "date": str(r["date"]),
                    "cumulative_savings": float(r.get("cumulative_savings", 0)),
                }
            )

    # 6. Build Weekly Study Hours Distribution
    study_series = []
    total_weekly_hours = 0.0
    if not weekly_study_df.empty:
        for _, r in weekly_study_df.iterrows():
            hrs = float(r.get("hours", 0))
            total_weekly_hours += hrs
            study_series.append({"day": str(r["day"]), "hours": hrs})
    else:
        for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            study_series.append({"day": d, "hours": 0.0})

    # 7. Curated Twin Insights
    twin_insights = []
    if not recs_df.empty:
        for _, r in recs_df.iterrows():
            twin_insights.append(
                {
                    "category": r.get("category", "Intelligence"),
                    "priority": r.get("priority", "medium"),
                    "text": r.get("recommendation_text") or r.get("reason") or "",
                    "action": r.get("next_action") or "",
                }
            )
    if not twin_insights:
        twin_insights = [
            {
                "category": "Calibration",
                "priority": "normal",
                "text": "Your Digital Twin model is calibrated and ready. Log daily activities to refine predictive accuracy.",
                "action": "Add financial or study records to begin simulation modeling.",
            }
        ]

    # 8. Sleep KPI derivation
    current_sleep = sleep if sleep > 0 else 7.5

    has_finance_data = (
        float(fin_summary.get("total_savings", 0.0) or 0) != 0.0
        or float(fin_summary.get("monthly_income", 0.0) or 0) > 0.0
        or float(fin_summary.get("monthly_expenses", 0.0) or 0) > 0.0
    )
    has_study_data = total_weekly_hours > 0 or avg_study_score > 0
    has_sleep_data = bool(not fitness_df.empty or comp_rate > 0)

    return {
        "user": {
            "name": current_user["name"],
            "occupation": current_user.get("occupation") or "Twin User",
            "age": current_user.get("age") or 25,
            "days_active": db.get_days_active(user_id),
        },
        "kpis": {
            "health_vitality": {
                "score": round(vitality_score, 1) if has_fitness_data else None,
                "max": 100,
                "level": "Optimal" if vitality_score >= 80 else ("Good" if vitality_score >= 65 else "Developing"),
                "has_real_data": has_fitness_data,
            },
            "cognitive_focus": {
                "score": round(cognitive_score, 1) if avg_study_score > 0 else None,
                "max": 100,
                "level": "Peak" if cognitive_score >= 85 else ("Steady" if cognitive_score >= 70 else "Growing"),
                "has_real_data": avg_study_score > 0,
            },
            "saved_money": {
                "total_savings": float(fin_summary.get("total_savings", 0.0) or 0),
                "monthly_income": float(fin_summary.get("monthly_income", 0.0) or 0),
                "monthly_expenses": float(fin_summary.get("monthly_expenses", 0.0) or 0),
                "monthly_savings": float(fin_summary.get("monthly_savings", 0.0) or 0),
                "projected_1yr": float(projected_1yr),
                "monthly_rate": float(monthly_rate),
                "has_real_data": has_finance_data,
            },
            "sleep": {
                "avg_hours": round(current_sleep, 1) if has_sleep_data else None,
                "status": ("Healthy Range" if 7.0 <= current_sleep <= 9.0 else "Needs Optimization") if has_sleep_data else "No Data Logged",
                "has_real_data": has_sleep_data,
            },
            "weekly_study": {
                "total_hours": round(total_weekly_hours, 1),
                "peak_focus": peak_focus if has_study_data else "Not enough data",
                "has_real_data": has_study_data,
            },
            "goal_progress": {
                "average_pct": avg_goal_progress,
                "count": len(goals_list),
                "has_real_data": len(goals_list) > 0,
            },
        },
        "goals": goals_list,
        "savings_trend": trend_series,
        "study_distribution": study_series,
        "twin_insights": twin_insights,
    }


# --------------------------------------------------------------------------- #
# Wealth & Finance Endpoints
# --------------------------------------------------------------------------- #
SUPPORTED_FINANCIAL_CATEGORIES = [
    "Housing",
    "Food",
    "Dining Out",
    "Transport",
    "Salary",
    "Investment",
    "Entertainment",
    "Healthcare",
    "Education",
    "Bills",
    "Other",
]
SUPPORTED_TRANSACTION_TYPES = ["Income", "Expense", "Savings"]


@app.get("/api/wealth", response_model=WealthOverviewResponse)
def get_wealth_overview(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    fin = db.get_financial_records(user_id)

    if fin.empty:
        summary = FinancialSummary(
            total_income=None,
            total_expenses=None,
            net_cash_flow=None,
            total_savings=None,
            monthly_rate=None,
            savings_rate_pct=None,
            transaction_count=0,
            months_active=0,
        )
        spending_data = SpendingAnalysisData(
            total_spent=0.0,
            top_category=None,
            top_category_amount=None,
            category_wise=[],
            monthly=[],
        )
        savings_data = SavingsTrendData(
            history=[],
            forecast_1yr=0.0,
            monthly_rate=0.0,
        )
        budget_data = BudgetRecommendationData(
            has_budget=False,
            monthly_budget=None,
            weekly_budget=None,
            emergency_fund=None,
            savings_goal=None,
            basis="Log income and expenses to unlock budget recommendations.",
            category_limits=[],
        )
        return WealthOverviewResponse(
            has_data=False,
            summary=summary,
            transactions=[],
            spending_analysis=spending_data,
            savings_trend=savings_data,
            budget_recommendation=budget_data,
            supported_categories=SUPPORTED_FINANCIAL_CATEGORIES,
            supported_types=SUPPORTED_TRANSACTION_TYPES,
        )

    # 1. Summary calculations
    fin_date = pd.to_datetime(fin["date"])
    months_active = max(fin_date.dt.to_period("M").nunique(), 1)

    income_df = fin[fin["transaction_type"] == "Income"]
    total_income = float(income_df["amount"].sum()) if not income_df.empty else 0.0

    expense_df = fin[fin["transaction_type"] == "Expense"]
    total_expenses = float(expense_df["amount"].sum()) if not expense_df.empty else 0.0

    net_series = fin.apply(
        lambda r: r["amount"] if r["transaction_type"] in ("Income", "Savings") else -r["amount"],
        axis=1,
    )
    net_cash_flow = round(float(net_series.sum()), 2)

    fin_summary = db.get_user_financial_summary(user_id)
    history, projected_1yr, monthly_rate = db.get_savings_forecast(user_id)

    monthly_inc = float(fin_summary.get("monthly_income", 0.0) or 0.0)
    monthly_sav = float(fin_summary.get("monthly_savings", 0.0) or 0.0)
    savings_rate_pct = round((monthly_sav / monthly_inc) * 100, 1) if monthly_inc > 0 else 0.0
    tot_savings = float(fin_summary.get("total_savings", 0.0) or 0.0)

    summary = FinancialSummary(
        total_income=round(total_income, 2),
        total_expenses=round(total_expenses, 2),
        net_cash_flow=net_cash_flow,
        total_savings=round(tot_savings, 2),
        monthly_rate=round(float(monthly_rate), 2),
        savings_rate_pct=savings_rate_pct,
        transaction_count=len(fin),
        months_active=months_active,
    )

    # 2. Spending Analysis via AI Core
    spending = fin_ai.spending_analysis(fin)
    total_spent = round(float(spending.get("total_spent", 0.0)), 2)
    by_cat: list[SpendingCategoryPoint] = []
    cat_df = spending.get("category_wise")
    if cat_df is not None and not cat_df.empty:
        for _, r in cat_df.iterrows():
            amt = round(float(r["spent"]), 2)
            pct = round((amt / total_spent) * 100, 1) if total_spent > 0 else 0.0
            by_cat.append(SpendingCategoryPoint(category=str(r["category"]), spent=amt, percentage=pct))

    monthly_pts: list[SpendingMonthlyPoint] = []
    mon_df = spending.get("monthly")
    if mon_df is not None and not mon_df.empty:
        for _, r in mon_df.iterrows():
            try:
                m_label = pd.Period(str(r["month"])).strftime("%b %Y")
            except Exception:
                m_label = str(r["month"])
            monthly_pts.append(SpendingMonthlyPoint(month=m_label, spent=round(float(r["spent"]), 2)))

    top_cat = by_cat[0].category if by_cat else None
    top_cat_amt = by_cat[0].spent if by_cat else None

    spending_data = SpendingAnalysisData(
        total_spent=total_spent,
        top_category=top_cat,
        top_category_amount=top_cat_amt,
        category_wise=by_cat,
        monthly=monthly_pts,
    )

    # 3. Savings Trend
    trend_pts: list[SavingsTrendPoint] = []
    if not history.empty:
        for _, r in history.iterrows():
            d_val = r["date"]
            d_str = d_val.strftime("%Y-%m-%d") if hasattr(d_val, "strftime") else str(d_val)[:10]
            trend_pts.append(
                SavingsTrendPoint(date=d_str, cumulative_savings=round(float(r["cumulative_savings"]), 2))
            )
    savings_data = SavingsTrendData(
        history=trend_pts,
        forecast_1yr=round(float(projected_1yr), 2),
        monthly_rate=round(float(monthly_rate), 2),
    )

    # 4. Budget Recommendation via AI Core
    budget_res = fin_ai.recommend_budget(fin)
    cat_lims: list[BudgetCategoryLimit] = []
    lim_df = budget_res.get("category_limits")
    if lim_df is not None and not lim_df.empty:
        for _, r in lim_df.iterrows():
            cat_lims.append(BudgetCategoryLimit(category=str(r["category"]), limit=round(float(r["limit"]), 2)))

    m_budget = float(budget_res.get("monthly_budget", 0.0) or 0.0)
    w_budget = float(budget_res.get("weekly_budget", 0.0) or 0.0)
    e_fund = float(budget_res.get("emergency_fund", 0.0) or 0.0)
    s_goal = float(budget_res.get("savings_goal", 0.0) or 0.0)
    has_b = m_budget > 0 or w_budget > 0

    budget_data = BudgetRecommendationData(
        has_budget=has_b,
        monthly_budget=round(m_budget, 2) if has_b else None,
        weekly_budget=round(w_budget, 2) if has_b else None,
        emergency_fund=round(e_fund, 2) if has_b else None,
        savings_goal=round(s_goal, 2) if has_b else None,
        basis=str(budget_res.get("basis", "")),
        category_limits=cat_lims,
    )

    # 5. Transactions List
    tx_list: list[TransactionItem] = []
    for _, r in fin.iterrows():
        d_val = r["date"]
        d_str = d_val.strftime("%Y-%m-%d") if hasattr(d_val, "strftime") else str(d_val)[:10]
        tx_list.append(
            TransactionItem(
                record_id=int(r["record_id"]),
                user_id=int(r["user_id"]),
                category=str(r["category"]),
                amount=round(float(r["amount"]), 2),
                transaction_type=str(r["transaction_type"]),
                date=d_str,
            )
        )

    return WealthOverviewResponse(
        has_data=True,
        summary=summary,
        transactions=tx_list,
        spending_analysis=spending_data,
        savings_trend=savings_data,
        budget_recommendation=budget_data,
        supported_categories=SUPPORTED_FINANCIAL_CATEGORIES,
        supported_types=SUPPORTED_TRANSACTION_TYPES,
    )


@app.post("/api/wealth/transactions", status_code=status.HTTP_201_CREATED, response_model=TransactionItem)
def create_transaction_endpoint(
    req: TransactionCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    if req.date:
        try:
            tx_date = date.fromisoformat(str(req.date))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid date format. Expected YYYY-MM-DD.",
            )
    else:
        tx_date = date.today()

    record_id = db.add_financial_record(
        user_id=user_id,
        category=req.category.strip(),
        amount=float(req.amount),
        transaction_type=req.transaction_type,
        date_=tx_date,
    )
    if not record_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record transaction in database.",
        )
    return TransactionItem(
        record_id=record_id,
        user_id=user_id,
        category=req.category.strip(),
        amount=round(float(req.amount), 2),
        transaction_type=req.transaction_type,
        date=tx_date.isoformat(),
    )


@app.put("/api/wealth/transactions/{record_id}", response_model=TransactionItem)
def update_transaction_endpoint(
    record_id: int,
    req: TransactionUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    update_fields: dict[str, Any] = {}
    if req.category is not None:
        update_fields["category"] = req.category.strip()
    if req.amount is not None:
        update_fields["amount"] = float(req.amount)
    if req.transaction_type is not None:
        update_fields["transaction_type"] = req.transaction_type
    if req.date is not None:
        try:
            update_fields["date"] = date.fromisoformat(str(req.date))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid date format. Expected YYYY-MM-DD.",
            )

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update.",
        )

    updated = db.update_financial_record(record_id, user_id=user_id, **update_fields)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found or not owned by the current user.",
        )

    records = db.get_financial_records(user_id)
    matched = records[records["record_id"] == record_id]
    if matched.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction record could not be retrieved after update.",
        )
    row = matched.iloc[0]
    d_val = row["date"]
    d_str = d_val.strftime("%Y-%m-%d") if hasattr(d_val, "strftime") else str(d_val)[:10]
    return TransactionItem(
        record_id=int(row["record_id"]),
        user_id=int(row["user_id"]),
        category=str(row["category"]),
        amount=round(float(row["amount"]), 2),
        transaction_type=str(row["transaction_type"]),
        date=d_str,
    )


@app.delete("/api/wealth/transactions/{record_id}")
def delete_transaction_endpoint(
    record_id: int,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    deleted = db.delete_financial_record(record_id, user_id=user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found or not owned by current user.",
        )
    return {"message": "Transaction deleted successfully", "record_id": record_id}


@app.post("/api/wealth/classify", response_model=ExpenseClassifyResponse)
def classify_expense_endpoint(
    req: ExpenseClassifyRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    desc = req.description.strip()
    if not desc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expense description must not be empty.",
        )
    try:
        result = fin_ai.classify_expense(desc)
        cat = result.get("category", "Other")
        conf = float(result.get("confidence", 0.0))
        try:
            db.log_finance_prediction(
                user_id=user_id,
                prediction_type="expense_classification",
                result_value=None,
                result_category=cat,
                confidence=conf,
                input_data={"description": desc},
                output_data=result,
            )
        except Exception as log_err:
            logger.debug(f"Failed to log expense classification: {log_err}")

        return ExpenseClassifyResponse(
            description=desc,
            category=cat,
            confidence=round(conf, 3),
            is_prediction=True,
        )
    except Exception as e:
        logger.error(f"Expense classification error: {e}", exc_info=True)
        return ExpenseClassifyResponse(
            description=desc,
            category="Other",
            confidence=0.0,
            is_prediction=False,
        )


@app.post("/api/wealth/forecast", response_model=ForecastSimulateResponse)
def simulate_forecast_endpoint(
    req: ForecastSimulateRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    history, projected_1yr, monthly_rate = db.get_savings_forecast(user_id)

    extra = float(req.extra_monthly_savings)
    effective_rate = float(monthly_rate) + extra

    if history.empty:
        last_val = 0.0
        start_date = date.today()
    else:
        last_date_val = history["date"].iloc[-1]
        start_date = last_date_val.date() if hasattr(last_date_val, "date") else pd.to_datetime(last_date_val).date()
        last_val = float(history["cumulative_savings"].iloc[-1])

    timeline: list[ForecastTimelinePoint] = []
    for m in range(1, req.horizon_months + 1):
        future_date = (start_date + datetime.timedelta(days=30 * m)).isoformat()
        val = round(last_val + effective_rate * m, 2)
        timeline.append(ForecastTimelinePoint(month=m, date=future_date, projected_savings=val))

    final_savings = timeline[-1].projected_savings if timeline else last_val

    try:
        db.log_finance_prediction(
            user_id=user_id,
            prediction_type="savings_projection_simulation",
            result_value=final_savings,
            result_category=f"{req.horizon_months}-month forecast",
            input_data={"horizon_months": req.horizon_months, "extra_monthly_savings": extra},
            output_data={"projected_final_savings": final_savings, "effective_rate": effective_rate},
        )
    except Exception as log_err:
        logger.debug(f"Failed to log savings simulation: {log_err}")

    return ForecastSimulateResponse(
        current_savings=round(last_val, 2),
        baseline_monthly_rate=round(float(monthly_rate), 2),
        effective_monthly_rate=round(effective_rate, 2),
        horizon_months=req.horizon_months,
        projected_final_savings=round(final_savings, 2),
        projected_timeline=timeline,
    )


# --------------------------------------------------------------------------- #
# Analytics Endpoints
# --------------------------------------------------------------------------- #
@app.get("/api/analytics", response_model=AnalyticsResponse)
def get_analytics(
    range: str = Query(default="30D", pattern="^(7D|30D|90D|1Y)$"),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    today = date.today()
    range_days = {"7D": 7, "30D": 30, "90D": 90, "1Y": 365}.get(range, 30)
    start_date = today - datetime.timedelta(days=range_days)
    start_date_str = start_date.isoformat()
    today_str = today.isoformat()

    # 1. Fetch data from DB
    sched_df = db.get_schedule_history(user_id)
    study_df = db.get_study_activities(user_id)
    fin_df = db.get_financial_records(user_id)
    habits_df = db.get_habits(user_id)
    fitness_df = db.get_fitness_records(user_id)
    goals_df = db.get_goals(user_id)

    # 2. Productivity / Tasks in Range
    if not sched_df.empty:
        sched_df["date_dt"] = pd.to_datetime(sched_df["date"]).dt.date
        sched_filtered = sched_df[
            (sched_df["date_dt"] >= start_date) & (sched_df["date_dt"] <= today)
        ]
    else:
        sched_filtered = pd.DataFrame()

    if not sched_filtered.empty:
        tasks_total = len(sched_filtered)
        done_mask = sched_filtered["status"].astype(str).str.lower().isin(["done", "completed"])
        tasks_completed = int(done_mask.sum())
        productivity_score = round((tasks_completed / tasks_total) * 100, 1) if tasks_total > 0 else 0.0

        grouped_sched = sched_filtered.groupby("date_dt")
        prod_series = []
        for d_key, grp in sorted(grouped_sched, key=lambda x: x[0]):
            d_tot = len(grp)
            d_done = int(grp["status"].astype(str).str.lower().isin(["done", "completed"]).sum())
            d_rate = round((d_done / d_tot) * 100, 1) if d_tot > 0 else 0.0
            prod_series.append(
                ProductivityPoint(
                    date=d_key.isoformat(),
                    completed=d_done,
                    total=d_tot,
                    completion_rate=d_rate,
                )
            )
        prod_trend = ProductivityTrendData(has_data=len(prod_series) > 0, series=prod_series)
    else:
        productivity_score = None
        tasks_completed = 0
        tasks_total = 0
        prod_trend = ProductivityTrendData(has_data=False, series=[])

    # 3. Study Analytics in Range
    if not study_df.empty:
        study_df["date_dt"] = pd.to_datetime(study_df["date"]).dt.date
        study_filtered = study_df[
            (study_df["date_dt"] >= start_date) & (study_df["date_dt"] <= today)
        ]
    else:
        study_filtered = pd.DataFrame()

    if not study_filtered.empty:
        study_hours_val = round(float(study_filtered["hours_logged"].sum()), 1)
        sessions_count = len(study_filtered)
        scored = study_filtered.dropna(subset=["performance_score"])
        avg_study_score_val = (
            round(float(scored["performance_score"].mean()), 1) if not scored.empty else None
        )
        peak_focus_time = db.get_peak_focus_time(user_id)

        study_daily = []
        for d_key, grp in sorted(study_filtered.groupby("date_dt"), key=lambda x: x[0]):
            d_hrs = round(float(grp["hours_logged"].sum()), 1)
            sc = grp.dropna(subset=["performance_score"])
            sc_mean = round(float(sc["performance_score"].mean()), 1) if not sc.empty else None
            study_daily.append(StudyDailyPoint(date=d_key.isoformat(), hours=d_hrs, avg_score=sc_mean))

        subj_breakdown = []
        for subj_name, grp in study_filtered.groupby("subject"):
            s_hrs = round(float(grp["hours_logged"].sum()), 1)
            pct = round((s_hrs / study_hours_val) * 100, 1) if study_hours_val > 0 else 0.0
            sc = grp.dropna(subset=["performance_score"])
            sc_mean = round(float(sc["performance_score"].mean()), 1) if not sc.empty else None
            subj_breakdown.append(
                StudySubjectPoint(
                    subject=str(subj_name),
                    hours=s_hrs,
                    percentage=pct,
                    avg_score=sc_mean,
                )
            )
        subj_breakdown.sort(key=lambda x: x.hours, reverse=True)

        study_analytics = StudyAnalyticsData(
            has_data=True,
            total_hours=study_hours_val,
            sessions_count=sessions_count,
            avg_performance_score=avg_study_score_val,
            peak_focus_time=peak_focus_time,
            daily_trend=study_daily,
            subject_breakdown=subj_breakdown,
        )
    else:
        study_hours_val = None
        avg_study_score_val = None
        study_analytics = StudyAnalyticsData(
            has_data=False,
            total_hours=0.0,
            sessions_count=0,
            avg_performance_score=None,
            peak_focus_time="No schedule data",
            daily_trend=[],
            subject_breakdown=[],
        )

    # 4. Financial Analytics in Range
    if not fin_df.empty:
        fin_df["date_dt"] = pd.to_datetime(fin_df["date"]).dt.date
        fin_filtered = fin_df[(fin_df["date_dt"] >= start_date) & (fin_df["date_dt"] <= today)]
    else:
        fin_filtered = pd.DataFrame()

    fin_summary = db.get_user_financial_summary(user_id)
    total_savings_val = (
        float(fin_summary.get("total_savings", 0.0) or 0.0) if not fin_df.empty else None
    )

    if not fin_filtered.empty:
        income_sum = round(
            float(fin_filtered[fin_filtered["transaction_type"] == "Income"]["amount"].sum()), 2
        )
        expense_sum = round(
            float(fin_filtered[fin_filtered["transaction_type"] == "Expense"]["amount"].sum()), 2
        )
        net_flow_val = round(income_sum - expense_sum, 2)

        spending_cats = []
        exp_df = fin_filtered[fin_filtered["transaction_type"] == "Expense"]
        if not exp_df.empty:
            for cat, grp in exp_df.groupby("category"):
                amt = round(float(grp["amount"].sum()), 2)
                pct = round((amt / expense_sum) * 100, 1) if expense_sum > 0 else 0.0
                spending_cats.append(
                    SpendingCategoryPoint(category=str(cat), spent=amt, percentage=pct)
                )
            spending_cats.sort(key=lambda x: x.spent, reverse=True)

        cashflow_trend = []
        if range_days <= 14:
            for d_key, grp in sorted(fin_filtered.groupby("date_dt"), key=lambda x: x[0]):
                inc = float(grp[grp["transaction_type"] == "Income"]["amount"].sum())
                exp = float(grp[grp["transaction_type"] == "Expense"]["amount"].sum())
                cashflow_trend.append(
                    FinancialCashflowPoint(
                        period=d_key.strftime("%b %d"),
                        income=round(inc, 2),
                        expenses=round(exp, 2),
                        net=round(inc - exp, 2),
                    )
                )
        elif range_days <= 90:
            fin_filtered_copy = fin_filtered.copy()
            fin_filtered_copy["period"] = pd.to_datetime(fin_filtered_copy["date_dt"]).dt.to_period("W")
            for p_key, grp in sorted(fin_filtered_copy.groupby("period"), key=lambda x: str(x[0])):
                inc = float(grp[grp["transaction_type"] == "Income"]["amount"].sum())
                exp = float(grp[grp["transaction_type"] == "Expense"]["amount"].sum())
                min_date = grp["date_dt"].min()
                cashflow_trend.append(
                    FinancialCashflowPoint(
                        period=f"Wk of {min_date.strftime('%b %d')}",
                        income=round(inc, 2),
                        expenses=round(exp, 2),
                        net=round(inc - exp, 2),
                    )
                )
        else:
            fin_filtered_copy = fin_filtered.copy()
            fin_filtered_copy["period"] = pd.to_datetime(fin_filtered_copy["date_dt"]).dt.to_period("M")
            for p_key, grp in sorted(fin_filtered_copy.groupby("period"), key=lambda x: str(x[0])):
                inc = float(grp[grp["transaction_type"] == "Income"]["amount"].sum())
                exp = float(grp[grp["transaction_type"] == "Expense"]["amount"].sum())
                cashflow_trend.append(
                    FinancialCashflowPoint(
                        period=p_key.strftime("%b %Y"),
                        income=round(inc, 2),
                        expenses=round(exp, 2),
                        net=round(inc - exp, 2),
                    )
                )

        fin_analytics = FinancialAnalyticsData(
            has_data=True,
            total_income=income_sum,
            total_expenses=expense_sum,
            net_savings=net_flow_val,
            spending_by_category=spending_cats,
            cashflow_trend=cashflow_trend,
        )
    else:
        income_sum = None
        expense_sum = None
        net_flow_val = None
        fin_analytics = FinancialAnalyticsData(
            has_data=False,
            total_income=0.0,
            total_expenses=0.0,
            net_savings=0.0,
            spending_by_category=[],
            cashflow_trend=[],
        )

    # 5. Habit & Lifestyle Analytics
    habit_points = []
    overall_consistency = None
    if not habits_df.empty:
        habits_df["completion_rate"] = pd.to_numeric(habits_df["completion_rate"], errors="coerce")
        overall_consistency = round(float(habits_df["completion_rate"].mean()), 1)
        habit_names = db.get_habit_names(user_id) or []
        for hname in habit_names:
            pred = db.get_habit_prediction_by_name(user_id, hname)
            habit_points.append(
                HabitMetricPoint(
                    habit_name=hname,
                    rate=float(pred["rate"]),
                    trend_pct=float(pred["trend_pct"]),
                    insight=str(pred["insight"]),
                )
            )

    sleep_activity_trend = []
    avg_sleep_val = None
    if not fitness_df.empty:
        fitness_df["date_dt"] = pd.to_datetime(fitness_df["date"]).dt.date
        fit_filtered = fitness_df[
            (fitness_df["date_dt"] >= start_date) & (fitness_df["date_dt"] <= today)
        ]
        if not fit_filtered.empty:
            for d_key, grp in sorted(fit_filtered.groupby("date_dt"), key=lambda x: x[0]):
                slp = (
                    float(grp["sleep_hours"].mean())
                    if "sleep_hours" in grp.columns and pd.notna(grp["sleep_hours"].mean())
                    else None
                )
                stps = (
                    float(grp["steps"].mean())
                    if "steps" in grp.columns and pd.notna(grp["steps"].mean())
                    else None
                )
                ex = (
                    float(grp["exercise_minutes"].mean())
                    if "exercise_minutes" in grp.columns and pd.notna(grp["exercise_minutes"].mean())
                    else None
                )
                sleep_activity_trend.append(
                    SleepActivityPoint(
                        date=d_key.isoformat(),
                        sleep_hours=round(slp, 1) if slp is not None else None,
                        steps=round(stps, 0) if stps is not None else None,
                        exercise_minutes=round(ex, 1) if ex is not None else None,
                    )
                )
            if "sleep_hours" in fit_filtered.columns and not fit_filtered["sleep_hours"].dropna().empty:
                avg_sleep_val = round(float(fit_filtered["sleep_hours"].mean()), 1)

    has_habits_or_fit = len(habit_points) > 0 or len(sleep_activity_trend) > 0
    habit_lifestyle_analytics = HabitLifestyleAnalyticsData(
        has_data=has_habits_or_fit,
        overall_consistency=overall_consistency,
        habits=habit_points,
        sleep_activity_trend=sleep_activity_trend,
    )

    # 6. Goals Progress
    if not goals_df.empty:
        goal_points = []
        goal_pcts = []
        for _, g in goals_df.iterrows():
            tgt = float(g.get("target_amount") or 0)
            curr = float(g.get("current_progress") or 0)
            pct = round((curr / tgt * 100) if tgt > 0 else 0, 1)
            goal_pcts.append(min(pct, 100.0))
            goal_points.append(
                GoalAnalyticsPoint(
                    goal_id=int(g["goal_id"]),
                    goal_name=str(g["goal_name"]),
                    target_amount=tgt,
                    current_progress=curr,
                    progress_pct=min(pct, 100.0),
                    target_date=str(g["target_date"]) if pd.notna(g.get("target_date")) else None,
                )
            )
        active_goals_count = len(goal_points)
        avg_goal_progress = round(sum(goal_pcts) / len(goal_pcts), 1) if goal_pcts else 0.0
        goals_analytics = GoalsAnalyticsData(has_data=True, goals=goal_points)
    else:
        active_goals_count = 0
        avg_goal_progress = None
        goals_analytics = GoalsAnalyticsData(has_data=False, goals=[])

    # 7. Grounded Twin Insights
    twin_insights = []
    if tasks_total > 0 and productivity_score is not None:
        if productivity_score >= 75:
            twin_insights.append(
                TwinInsight(
                    domain="productivity",
                    title="Strong Task Execution",
                    message=f"Completed {tasks_completed} of {tasks_total} scheduled items ({productivity_score}%) in this {range} window.",
                    type="positive",
                )
            )
        else:
            twin_insights.append(
                TwinInsight(
                    domain="productivity",
                    title="Task Completion Rate",
                    message=f"{tasks_completed} of {tasks_total} scheduled tasks completed ({productivity_score}%). Focus on prioritizing essential tasks first.",
                    type="attention",
                )
            )

    if study_hours_val is not None and study_hours_val > 0:
        twin_insights.append(
            TwinInsight(
                domain="study",
                title="Academic Engagement",
                message=f"Logged {study_hours_val} hours across {len(study_analytics.subject_breakdown)} subject(s) with an average performance score of {avg_study_score_val or '--'}/100.",
                type="positive" if (avg_study_score_val or 0) >= 70 else "neutral",
            )
        )

    if income_sum is not None and expense_sum is not None:
        if (net_flow_val or 0) >= 0:
            twin_insights.append(
                TwinInsight(
                    domain="finance",
                    title="Positive Net Cash Flow",
                    message=f"Net savings of ₹{net_flow_val:,.0f} over the last {range} (Income: ₹{income_sum:,.0f}, Expenses: ₹{expense_sum:,.0f}).",
                    type="positive",
                )
            )
        else:
            twin_insights.append(
                TwinInsight(
                    domain="finance",
                    title="Spending Outflow Deficit",
                    message=f"Expenses (₹{expense_sum:,.0f}) exceeded income (₹{income_sum:,.0f}) by ₹{abs(net_flow_val or 0):,.0f} during this {range} period.",
                    type="attention",
                )
            )

    if overall_consistency is not None:
        twin_insights.append(
            TwinInsight(
                domain="habits",
                title="Habit Consistency",
                message=f"Average habit completion rate stands at {overall_consistency}%.",
                type="positive" if overall_consistency >= 70 else "neutral",
            )
        )

    if active_goals_count > 0:
        twin_insights.append(
            TwinInsight(
                domain="goals",
                title="Goal Pacing",
                message=f"{active_goals_count} active target(s) progressing at an average of {avg_goal_progress}%.",
                type="neutral",
            )
        )

    if not twin_insights:
        twin_insights.append(
            TwinInsight(
                domain="general",
                title="Awaiting Activity Data",
                message=f"No activity records have been logged in the last {range}. As you record tasks, study sessions, and financial transactions, your Twin will automatically surface grounded analytical insights.",
                type="neutral",
            )
        )

    has_any_data = any(
        [
            prod_trend.has_data,
            study_analytics.has_data,
            fin_analytics.has_data,
            habit_lifestyle_analytics.has_data,
            goals_analytics.has_data,
        ]
    )

    overview_metrics = AnalyticsOverviewMetrics(
        productivity_score=productivity_score,
        tasks_completed=tasks_completed,
        tasks_total=tasks_total,
        study_hours=study_hours_val,
        avg_study_score=avg_study_score_val,
        net_cash_flow=net_flow_val,
        total_savings=total_savings_val,
        habit_consistency=overall_consistency,
        avg_sleep_hours=avg_sleep_val,
        active_goals_count=active_goals_count,
        avg_goal_progress=avg_goal_progress,
    )

    return AnalyticsResponse(
        range=range,
        start_date=start_date_str,
        end_date=today_str,
        has_data=has_any_data,
        overview_metrics=overview_metrics,
        productivity_trend=prod_trend,
        study_analytics=study_analytics,
        financial_analytics=fin_analytics,
        habit_lifestyle_analytics=habit_lifestyle_analytics,
        goals_progress=goals_analytics,
        twin_insights=twin_insights,
    )


# --------------------------------------------------------------------------- #
# Conversational AI Endpoints
# --------------------------------------------------------------------------- #
@app.get("/api/chat/status")
def get_chat_status(current_user: dict = Depends(get_current_user)):
    try:
        cfg = get_llm_config()
        provider = cfg.provider
        model = cfg.model
        has_key = has_valid_api_key(cfg) if provider == "gemini" else True
    except Exception:
        provider = "rule_based"
        model = "deterministic-fallback"
        has_key = True

    return {
        "provider": provider,
        "model": model,
        "has_api_key": has_key,
        "suggested_questions": templates.SUGGESTED_QUESTIONS,
        "greeting": templates.DEFAULT_GREETING,
    }


@app.post("/api/chat/ask")
def chat_ask_endpoint(req: ChatAskRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    try:
        service = ConversationService(user_id)
        turn = service.answer(req.message.strip())
        return {
            "question": turn.question,
            "answer": turn.answer,
            "provider": turn.provider,
            "model": turn.model,
            "grounded": turn.grounded,
        }
    except ConversationError as ce:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ce))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversational engine error: {str(e)}",
        )


# --------------------------------------------------------------------------- #
# Milestone 3 — What-If Simulation Endpoints
# --------------------------------------------------------------------------- #
@app.get("/api/simulation/baseline", response_model=SimulationBaselineResponse)
def get_simulation_baseline_endpoint(current_user: dict = Depends(get_current_user)):
    """Retrieve the user's real baseline metrics for Financial, Study, and Habit domains."""
    user_id = current_user["user_id"]

    # Financial baseline
    fin = db.get_user_financial_summary(user_id)
    raw_goals = db.get_user_goals(user_id)
    goals = [
        FinancialGoalItem(
            goal_id=int(g["goal_id"]),
            goal_name=str(g["goal_name"]),
            target_amount=float(g["target_amount"]),
            current_progress=float(g["current_progress"]),
            target_date=str(g.get("target_date", "")) if g.get("target_date") else None,
        )
        for g in raw_goals
    ]
    fin_has_data = (
        float(fin.get("monthly_income", 0)) > 0
        or float(fin.get("monthly_expenses", 0)) > 0
        or float(fin.get("total_savings", 0)) != 0
    )
    financial_baseline = SimulationBaselineFinancial(
        has_data=fin_has_data,
        monthly_income=float(fin.get("monthly_income", 0.0)),
        monthly_expenses=float(fin.get("monthly_expenses", 0.0)),
        monthly_savings=float(fin.get("monthly_savings", 0.0)),
        total_savings=float(fin.get("total_savings", 0.0)),
        goals=goals,
    )

    # Study baseline
    study = db.get_user_study_summary(user_id)
    study_has_data = (
        float(study.get("avg_hours_per_day", 0)) > 0
        or int(study.get("days_active", 0)) > 0
        or len(study.get("subjects", [])) > 0
    )
    study_baseline = SimulationBaselineStudy(
        has_data=study_has_data,
        avg_hours_per_day=float(study.get("avg_hours_per_day", 0.0)),
        avg_performance_score=float(study.get("avg_performance_score", 0.0)),
        subjects=[str(s) for s in study.get("subjects", [])],
        days_active=int(study.get("days_active", 0)),
    )

    # Habits baseline
    habits = db.get_user_habit_summary(user_id)
    habits_has_data = (
        float(habits.get("avg_completion_rate", 0)) > 0
        or float(habits.get("avg_steps", 0)) > 0
        or len(habits.get("habit_names", [])) > 0
    )
    habits_baseline = SimulationBaselineHabits(
        has_data=habits_has_data,
        avg_completion_rate=float(habits.get("avg_completion_rate", 0.0)),
        exercise_frequency=int(habits.get("exercise_frequency", 3)),
        avg_steps=float(habits.get("avg_steps", 0.0)),
        avg_sleep_hours=float(habits.get("avg_sleep_hours", 0.0)),
        avg_exercise_minutes=float(habits.get("avg_exercise_minutes", 0.0)),
        habit_names=[str(h) for h in habits.get("habit_names", [])],
    )

    return SimulationBaselineResponse(
        financial=financial_baseline,
        study=study_baseline,
        habits=habits_baseline,
    )


@app.post("/api/simulation/run", response_model=RunSimulationResponse)
def run_simulation_endpoint(
    req: RunSimulationRequest,
    current_user: dict = Depends(get_current_user),
):
    """Execute deterministic scenario simulation across financial, study, or habits domains."""
    user_id = current_user["user_id"]
    domain = req.domain
    horizon = req.horizon_months

    # Prepare custom scenarios dicts if provided
    formatted_custom = None
    if req.custom_scenarios:
        formatted_custom = []
        for cs in req.custom_scenarios:
            item: dict[str, Any] = {"name": cs.name, "description": cs.description or ""}
            if domain == "finance":
                if cs.monthly_saving is not None:
                    item["monthly_saving"] = float(cs.monthly_saving)
                if cs.monthly_expenses is not None:
                    item["monthly_expenses"] = float(cs.monthly_expenses)
            elif domain == "study":
                if cs.hours_per_day is not None:
                    item["hours_per_day"] = float(cs.hours_per_day)
            elif domain == "habits":
                if cs.completion_rate is not None:
                    item["completion_rate"] = float(cs.completion_rate)
                if cs.exercise_frequency is not None:
                    item["exercise_frequency"] = int(cs.exercise_frequency)
            formatted_custom.append(item)

    # Gather user baseline data from PostgreSQL
    user_data: dict[str, Any] = {}
    assumptions: list[str] = []
    has_baseline_data = False

    if domain == "finance":
        fin_summary = db.get_user_financial_summary(user_id)
        goals = db.get_user_goals(user_id)
        user_data["financial"] = fin_summary
        user_data["goals"] = goals
        has_baseline_data = (
            float(fin_summary.get("monthly_income", 0)) > 0
            or float(fin_summary.get("monthly_expenses", 0)) > 0
            or float(fin_summary.get("total_savings", 0)) != 0
        )
        assumptions.append(
            f"Baseline is derived from recorded transactions: Monthly income \u20b9{fin_summary['monthly_income']:,.0f}, "
            f"expenses \u20b9{fin_summary['monthly_expenses']:,.0f}, savings rate \u20b9{fin_summary['monthly_savings']:,.0f}."
        )
        assumptions.append(f"Projects cumulative balances and goal achievements deterministically over {horizon} months.")
        if goals:
            assumptions.append(f"Assesses feasibility and estimated completion months against {len(goals)} active financial goals.")

    elif domain == "study":
        study_summary = db.get_user_study_summary(user_id)
        user_data["study"] = study_summary
        has_baseline_data = (
            float(study_summary.get("avg_hours_per_day", 0)) > 0
            or int(study_summary.get("days_active", 0)) > 0
        )
        current_hrs = study_summary.get("avg_hours_per_day", 0.0)
        current_score = study_summary.get("avg_performance_score", 0.0)
        assumptions.append(
            f"Baseline reflects your logged study activity: {current_hrs:.1f} hrs/day, average performance score {current_score:.1f}%."
        )
        assumptions.append(
            f"Evaluates performance growth using predictive modeling under {int((req.consistency or 0.6) * 100)}% study consistency."
        )
        assumptions.append(f"Calculates total cumulative investment ({horizon * 30} potential study days).")

    elif domain == "habits":
        habit_summary = db.get_user_habit_summary(user_id)
        user_data["habits"] = habit_summary
        has_baseline_data = (
            float(habit_summary.get("avg_completion_rate", 0)) > 0
            or float(habit_summary.get("avg_steps", 0)) > 0
            or len(habit_summary.get("habit_names", [])) > 0
        )
        comp_rate = habit_summary.get("avg_completion_rate", 0.0)
        freq = habit_summary.get("exercise_frequency", 3)
        assumptions.append(
            f"Baseline reflects your current habit completion ({comp_rate:.0f}%) and workout frequency ({freq} days/week)."
        )
        assumptions.append(
            f"Projects composite fitness scores incorporating sleep regularity and step averages across {horizon} months."
        )

    disclaimer = (
        "What-if simulations are deterministic projections based on historical data and scenario parameters. "
        "They are designed for comparative decision support and do not guarantee future outcomes or constitute certified financial or medical advice."
    )

    sim_request = SimulationRequest(
        user_id=user_id,
        domain=domain,
        horizon_months=horizon,
        custom_params={
            "scenarios": formatted_custom,
            "consistency": req.consistency or 0.6,
        },
    )

    try:
        sim_result = run_simulation(sim_request, user_data)
    except Exception as e:
        logger.exception("Simulation execution failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute simulation: {str(e)}",
        )

    scenarios = sim_result.get("scenarios", [])
    raw_rec = sim_result.get("recommendation")
    comparison_table = get_comparison_table(scenarios, domain)

    scenario_schemas: list[ScenarioResultSchema] = []
    for s in scenarios:
        scenario_schemas.append(
            ScenarioResultSchema(
                name=s.name,
                description=s.description,
                is_baseline=s.is_baseline,
                input_params=s.input_params,
                output_metrics=s.output_metrics,
                score=float(s.score),
                score_breakdown={k: float(v) for k, v in s.score_breakdown.items()},
                time_series=s.time_series,
            )
        )

    rec_schema = None
    if raw_rec:
        rec_schema = SimulationRecommendationSchema(
            recommended_scenario=str(raw_rec.get("recommended_scenario", "")),
            score=float(raw_rec.get("score", 0.0)),
            reason=str(raw_rec.get("reason", "")),
            benefits=[str(b) for b in raw_rec.get("benefits", [])],
            risks=[str(r) for r in raw_rec.get("risks", [])],
            next_actions=[str(a) for a in raw_rec.get("next_actions", [])],
            baseline_comparison=raw_rec.get("baseline_comparison", {}),
        )

    return RunSimulationResponse(
        domain=domain,
        horizon_months=horizon,
        has_baseline_data=has_baseline_data,
        scenarios=scenario_schemas,
        comparison_table=comparison_table,
        recommendation=rec_schema,
        assumptions=assumptions,
        disclaimer=disclaimer,
    )


@app.post("/api/simulation/save", response_model=SaveSimulationResponse)
def save_simulation_endpoint(
    req: SaveSimulationRequest,
    current_user: dict = Depends(get_current_user),
):
    """Persist simulation scenarios and recommendations to the user's Digital Twin."""
    user_id = current_user["user_id"]
    try:
        sim_id = db.create_simulation(
            user_id=user_id,
            simulation_type=req.domain,
            title=req.title,
            horizon_months=req.horizon_months,
            parameters=req.parameters,
        )

        rec_scenario_id = None
        for s in req.scenarios:
            scenario_id = db.add_simulation_scenario(
                simulation_id=sim_id,
                scenario_name=s.name,
                is_baseline=s.is_baseline,
                input_data=s.input_params,
                output_data=s.output_metrics,
                score=s.score,
            )
            if req.recommendation and s.name == req.recommendation.recommended_scenario:
                rec_scenario_id = scenario_id

        if req.recommendation and rec_scenario_id:
            db.add_recommendation(
                user_id=user_id,
                simulation_id=sim_id,
                recommended_scenario_id=rec_scenario_id,
                recommendation_text=req.recommendation.reason,
                category=req.domain,
                priority="medium",
                reason=req.recommendation.reason,
                risks="; ".join(req.recommendation.risks),
                next_action="; ".join(req.recommendation.next_actions),
            )

        return SaveSimulationResponse(
            simulation_id=sim_id,
            message=f"Simulation '{req.title}' successfully saved to your Digital Twin.",
        )
    except Exception as e:
        logger.exception("Failed to persist simulation: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save simulation: {str(e)}",
        )


@app.get("/api/simulation/history", response_model=list[SimulationHistoryItem])
def get_simulation_history_endpoint(
    domain: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve past saved simulations for the authenticated user."""
    user_id = current_user["user_id"]
    try:
        df = db.get_simulations(user_id, simulation_type=domain, limit=20)
        if df.empty:
            return []
        results = []
        for _, row in df.iterrows():
            results.append(
                SimulationHistoryItem(
                    simulation_id=int(row["simulation_id"]),
                    simulation_type=str(row["simulation_type"]),
                    title=str(row["title"]),
                    horizon_months=int(row["horizon_months"]),
                    created_at=str(row["created_at"]),
                    parameters=row.get("parameters") if isinstance(row.get("parameters"), dict) else None,
                )
            )
        return results
    except Exception as e:
        logger.exception("Failed to retrieve simulation history: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not retrieve simulation history: {str(e)}",
        )


# Preserved legacy chat endpoint
@app.post("/api/chat")
def legacy_chat_endpoint(req: LegacyChatRequest):
    try:
        uid = int(req.user_id) if req.user_id.isdigit() else 1
        service = ConversationService(uid)
        turn = service.answer(req.message.strip())
        return {"response": turn.answer}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)