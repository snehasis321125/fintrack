# Fintrack - AI Financial Tracker

[![Repo](https://github.com/snehasis321125/fintrack/actions/workflows/ci.yml/badge.svg)](https://github.com/snehasis321125/fintrack/actions)

## Overview
Fintrack is an AI-powered personal finance tracker. Track expenses, get ML-based predictions, and manage finances via a Flask web app.

## Features
- User authentication (login/register)
- Dashboard with expense charts
- AI/ML model for expense predictions (backend/model.py)
- Admin panel
- Profile management

## Tech Stack
- Backend: Flask (Python)
- Frontend: HTML/CSS/JS, Chart.js
- Database: SQLite (backend/db.py)
- ML: Trained models in backend/trained_models/
- Dataset generation & loading scripts

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Init DB: `python backend/init_db.py`
3. Load sample data: `python backend/load_dataset.py`
4. Run app: `python backend/app.py`
5. Open http://localhost:5000

## Project Structure
```
.
├── backend/         # Flask app
│   ├── app.py       # Main app
│   ├── auth.py      # Authentication
│   ├── db.py        # Database models
│   ├── expense.py   # Expense CRUD
│   ├── model.py     # ML model
│   ├── templates/   # HTML templates
│   ├── static/      # CSS/JS/assets
│   └── trained_models/
├── requirements.txt
├── .gitignore
└── README.md
```

## ML Details
- Generates synthetic expense dataset
- Trains model for predictions
- Integrated in dashboard

## License
MIT
