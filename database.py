"""
database.py
------------
Handles the PostgreSQL connection and defines the ORM tables (via SQLAlchemy)
for the Health & Fitness Digital Twin project.

Tables created:
    users            -> static personal / profile information
    daily_logs       -> day-to-day health metrics entered by the user
    predictions      -> AI prediction snapshots (weight, BMI, fitness score, risks)
    simulations       -> "what-if" scenario results
    recommendations  -> personalized recommendations generated for a user
"""

import os
from datetime import datetime, date

from dotenv import load_dotenv
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Date, DateTime,
    ForeignKey, Text, JSON
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "digital_twin_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    security_question = Column(String(200))
    security_answer_hash = Column(String(255))

    age = Column(Integer)
    gender = Column(String(20))
    height_cm = Column(Float)
    weight_kg = Column(Float)
    blood_group = Column(String(10))
    medical_history = Column(Text)
    fitness_goal = Column(String(50))  # weight_loss, muscle_gain, endurance, maintenance

    created_at = Column(DateTime, default=datetime.utcnow)

    daily_logs = relationship("DailyLog", back_populates="user", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")
    simulations = relationship("Simulation", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
    health_record = relationship("HealthRecord", back_populates="user", uselist=False,
                                   cascade="all, delete-orphan")


class DailyLog(Base):
    __tablename__ = "daily_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    log_date = Column(Date, default=date.today)

    steps = Column(Integer, default=0)
    exercise_minutes = Column(Integer, default=0)
    calories_burned = Column(Float, default=0)
    calories_consumed = Column(Float, default=0)
    water_liters = Column(Float, default=0)
    sleep_hours = Column(Float, default=0)
    sleep_quality = Column(String(20))  # poor, average, good, excellent
    weight_kg = Column(Float)

    heart_rate = Column(Integer)
    blood_pressure_sys = Column(Integer)
    blood_pressure_dia = Column(Integer)
    blood_sugar = Column(Float)

    user = relationship("User", back_populates="daily_logs")


class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    predicted_weight_kg = Column(Float)
    predicted_bmi = Column(Float)
    fitness_score = Column(Float)
    daily_calorie_requirement = Column(Float)

    obesity_risk = Column(String(20))
    diabetes_risk = Column(String(20))
    hypertension_risk = Column(String(20))

    user = relationship("User", back_populates="predictions")


class Simulation(Base):
    __tablename__ = "simulations"

    simulation_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    scenario_name = Column(String(120))
    horizon_days = Column(Integer)
    input_params = Column(JSON)
    projected_weight_kg = Column(Float)
    projected_bmi = Column(Float)
    projected_fitness_score = Column(Float)
    summary = Column(Text)

    user = relationship("User", back_populates="simulations")


class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = Column(String(50))     # nutrition, exercise, sleep, hydration, risk_alert
    priority = Column(String(20))     # low, medium, high
    recommendation_text = Column(Text)

    user = relationship("User", back_populates="recommendations")


class HealthRecord(Base):
    """One row per user -- detailed medical background, editable any time
    from the Health Records page (separate from the free-text `medical_history`
    field on the profile, which is a quick summary)."""
    __tablename__ = "health_records"

    health_record_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    allergies = Column(Text)
    chronic_conditions = Column(Text)
    current_medications = Column(Text)
    past_surgeries = Column(Text)

    user = relationship("User", back_populates="health_record")


def init_db():
    """Create all tables if they do not already exist."""
    Base.metadata.create_all(engine)


def get_session():
    """Return a new SQLAlchemy session."""
    return SessionLocal()