#!/bin/bash
echo "Starting API endpoint"

python -m uvicorn Api.main:app --host 0.0.0.0 --port 8080
