#importing necessary libraries
import requests
import time
import monitor_db
import asyncio

async def run_monitor_cycle():
    #Making a request to the endpoint
    url = "https://us-treasury-pipeline.onrender.com/health"
    start_time = time.time() #start time

    try:
        #Making a GET request to the API endpoint
        response = requests.get(url, timeout=10)
        status = response.status_code
        message = response.reason

        #Error messages for specific status codes
        if status == 404:
            message = f"{message}: Endpoint missing - check your URL"
        elif status == 405:
            message = f"{message}: Wrong method - use GET, not POST"
        health_status = (status == 200) #Setting status = True if condition is fufilled

    except requests.exceptions.RequestException as e: #Handling request exceptions
        #If no specific status code is returned as sometimes render API goes to sleep
        status = 0
        message = "Connection Error: API might be sleeping or down" #Api may be down
        health_status = False

    latency = round((time.time() - start_time) * 1000, 2) #Calculating latency/Start to finish times in milliseconds

    #writing to aiven db
    await monitor_db.make_connection() #Await a connection is made from the pool

    db_pool = monitor_db.db_pool
    if db_pool is None:
          return "No connection made to the database."
    try:
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO API_health_checks 
                    (status_code, status_message, latency_ms, is_healthy) 
                    VALUES ($1, $2, $3, $4)
                """, status, message, latency, health_status)
    except Exception as e:
                print(f"Error inserting into database: {e}") #Error in db insertion
    else:
            print(f"[{status}] {message} - Recorded ({latency:.2f}ms)") #Print Status message and time takaen

asyncio.run(run_monitor_cycle()) #un the async function