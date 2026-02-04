#Importing necessary libraries
import sys
import os
import pendulum
import datetime
from airflow.decorators import dag, task #dag and task decorators
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))#Appending file parts to prevent function import errors
#Default dags argument
default_args = {
    'owner': 'Human-Gechi',
    'email': 'okoliogechi74@gmail.com',
    'email_on_failure': True,
    'email_on_retry': True,
    'retries': 3,
    'retry_delay' : datetime.timedelta(minutes=3)
}#Dag definition
@dag(
    dag_id='Securities_Rate',
    default_args=default_args,
    start_date=pendulum.datetime(2026, 2, 2),
    schedule='0 0 10 * *',
)
#Task definition using the @task decorator
def securities_rate():
    @task(task_id="run_data_task") #Defining the task
    def run_data(): #function for the task
        import asyncio #Inner package imports
        from average_securities_rate.Data.data import api_insertion
        from average_securities_rate.Data.db_conn import connect_to_db
        async def main(): #Run the functions
            await connect_to_db()
            await api_insertion()

        asyncio.run(main())
    run_data()
securities_rate() #Call dag func.