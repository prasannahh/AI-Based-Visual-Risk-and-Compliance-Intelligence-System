-- ============================================================================
-- Milestone 3 — Digital Twin Simulation Engine migration
-- Digital Twin AI — PostgreSQL
-- ----------------------------------------------------------------------------
-- Adds the tables required by the Simulation Engine to an existing
-- Milestone 1 + Milestone 2 database. All statements are idempotent
-- (CREATE TABLE IF NOT EXISTS), so running this script more than once is safe.
--
-- Usage:
--   psql -U postgres -d digital_twin -f sql/milestone_3.sql
--
-- The same DDL is executed automatically by database.init_db() on app start,
-- so this script is only needed for standalone/manual migrations.
-- ============================================================================

-- Stores each simulation run (e.g. "Financial Simulation - 12 months").
CREATE TABLE IF NOT EXISTS Simulations (
    simulation_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    simulation_type VARCHAR(40) NOT NULL,
    title VARCHAR(200) NOT NULL,
    horizon_months INT NOT NULL DEFAULT 12,
    parameters JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Individual scenario outcomes within a simulation run.
CREATE TABLE IF NOT EXISTS Simulation_Scenarios (
    scenario_id SERIAL PRIMARY KEY,
    simulation_id INT REFERENCES Simulations(simulation_id) ON DELETE CASCADE,
    scenario_name VARCHAR(150) NOT NULL,
    is_baseline BOOLEAN DEFAULT FALSE,
    input_data JSONB,
    output_data JSONB,
    score NUMERIC(8,4),
    created_at TIMESTAMP DEFAULT NOW()
);

-- AI-generated recommendations tied to a simulation.
CREATE TABLE IF NOT EXISTS Recommendations (
    recommendation_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    simulation_id INT REFERENCES Simulations(simulation_id) ON DELETE CASCADE,
    recommended_scenario_id INT REFERENCES Simulation_Scenarios(scenario_id),
    recommendation_text TEXT NOT NULL,
    category VARCHAR(60),
    priority VARCHAR(20) DEFAULT 'medium',
    reason TEXT,
    risks TEXT,
    next_action TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
