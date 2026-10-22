#!/usr/bin/env bash
set -e
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
python scripts/download_models.py
uvicorn app.main:app --reload --port 8000
