# importing necessary libraries
import asyncio
import os
import sys
import time
from datetime import datetime

import requests
from sqlalchemy import insert

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Data.models import APIHealthCheck
from Logs.logs import api_logger


async def run_monitor_cycle():
    """Function to monitor API health and log results to the datatbase"""

    url = "https://us-treasury-pipeline.onrender.com/health"
    start_time = time.time()
    from Data.db_conn import close_db_pool, connect_to_db

    try:
        # Making a GET request to the API endpoint
        response = requests.get(url, timeout=10)
        status = response.status_code
        message = response.reason

        # Error messages for specific status codes
        if status == 404:
            message = f"{message}: Endpoint missing - check your URL"
        elif status == 405:
            message = f"{message}: Wrong method - use GET, not POST"
        health_status = status == 200  # Setting status = True if condition is fulfilled

    except requests.exceptions.RequestException as e:
        api_logger.error(f"Request failed: {e}")

        # If no specific status code is returned as sometimes render API goes to sleep
        status = 0
        message = "Connection Error: API might be sleeping or down"
        health_status = False

    latency = round(
        (time.time() - start_time) * 1000, 2
    )  # Calculating latency/Start to finish times in milliseconds

    await connect_to_db()
    from Data.db_conn import db_engine

    if db_engine is None:
        api_logger.error("No connection made to the database.")
        return "No connection made to the database."
    try:
        async with db_engine.begin() as conn:
            await conn.execute(
                insert(APIHealthCheck).values(
                    checked_at=datetime.utcnow(),
                    status_code=status,
                    status_message=message,
                    latency_ms=latency,
                    is_healthy=health_status,
                )
            )
            api_logger.info(f"[{status}] {message} - Recorded ({latency:.2f}ms)")
    except Exception as e:
        api_logger.error(f"Error inserting into database: {e}")  # Error in db insertion
    else:
        api_logger.info(
            f"[{status}] {message} - Recorded ({latency:.2f}ms)"
        )  # Print Status message and time taken
    finally:
        await close_db_pool()  # Close the database connection


asyncio.run(run_monitor_cycle())
