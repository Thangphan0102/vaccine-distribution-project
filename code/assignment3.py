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

except (Exception, Error) as error:
    print("Error while connecting to PostgreSQL", error)

###########################################################################################
# QUESTION 1
sql_query_1 = """
SELECT patient AS ssNO, gender, birthday AS dateOfBirth, symptom, DATE AS diagnosisDate
FROM diagnosis, patients
WHERE patient = ssno
ORDER BY diagnosisDate;
"""

df = pd.read_sql_query(sql_query_1, psql_conn)
df.to_sql("PatientSymptoms", con=psql_conn, if_exists='replace', index=True)
print("Question 1:")
print(df)
psql_conn.commit()
###########################################################################################

###########################################################################################
# QUESTION 2
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
vaccinepatients vp2 ON vp1.patientssno = vp2.patientssno AND vp2.date != vp1.date 
LEFT JOIN
vaccinations v2 ON vp2.date = v2.date AND vp2.location = v2.location 
LEFT JOIN
vaccinebatch vb2 ON v2.batchid = vb2.batchid
LEFT JOIN
manufacturer m2 ON vb2.manufacturer = m2.id
WHERE
v1.date < v2.date OR v2.date IS NULL
"""

df_vaccine = pd.read_sql_query(sql_query_2, psql_conn)
df_vaccine.to_sql("PatientVaccineInfo", con=psql_conn, if_exists='replace', index=True)
print("\nQuestion 2:")
print(df_vaccine)
psql_conn.commit()
###########################################################################################

###########################################################################################
# QUESTION 3
sql_query_3 = """
SELECT *
FROM "PatientSymptoms"
"""
print("\nQuestion 3")
print('Most frequent symptoms')
df = pd.read_sql_query(sql_query_3, psql_conn)
df1 = df[df['gender'] == 'M']
df2 = df[df['gender'] == 'F']
print('For Males:\n' + df1['symptom'].value_counts().head(3).to_string() + '\n')
print('For Females:\n' + df2['symptom'].value_counts().head(3).to_string() + '\n')
###########################################################################################

###########################################################################################
# QUESTION 4
sql_query_4 = """
SELECT *
FROM patients
"""

df = pd.read_sql_query(sql_query_4, psql_conn)
bins = [0, 10, 20, 40, 60, float('inf')]
labels = ['0-10', '10-20', '20-40', '40-60', '60+']
df['ageGroup'] = pd.cut(df['birthday'].apply(lambda x: relativedelta(date.today(), x).years), bins=bins, labels=labels,
                        right=False)
print("\nQuestion 4")
print(df)
###########################################################################################

###########################################################################################
# QUESTION 5
df_vaccine['VaccineCount'] = df_vaccine[['date1', 'date2']].notnull().sum(axis=1)
vaccine_counts = df_vaccine.groupby('patientssno')['VaccineCount'].sum().astype('str')
df['VaccineCount'] = df['ssno'].map(vaccine_counts).fillna('0')
print("\nQuestion 5")
print(df)  # the dataframe used for task 6 is df
###########################################################################################

###########################################################################################
# QUESTION 8
sql_query_8 = """
WITH event_amount_info AS (SELECT v.date, vb.location, vb.amount
                           FROM vaccinations v
                                    JOIN vaccinebatch vb
                                         ON v.batchid = vb.batchid),
     event_patient_info AS (SELECT vp.date, vp.location, COUNT(*) AS total_patients
                            FROM vaccinepatients vp
                            GROUP BY vp.date, vp.location)
SELECT eai.date, eai.location, round((epi.total_patients::NUMERIC / eai.amount), 2) AS attending_percentage
FROM event_amount_info eai
         JOIN event_patient_info epi
              ON eai.date = epi.date
                  AND eai.location = epi.location;
"""
attend_percentage_df = pd.read_sql(sql_query_8, psql_conn)
print("Question 8:")
print(attend_percentage_df)

# Expected percentage of patients that will attend
mean = attend_percentage_df['attending_percentage'].mean()
print(f"\nThe expected percentage of patientss that will attend is {mean}")

# Standard deviation of the percentage of attending patients
std = attend_percentage_df['attending_percentage'].std()
print(f"The standard deviation of the percentage of attedning patients is {std}")

# The estimated amount of vaccines (as a percentage) that should be reserved for each vaccination to minimize waste
print(f"The estimated amount of vaccines (as a percentage) that should be reserved for each vaccination to minimize "
      f"waste is {mean + std}")
###########################################################################################

###########################################################################################
# QUESTION 10

def find_close_contact_people(ssno, date):
    """ This function is the generalize function of this task. It takes two arguments as inputs and return a dataframe
    contains the people that the person of interest have close contact with within 10 days from the date.

    Args:
        ssno (str): The social security number of the person of interest
        date (str): The date when the person of interest got the positive test result. It must in format "yyyy-mm-dd"

    Return:
        result_df (pd.DataFrame): A dataframe contains the ssno of the staffs and the patients that the person of
        interest may have met.
    """

    # 1. Find the staffs that the person may have met
    query_1 = f"""
    WITH vaccinations_with_weekday AS (SELECT *, REPLACE(TO_CHAR(v.date, 'Day'), ' ', '')::weekdays AS weekday
                                       FROM vaccinations v)
    SELECT s.worker
    FROM vaccinations_with_weekday vww
             JOIN shifts s
                  ON vww.location = s.station
                      AND vww.weekday = s.weekday
    WHERE (vww.date BETWEEN ('{date}'::DATE - 10) AND '{date}')
      AND (vww.location = (SELECT DISTINCT station
                           FROM shifts
                           WHERE worker = '{ssno}'));
    """

    staffs_df = pd.read_sql(query_1, psql_conn)
    staffs_df = staffs_df.rename(columns={'worker': 'ssno'})
    staffs_df['is_staff'] = True

    # 2. Find the patients that person may have met
    query_2 = f"""
    SELECT vp.patientssno
    FROM vaccinations v
             JOIN vaccinepatients vp
                  ON v.date = vp.date
                      AND v.location = vp.location
    WHERE (v.date BETWEEN ('{date}'::DATE - 10) AND '{date}')
      AND (v.location = (SELECT DISTINCT station
                         FROM shifts
                         WHERE worker = '{ssno}'));
    """

    patients_df = pd.read_sql(query_2, psql_conn)
    patients_df = patients_df.rename(columns={'patientssno': 'ssno'})
    patients_df['is_staff'] = False

    # 3. Concat these two dataframes into one dataframe
    result_df = pd.concat((staffs_df, patients_df))

    return result_df


print("\nQuestion 10: ")
print(find_close_contact_people('19740919-7140', '2021-05-15'))


connection.close()
psql_conn.close()
