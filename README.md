# 🩺 AI-Powered Health & Fitness Digital Twin - Milestone 1

An AI-powered Health & Fitness Digital Twin that creates a virtual representation of a user's health profile. The application securely collects daily health information and prepares the data for AI predictions, digital twin simulation, and personalized health recommendations.

---

# 🚀 Project Overview

The Health & Fitness Digital Twin is designed to create a digital representation of a user's health and lifestyle.

The application allows users to:

- Register securely
- Login to their account
- Recover forgotten passwords
- Maintain personal health profiles
- Log daily health activities
- Store historical health records

The collected information serves as the foundation for future AI prediction models and Digital Twin simulations.

---

# ✨ Features

## Authentication

- User Registration
- Secure Login
- Forgot Password
- Password Hashing
- Session Management

---

## Profile Management

Users can manage

- Name
- Age
- Gender
- Height
- Weight
- Blood Group
- Health Goal

---

## Daily Health Log

Users can record

- Steps Walked
- Exercise Duration
- Sleep Hours
- Water Intake
- Calories
- Daily Weight
- Activity Date

---

## Upcoming Modules

- AI Predictions
- Digital Twin Simulation
- Personalized Recommendations
- Analytics Dashboard
- AI Assistant

---

# 🛠 Technology Stack

## Frontend

- Streamlit
- HTML
- CSS

## Backend

- Python

## Database

- PostgreSQL
- SQLAlchemy

## Machine Learning

- Scikit-learn
- Pandas
- NumPy

## Visualization

- Plotly

---

# 📂 Project Structure

```
health_fitness_digital_twin/

│── app.py
│── database.py
│── init_db.py
│── simulation.py
│── recommendations.py
│── chatbot.py
│── utils.py
│
├── data/
│
├── ml/
│   ├── bmi.py
│   ├── fitness_score.py
│   ├── weight_predictor.py
│   ├── risk_classifier.py
│   ├── kaggle_models.py
│   └── evaluate_models.py
│
├── models/
│
├── .streamlit/
│
├── requirements.txt
│
└── README.md
```

---

# 🗄 Database Schema

Database Tables

- Users
- User Profile
- Daily Health Logs
- Predictions
- Recommendations

Database Used

- PostgreSQL

---

# 🔐 Authentication & Security

Security Features

- Password Hashing (bcrypt)
- Secure Login Authentication
- Session Management
- Password Recovery
- PostgreSQL Secure Storage

---

# ⚙ Environment Variables

Create a **.env** file

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=digital_twin_db
DB_USER=postgres
DB_PASSWORD=your_password
OPENAI_API_KEY=your_api_key
```

---

# 🚀 Installation & Running Guide

## 1. Clone Repository

```bash
git clone https://github.com/yourusername/health-fitness-digital-twin.git
```

## 2. Create Virtual Environment

```bash
python -m venv venv
```

Activate

Windows

```bash
venv\Scripts\activate
```

Linux / macOS

```bash
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure PostgreSQL

Create Database

```sql
CREATE DATABASE digital_twin_db;
```

Initialize

```bash
python init_db.py
```

---

## 5. Run Application

```bash
streamlit run app.py

---

# 📅 Milestone 1 Deliverables

✅ User Registration

✅ Login Authentication

✅ Forgot Password

✅ User Profile Management

✅ Daily Health Data Logging

✅ PostgreSQL Integration

✅ Secure Password Storage

---

# 🚀 Upcoming Milestones

## Milestone 2

- AI Predictions
- Forecasting
- Risk Analysis

---

## Milestone 3

- Digital Twin Simulation
- Lifestyle Comparison
- Scenario Analysis

---

## Milestone 4

- AI Assistant
- Dashboard
- Reports
- Deployment

---

# 👨‍💻 Contributors

**Project:** Health & Fitness Digital Twin

**Domain:** Artificial Intelligence | Machine Learning | Healthcare

**Developed By**
Prasanna Sankar B
chitrita Bhattacharjee
Gadde Rohit Kumar Yadhav
Shraddha Vadar

---

# ⭐ Future Scope

- AI-based Disease Risk Prediction
- Personalized Fitness Coaching
- Wearable Device Integration
- Smart Health Dashboard
- Cloud Deployment
- Mobile Application
