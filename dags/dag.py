# Importing necessary libraries
import asyncio
import datetime
import sys

import pendulum

from airflow.sdk import dag, task

# Default dags argument
default_args = {
    "owner": "Human-Gechi",
    "email": "okoliogechi74@gmail.com",
    "email_on_failure": True,
    "email_on_retry": True,
    "retries": 3,
    "retry_delay": datetime.timedelta(minutes=3),
}


@dag(
    dag_id="Securities_Rate",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 2, 2),
    schedule="0 0 10 * *",
)
def securities_rate():
    @task(task_id="run_data_task")
    def run_data():

        project_root = "/opt/airflow/"

        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from data.data_extract import api_insertion
        from data.db_conn import connect_to_db, close_db_pool

        async def main():
            await connect_to_db()
            await api_insertion(records=[])
            await close_db_pool()

        asyncio.run(main())

    run_data()


securities_rate()
