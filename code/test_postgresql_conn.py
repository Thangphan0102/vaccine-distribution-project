# Source: https://pynative.com/python-postgresql-tutorial/
import psycopg2
import os
from psycopg2 import Error
import pandas as pd
from sqlalchemy import create_engine, text

try:
   # Get the directory path of the current script
   script_dir = os.path.dirname(os.path.abspath(__file__))

   # Remove the "/code" part from the script directory path
   parent_dir = os.path.dirname(script_dir)

   # Construct the relative file path
   file_path = os.path.join(parent_dir, 'data', 'vaccine-distribution-data.xlsx')

   # Read the Excel file into a pandas DataFrame
   df = pd.ExcelFile(file_path)

   # Use the DataFrame for further processing or analysis
   sheet_names=df.sheet_names
   data={}
   for sheet in sheet_names:
      temp=df.parse(sheet)
      temp.columns = temp.columns.str.lower()
      data[sheet]=temp
   tables={}
   tables['vaccinetype']='VaccineType'
   tables['manufacturer']='Manufacturer'


   # Connect to an test database 
   # NOTE: 
   # 1. NEVER store credential like this in practice. This is only for testing purpose
   # 2. Replace your "database" name, "user" and "password" that we provide to test the connection to your database 
   database = 'grp02db_2023'  # TO BE REPLACED
   user = 'grp02_2023'  # TO BE REPLACED
   password = 'A88z1c6B'  # TO BE REPLACED
   host = 'dbcourse.cs.aalto.fi'

   connection = psycopg2.connect(
      database="grp02db_2023",  # TO BE REPLACED
      user='grp02_2023',  # TO BE REPLACED
      password='A88z1c6B',  # TO BE REPLACED
      host='dbcourse.cs.aalto.fi',
      port='5432'
   )
   connection.autocommit = True

   DIALECT = 'postgresql+psycopg2://'
   db_uri = "%s:%s@%s/%s" % (user, password, host, database)
   engine = create_engine(DIALECT + db_uri)
   psql_conn = engine.connect()

   for key in tables:
      print(data[tables[key]])
      data[tables[key]].to_sql(key, con=psql_conn, if_exists='append', index=False)

except (Exception, Error) as error:
   print("Error while connecting to PostgreSQL", error)
finally:
   if (connection):
      psql_conn.close()
      connection.close()
      print("PostgreSQL connection is closed")