FROM python:3.12-slim

# See logs in docker in realtime
ENV PYTHONUNBUFFERED=1

# DO NOT CREATE .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ ./api/
COPY data/ ./data/
COPY log.py .


ARG AIRFLOW_UID=50000
RUN useradd -m -u ${AIRFLOW_UID} airflow
USER airflow

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001"]