# Synth — Research Intelligence Platform

A research intelligence backend built with FastAPI.

## Current Features
- GET / — Welcome endpoint
- GET /health — Health check
- POST /extract — Accepts a research abstract

## Run Locally
Activate the virtual environment and run:

python -m uvicorn main:app --reload

API documentation: http://127.0.0.1:8000/docs
