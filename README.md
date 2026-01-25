# 📊 US Treasury Pipeline

A comprehensive data pipeline for extracting, processing, and visualizing US Treasury financial data. This project features a FastAPI backend deployed on Render, an automated data ingestion pipeline, and an interactive Streamlit dashboard for real-time financial analytics.

---

## 🎯 Project Overview

The US Treasury Pipeline is a full-stack application designed to ingest Treasury data from official sources, perform data validation and transformation, expose insights through a RESTful API, and visualize metrics via an interactive dashboard. This pipeline serves as a backbone for analyzing Treasury bond yields, auction data, and other critical financial indicators.

**Key Objectives:**
- Automate Treasury data collection and processing
- Expose cleaned data through a scalable REST API
- Provide real-time financial analytics via interactive dashboard
- Enable programmatic access to Treasury metrics

---

## 🛠️ Tech Stack

* **Backend API:** FastAPI
* **Data Extraction:** US treasury API
* **API Hosting:** Render
* **Frontend Dashboard:** Streamlit
* **Languages:** Python
* **Visualization:** Streamlit
* **Infrastructure:** Docker
* **Data Storage:** Postgres Database hosted on aiven

---

## 📁 Project Structure

```
US-Treasury-Pipeline/
├── Api/                    # FastAPI application & endpoints
│   ├── main.py             # FastAPI application entry point
│   ├── models/             # Data models & schemas
├── Data/                   # Raw and processed data storage
│   ├── db_conn             #Connection to database
│   └── data.py             # data extraction
|   └── models.py           # Data models for API endpoint
├── Logs/                   # Pipeline execution logs
│   └── [Execution records and error tracking]
├── dashboard.py            # Streamlit frontend application
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container configuration
├── .gitignore              # Git ignore rules
├── .dockerignore           # Docker ignore rules
└── README.md               # Project documentation
```

---

## 🏗️ Architecture Overview

### 1. **Data Extraction & Pipeline**
- Fetches Treasury data from public sources (US Department of Treasury APIs)
- Handles authentication, rate limiting, and error handling
- Validates data quality and performs deduplication
- Stores processed data in `Data/` folder

### 2. **FastAPI Backend (Api/)**
- RESTful API endpoints serving Treasury data
- Data models with Pydantic validation
- CORS-enabled for cross-origin requests
- Deployed on Render cloud platform
- Handles authentication and request validation

### 3. **Streamlit Dashboard (dashboard.py)**
- Consumes data from FastAPI backend via HTTP requests
- Interactive web interface for exploring Treasury metrics
- Real-time data visualization and trend analysis
- Responsive UI with filters and date range selectors

### 4. **Data Storage (Data/)**
- Persistent storage of raw and processed datasets into the database
- Batch data uploads(200 records per insertion) for 4861 records
- Organized by data type and time period
---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Docker & Docker Compose
- Git
- Render account (for API deployment)

### Local Installation & Development

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Human-Gechi/US-Treasury-Pipeline.git
   cd US-Treasury-Pipeline
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   Create a `.env` file:
   ```bash
   # API Configuration
   API_KEY= ***
   
   # DATABASE CREDENTIALS
   DB_HOST = *******
   DB_USER = *****
   DB_PORT = ***
   DB_PASSWORD = ****
   DATABASE_URL = *****
   ```

4. **Run Locally with Docker**
   ```bash
   docker-compose up -d
   ```

---

## 🚀 Running the Application

### Start FastAPI Backend (Local Development)
```bash
cd Api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
API will be available at: `http://localhost:8000`
API Docs (Swagger UI): `http://localhost:8000/docs`

### Start Streamlit Dashboard
In a separate terminal:
```bash
streamlit run dashboard.py
```
Dashboard will be available at: `http://localhost:8501`

### Production Deployment (Render)

**FastAPI is already deployed on Render:**
- **API Endpoint:** `https://your-app.onrender.com`
- **Health Check:** `https://your-app.onrender.com/health`
- **API Documentation:** `https://your-app.onrender.com/docs`

The Streamlit dashboard automatically connects to the Render-hosted API in production.

---

## 📊 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/records` | Fetch First 50 Treasury data for avergae_securities|
| `GET` | `/records/record_count` | Fetch total records at the endpoint|
| `GET` | `/records/latest` | Fetch latest record |
| `GET` | `/records/type` | Fetch records by type |
| `GET` | `/records/by-date` | Fetch records by date |
| `GET` | `get_records_by_security_type`| Filter records by security type |
| `GET` | `get_records_by_security_type_and_date` | Fetch records by securities_type and date |


## 📈 Pipeline Workflow

1. **Data Extraction** -> Treasury APIs fetch latest financial metrics
3. **Transformation** -> Cleaning, aggregation, and enrichment
4. **Storage** -> Processed data persisted to database
5. **API Exposure** -> FastAPI serves data via REST endpoints
6. **Visualization** -> Streamlit dashboard consumes API data and displays insights

---

## 🔌 Dashboard Features

- **Real-time Metrics Dashboard** -> Current average securities yields and rates
- **Historical Trend Analysis**  -> Graph depicting securities trends overtime
- **Record count** -> Total count, individual security type count
- **Latest Record**
---


### Dashboard Connection Issues
- Check API is running: Check render service if you provided the accurate credentials
- Clear browser cache and restart Streamlit

### Data Not Appearing
- Ensure data files exist in `Data/` folder
- Verify API credentials in environment variables
- Check API logs for data fetch errors

### Docker Issues
```bash
# Rebuild containers
docker-compose build --no-cache

# Clear volumes
docker-compose down -v

# Restart all services
docker-compose up -d
```

---

## 🔐 Security Considerations
- Store API keys in environment variables (never hardcode)
- Use Render's environment variable management for production secrets
- Enable CORS only for trusted domains

---

## 📊 Data Schema

The pipeline processes Treasury metrics including:

- record_id
- record_date
- record_year (Generated at runtime from record_date)
- security_type_desc (Marketable, Non-Marketable, Interest-bearin debt)
-avg_interest_rate_amt (%avg_interest_rate)
---

## 🚀 Deployment on Render

### Pre-requisites
- GitHub repository linked to Render
- Docker image building enabled

### Deployment Steps

1. **Create Render Service**
   - Go to https://dashboard.render.com
   - Click "New" → "Web Service"
   - Connect GitHub repository
   - Set Build Command: `pip install -r requirements.txt`
   - Set Start Command: `uvicorn Api.main:app --host 0.0.0.0 --port $PORT`

2. **Configure Environment Variables**
   - Add all variables from `.env` in Render dashboard

3. **Deploy**
   - Click "Deploy"
   - Monitor logs in Render dashboard
   - API will be live at provided URL

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Commit changes (`git commit -m 'Add YourFeature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Open a Pull Request

---

## 📈 Performance Metrics

- **API Response Time:** <= 50 seconds
- **Dashboard Load Time:** <= 50 seconds
- **Data Refresh Frequency:** Every month
- **Data Accuracy:** 95%

---

## 📜 License

This project is open source and available under the MIT License.

---

## 👤 About the Author

**Ogechukwu Abimbola Okolі**

Building scalable data pipelines and analytics systems.

- **Focus:** Data Engineering,Anaytics, ML
- **LinkedIn:** [LinkedIn](https://shorturl.at/PwBSf)
- **GitHub:** [@Human-Gechi](https://github.com/Human-Gechi)

---
