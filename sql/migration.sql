-- ============================================================================
-- Milestone 2 (AI Core Layer) migration
-- Digital Twin AI — PostgreSQL
-- ----------------------------------------------------------------------------
-- Adds the tables required by the AI layer to an existing Milestone 1
-- database. All statements are idempotent (CREATE TABLE IF NOT EXISTS), so
-- running this script more than once is safe.
--
-- Usage:
--   psql -U postgres -d digital_twin -f sql/migration.sql
--
-- The same DDL is executed automatically by database.init_db() on app start,
-- so this script is only needed for standalone/manual migrations.
-- ============================================================================

-- Health measurements used by the health AI models (BMI, weight, calories).
CREATE TABLE IF NOT EXISTS Health_Records (
    record_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    record_date DATE NOT NULL,
    height_cm NUMERIC(6,2),
    weight_kg NUMERIC(6,2)
);

-- Daily fitness inputs used by the fitness AI models.
CREATE TABLE IF NOT EXISTS Fitness_Records (
    record_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    record_date DATE NOT NULL,
    steps INT,
    exercise_minutes NUMERIC(6,2),
    sleep_hours NUMERIC(4,2),
    water_litres NUMERIC(4,2),
    calories_burned NUMERIC(8,2),
    exercise_frequency INT
);

-- Audit trail of every AI model training run.
CREATE TABLE IF NOT EXISTS model_logs (
    log_id SERIAL PRIMARY KEY,
    model_name VARCHAR(120) NOT NULL,
    model_version VARCHAR(40) NOT NULL,
    domain VARCHAR(40) NOT NULL,
    algorithm VARCHAR(80),
    metrics JSONB,
    records INT DEFAULT 0,
    trained_at TIMESTAMP DEFAULT NOW()
);

-- Generic traceability log: every prediction made for a user.
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    domain VARCHAR(40) NOT NULL,
    model_name VARCHAR(120) NOT NULL,
    model_version VARCHAR(40),
    confidence NUMERIC(6,4),
    input_data JSONB,
    output_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Domain-specific prediction history (structured, easy to chart).
CREATE TABLE IF NOT EXISTS health_predictions (
    health_prediction_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    prediction_type VARCHAR(40) NOT NULL,
    result_value NUMERIC(12,4),
    result_category VARCHAR(120),
    confidence NUMERIC(6,4),
    model_version VARCHAR(40),
    input_data JSONB,
    output_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fitness_predictions (
    fitness_prediction_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    prediction_type VARCHAR(40) NOT NULL,
    result_value NUMERIC(8,2),
    result_category VARCHAR(120),
    confidence NUMERIC(6,4),
    model_version VARCHAR(40),
    input_data JSONB,
    output_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS finance_predictions (
    finance_prediction_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    prediction_type VARCHAR(40) NOT NULL,
    result_value NUMERIC(14,2),
    result_category VARCHAR(120),
    confidence NUMERIC(6,4),
    model_version VARCHAR(40),
    input_data JSONB,
    output_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS study_predictions (
    study_prediction_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    prediction_type VARCHAR(40) NOT NULL,
    result_value NUMERIC(8,2),
    result_category VARCHAR(120),
    confidence NUMERIC(6,4),
    model_version VARCHAR(40),
    input_data JSONB,
    output_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
