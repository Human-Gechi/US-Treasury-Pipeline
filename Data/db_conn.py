#Importing necessary libraries
import os
import sys
import asyncio
import asyncpg
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.abspath(__file__))) #Appending file path to avoid import errors
from Logs.logs import db_logger
load_dotenv() #Load env. variables

db_url = os.getenv("DATABASE_URL")#get db url
db_pool = None #Defining db_pool

async def connect_to_db(): #Mkae a connection
    global db_pool #Uing the initally set db_pool
    if db_pool is None: #If no connection made,
        db_pool = await asyncpg.create_pool(db_url, min_size=1, max_size=5) #Make a connection by creating a coroutine
        db_logger.info("Connection to Database was successful") #db_logger info
    return db_pool

async def create_tables(): #Create tables
    try:
        global db_pool #Use db_pool
        if db_pool is None:
            raise Exception("DB pool not initialized. Call connect_to_db() ") #If no connection made error

        #create table
        table_query = """ 
            CREATE TABLE IF NOT EXISTS avg_us_securities_2001_present (
                record_date DATE,
                record_year INT GENERATED ALWAYS AS (COALESCE(EXTRACT(YEAR FROM record_date)::INT, 0)) STORED,
                security_type_desc VARCHAR(100) CHECK(security_type_desc IN('Marketable','Non-marketable','Interest-bearing Debt')),
                security_desc VARCHAR(100),
                avg_interest_rate_amt DECIMAL(7,5) DEFAULT 0
            )
        """
        #Acquire connection and execute table creation query
        async with db_pool.acquire() as conn:
            await conn.execute(table_query)
            db_logger.info("Table created successfully") #log message
    except Exception as e:
        db_logger.info(f"Table not created : {e}")

async def insert_data(rows, batch_size=1000): #Insert data
    global db_pool #Use global_pool
    if db_pool is None: #If no connection made:
        raise Exception("DB pool not initialized. Call connect_to_db() first.") #Raise an exception

    if not rows: #If no data fetched
        db_logger.warning("No rows to insert - empty list")
        return 0

    total_inserted = 0 #Count for total number of data inserted
    #Inserting data
    insertion = """
        INSERT INTO avg_us_securities_2001_present(
            record_date,
            security_type_desc,
            security_desc,
            avg_interest_rate_amt
        ) VALUES ($1, $2, $3, $4)
        ON CONFLICT(record_date, security_type_desc, security_desc) DO NOTHING
    """
    #Try,except block to insert data
    try:
        for i in range(0, len(rows), batch_size): #For loop for insertion
            batch = rows[i : i + batch_size] #Getting the number of rows per batch

            #Acquire a connection
            async with db_pool.acquire() as connection:
                db_logger.info(f"Connection acquired")
                await connection.executemany(insertion, batch) #Multi row insertion.
                total_inserted += len(batch) #Increment total insertion counter
        return total_inserted #Return the count
    #Error message
    except Exception as e: #If there be errors:
        db_logger.error(f"DB insertion failed: {e}")
        db_logger.error(f"Exception type: {type(e)}")

        return total_inserted #Return inserted count

#Call the functions to create tables and connect to db
async def main():
    await connect_to_db()
    await create_tables()

if __name__ == "__main__":
    asyncio.run(main()) # run main()

