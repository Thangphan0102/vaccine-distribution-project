# Source: https://pynative.com/python-postgresql-tutorial/
import psycopg2
from psycopg2 import Error
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import date
from dateutil.relativedelta import relativedelta 

try:

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


    sql_query_1 = """
    SELECT patient AS ssNO, gender, birthday AS dateOfBirth, symptom, date AS diagnosisDate
    FROM diagnosis, patients
    WHERE patient = ssno
    order by diagnosisDate;
    """
    sql_query_2 = """
    SELECT
    vp1.patientssno,
    v1.date AS date1,
    m1.vaccine AS vaccinetype1,
    v2.date AS date2,
    m2.vaccine AS vaccinetype2
    FROM
    vaccinepatients vp1
    LEFT JOIN
    vaccinations v1 ON vp1.date = v1.date AND vp1.location = v1.location
    LEFT JOIN
    vaccinebatch vb1 ON v1.batchid = vb1.batchid
    LEFT JOIN
    manufacturer m1 ON vb1.manufacturer = m1.id
    LEFT JOIN
    vaccinepatients vp2 ON vp1.patientssno = vp2.patientssno and vp2.date != vp1.date 
    LEFT JOIN
    vaccinations v2 ON vp2.date = v2.date AND vp2.location = v2.location 
    LEFT JOIN
    vaccinebatch vb2 ON v2.batchid = vb2.batchid
    LEFT JOIN
    manufacturer m2 ON vb2.manufacturer = m2.id
    WHERE
    v1.date < v2.date OR v2.date IS NULL
    """


    sql_query_3 = """
    SELECT *
    FROM "PatientSymptoms"
    """

    sql_query_4 = """
    SELECT *
    FROM patients
    """

    #1
    df = pd.read_sql_query(sql_query_1, psql_conn)
    df.to_sql("PatientSymptoms", con=psql_conn, if_exists='replace', index=True)
    psql_conn.commit()
    #2
    df_vaccine = pd.read_sql_query(sql_query_2, psql_conn)
    df_vaccine.to_sql("PatientVaccineInfo", con=psql_conn, if_exists='replace', index=True)
    psql_conn.commit()
    #3
    print('Most frequent symptoms')
    df = pd.read_sql_query(sql_query_3, psql_conn)
    df1=df[df['gender']=='M']
    df2=df[df['gender']=='F']
    print('For Males:\n' + df1['symptom'].value_counts().head(3).to_string() + '\n')
    print('For Females:\n' + df2['symptom'].value_counts().head(3).to_string() + '\n')
    
    #4
    df = pd.read_sql_query(sql_query_4, psql_conn)
    bins = [0, 10, 20, 40, 60, float('inf')]
    labels = ['0-10', '10-20', '20-40', '40-60', '60+']
    df['ageGroup'] = pd.cut(df['birthday'].apply(lambda x: relativedelta(date.today(), x).years), bins=bins, labels=labels, right=False)
    

    #5
    df_vaccine['VaccineCount'] = df_vaccine[['date1', 'date2']].notnull().sum(axis=1)
    vaccine_counts = df_vaccine.groupby('patientssno')['VaccineCount'].sum().astype('str')
    df['VaccineCount'] = df['ssno'].map(vaccine_counts).fillna('0')
    print(df[df['VaccineCount']=='2']) # the dataframe used for task 6 is df

except (Exception, Error) as error:
    print("Error while connecting to PostgreSQL", error)
finally:
    if (connection):
        psql_conn.close()
        connection.close()

        print("PostgreSQL connection is closed")
