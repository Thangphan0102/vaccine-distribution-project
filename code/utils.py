from datetime import datetime, time, date
from dateutil.relativedelta import relativedelta
import pandas as pd


def add_vaccination_status(row):
    if row['vaccinetype1'] is not None and row['vaccinetype2'] is not None:
        return 2
    elif row['vaccinetype1'] is not None and row['vaccinetype2'] is None:
        return 1
    else:
        return 0


def find_shift(name, conn):
    query = f"""
    SELECT s.station, s.weekday
    FROM shifts s
             JOIN staffmembers sm
                  ON s.worker = sm.ssno
    WHERE sm.name = '{name}';
    """

    df = conn.query(query)

    return df


def format_list_to_sql(list_of_values):
    return str(list_of_values).replace('[', '').replace(']', '')
