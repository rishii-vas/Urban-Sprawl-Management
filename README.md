# Urban Sprawl Management – Water Infrastructure Module

This project is a proof-of-concept backend for managing urban infrastructure stress caused by rapid urban growth.

## Features
- Machine learning–based stress prediction (Low / Medium / High)
- FastAPI backend
- Separate endpoints for:
  - Government dashboard
  - Civilian dashboard

## Tech Stack
- Python
- FastAPI
- Scikit-learn
- Pandas

## How to Run
```bash
pip install -r requirements.txt
python ml/train_model.py
python -m uvicorn api.main:app --reload

