# Milestone 3 – Digital Twin Simulation Engine

## Overview

Milestone 3 introduces the **Digital Twin Simulation Engine**, which allows users to simulate different decisions, compare future outcomes, and receive personalized recommendations.

The milestone focuses on:

* Decision and scenario simulation
* Future outcome comparison
* Recommendation generation

## Features

* Create and simulate different scenarios
* Compare multiple future outcomes
* Generate personalized recommendations
* Streamlit-based simulation interface
* SQL support for simulation-related data
* Automated tests for simulation and recommendations

## Project Structure

```text
simulation/
├── engine.py
├── scenarios.py
├── comparator.py
└── recommendation.py

pages_app/
└── simulation.py

sql/
└── milestone_3.sql

tests/
├── test_simulation.py
└── test_recommendation.py
```

## How to Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run app.py
```

Run tests:

```bash
pytest
```

## Milestone 3 Workflow

```text
User Input
    ↓
Scenario Creation
    ↓
Simulation
    ↓
Outcome Comparison
    ↓
Recommendation
```

## Status

**Milestone 3 – Completed ✅**

Main focus:

**Simulate → Compare → Recommend**
