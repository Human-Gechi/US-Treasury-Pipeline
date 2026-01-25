import requests
import time
from monitor_db import make_connection

def run_monitor_cycle():
    #Making a request to the endpoint
    url = "https://us-treasury-pipeline.onrender.com/health"
    start_time = time.time() #start time

    try:
        response = requests.get(url, timeout=10)
        status = response.status_code
        message = response.reason

        if status == 404:
            message = f"{message}: Endpoint missing - check your URL"
        elif status == 405:
            message = f"{message}: Wrong method - use GET, not POST"
        health_status = (status == 200) #Setting status = True if condition is fufilled

    except requests.exceptions.RequestException as e:
        status = 0
        message = "Connection Error: API might be sleeping or down"
        health_status = False

    latency = (time.time() - start_time) * 1000
    #writing to aiven db
    conn = make_connection()
    if conn:
        try:
            cur = conn.cursor()
            query = """
                INSERT INTO API_health_checks 
                (status_code, status_message, latency_ms, is_healthy) 
                VALUES (%s, %s, %s, %s)
            """
            cur.execute(query, (status, message, latency, health_status))
            conn.commit()
            print(f"[{status}] {message} - Recorded ({latency:.2f}ms)")
        finally:
            conn.close()
run_monitor_cycle()