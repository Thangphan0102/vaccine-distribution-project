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
    data_path = os.path.join(parent_dir, 'data', 'vaccine-distribution-data.xlsx')
    tablecreation_path = os.path.join(parent_dir, 'code', 'tablecreation.sql')
    sql_queries_path = os.path.join(parent_dir, 'code', 'SQL_queries.sql')
    # Read the Excel file into a pandas DataFrame
    df = pd.ExcelFile(data_path)

    # Use the DataFrame for further processing or analysis
    sheet_names = df.sheet_names
    data = {}
    for sheet in sheet_names:
        temp = df.parse(sheet)
        temp.columns = temp.columns.str.lower()
        data[sheet] = temp

    # relating the SQL tables to the imported sheets in the dataframe
    tables = {}
    tables['vaccinetype'] = 'VaccineType'
    tables['manufacturer'] = 'Manufacturer'
    tables['vaccinationstations'] = 'VaccinationStations'
    tables['vaccinebatch'] = 'VaccineBatch'
    tables['transportationlog'] = 'Transportation log'
    tables['staffmembers'] = 'StaffMembers'
    tables['shifts'] = 'Shifts'
    tables['vaccinations'] = 'Vaccinations'
    tables['patients'] = 'Patients'
    tables['vaccinepatients'] = 'VaccinePatients'
    tables['symptoms'] = 'Symptoms'
    tables['diagnosis'] = 'Diagnosis'

    # Connect to the database
    database = 'grp02db_2023'  # TO BE REPLACED
    user = 'grp02_2023'  # TO BE REPLACED
    password = 'A88z1c6B'  # TO BE REPLACED
    host = 'dbcourse.cs.aalto.fi'

    connection = psycopg2.connect(
        database=database,  # TO BE REPLACED
        user=user,  # TO BE REPLACED
        password=password,  # TO BE REPLACED
        host=host,
        port='5432'
    )
    connection.autocommit = True

    DIALECT = 'postgresql+psycopg2://'
    db_uri = "%s:%s@%s/%s" % (user, password, host, database)
    engine = create_engine(DIALECT + db_uri)
    psql_conn = engine.connect()

    # Execute table creation
    with open(tablecreation_path, 'r') as file:
        script_content = file.read()
    cursor = connection.cursor()
    cursor.execute(script_content)
    connection.commit()

    # Renaming columns
    data['Transportation log'].rename(columns={'departure ': 'departure'}, inplace=True)
    data['StaffMembers'].rename(columns={'social security number': 'ssno',
                                         'date of birth': 'birthday', 'vaccination status': 'status'}, inplace=True)
    data['Patients'].rename(columns={'date of birth': 'birthday'}, inplace=True)
    data['Vaccinations'].rename(columns={'location ': 'location'}, inplace=True)

    # Data cleaning

    # Diagnosis table
    data['Diagnosis'].loc[data['Diagnosis']['patient'] == '730126-956K', 'date'] = '2021-02-28'
    data['Diagnosis'].drop(data['Diagnosis'].loc[data['Diagnosis']['date'] == 44237].index, inplace=True)

    # Drop type column from the VaccineBatch
    data['VaccineBatch'].drop(columns=['type'], inplace=True)

    # Populating SQL tables from the dataframe sheet by sheet
    for key in tables:
        # print(data[tables[key]])
        data[tables[key]].to_sql(key, con=psql_conn, if_exists='append', index=False)

    # Execute SQL queries
    with open(sql_queries_path, 'r') as file:
        script_queries = file.read()
    cursor = connection.cursor()
    cursor.execute(script_queries)
    connection.commit()

except (Exception, Error) as error:
    print("Error while connecting to PostgreSQL", error)
finally:
    if (connection):
        psql_conn.close()
        cursor.close()
        connection.close()

        print("PostgreSQL connection is closed")
