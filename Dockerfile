FROM python:3.11-slim

#See logs int docker in realtime
ENV PYTHONUNBUFFERED=1

#DO NOT CREATE .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

#Create new user since docker runs on root
RUN useradd -m newuser
USER newuser

CMD [ "uvicorn", "Api.main:app", "--host", "0.0.0.0", "--port", "8000" ]


