import streamlit as st
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import pydeck as pdk

from utils import *

# Config
st.set_page_config(
    page_title="Vaccine distribution",
    page_icon=":syringe:",
    layout="wide"
)

# Connect to database
conn = st.experimental_connection('postgres', type='sql')

# Title
st.title("Data visualization")

# First chart
with st.container():
    st.subheader("Cumulative number of vaccinated people")

    query = """
    SELECT t1.date as date, num_of_vaccinated, num_of_fully_vaccinated
    FROM (SELECT date1 AS date, COUNT(date1) AS num_of_vaccinated
          FROM "PatientVaccineInfo"
          GROUP BY date1
          ORDER BY date1) t1
             left JOIN (SELECT date2 AS date, COUNT(date2) AS num_of_fully_vaccinated
                   FROM "PatientVaccineInfo"
                   GROUP BY date2
                   ORDER BY date2) t2
    ON t1.date = t2.date;
    """

    df = conn.query(query)
    df = df.fillna(0)
    df['cumsum_num_of_vaccinated'] = df['num_of_vaccinated'].cumsum()
    df['cumsum_num_of_fully_vaccinated'] = df['num_of_fully_vaccinated'].cumsum()
    df['date'] = pd.to_datetime(df['date'])

    start_date, end_date = st.select_slider(
        "Select a range",
        options=df['date'].drop_duplicates().sort_values(),
        value=(df['date'].drop_duplicates().min(), df['date'].drop_duplicates().max()),
        format_func=lambda x: datetime.strftime(x, "%d %b, %Y")
    )

    df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        value = int(df.iloc[-1]['cumsum_num_of_vaccinated'])
        delta = 0
        if len(df) >= 2:
            delta = int(df.iloc[-1]['cumsum_num_of_vaccinated'] - df.iloc[-2]['cumsum_num_of_vaccinated'])
        st.metric("Total of vaccinated people", value, delta)

    with col2:
        population = conn.query("SELECT COUNT(*) FROM patients;").iloc[0, 0]
        proportion = round(value / population * 100, 2)
        delta_proportion = 0
        if len(df) >= 2:
            delta_proportion = round(delta / population * 100, 2)

        st.metric("Proportion to population (vaccinated)", f"{proportion:.1f}%", f"{delta_proportion:.1f}%")

    with col3:
        value = int(df.iloc[-1]['cumsum_num_of_fully_vaccinated'])
        delta = 0
        if len(df) >= 2:
            delta = int(df.iloc[-1]['cumsum_num_of_fully_vaccinated'] - df.iloc[-2]['cumsum_num_of_fully_vaccinated'])
        st.metric("Total of fully vaccinated people", value, delta)

    with col4:
        population = conn.query("SELECT COUNT(*) FROM patients;").iloc[0, 0]
        proportion = round(value / population * 100, 2)
        delta_proportion = 0
        if len(df) >= 2:
            delta_proportion = round(delta / population * 100, 2)

        st.metric("Proportion to population (fully vaccinated)", f"{proportion:.1f}%", f"{delta_proportion:.1f}%")

    df = df.melt(id_vars=['date'], value_vars=['cumsum_num_of_vaccinated', 'cumsum_num_of_fully_vaccinated'])

    fig = px.line(df, x='date', y='value', color='variable', markers='dot')
    fig.update_layout(
        legend=dict(
            y=0.99,
            x=0.01
        )
    )
    st.plotly_chart(fig, use_container_width=True)


# Horizontal line
st.divider()

# Second chart
with st.container():
    st.subheader("Vaccine allocation")

    query = """
    SELECT mf.vaccine, COUNT(*)
    FROM vaccinepatients vp
             JOIN vaccinations v
                  ON vp.date = v.date AND vp.location = v.location
             JOIN vaccinebatch vb
                  ON v.batchid = vb.batchid
             JOIN manufacturer mf
                  ON vb.manufacturer = mf.id
    GROUP BY mf.vaccine;
    """

    df = conn.query(query)

    tab1, tab2 = st.tabs(["Bar", "Pie"])

    with tab1:
        fig = px.bar(df, x='vaccine', y='count', color='vaccine', category_orders={'vaccine': ['V01', 'V02', 'V03']})
        st.plotly_chart(fig)

    with tab2:
        fig = px.pie(df, names='vaccine', values='count', color='vaccine',
                     category_orders={'vaccine': ['V01', 'V02', 'V03']})
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig)

# Horizontal line
st.divider()

# Third chart
with st.container():
    st.subheader("Vaccination status")

    query = """
    SELECT p.*, pvi.vaccinetype1, pvi.vaccinetype2
    FROM patients p
        LEFT JOIN "PatientVaccineInfo" pvi
            ON p.ssno = pvi.patientssno;
    """

    df = conn.query(query)
    bins = [0, 10, 20, 40, 60, float('inf')]
    labels = ['0-10', '10-20', '20-40', '40-60', '60+']
    df['ageGroup'] = pd.cut(df['birthday'].apply(lambda x: relativedelta(date.today(), x).years), bins=bins,
                            labels=labels,
                            right=False)
    df['status'] = df.apply(add_vaccination_status, axis=1).astype('category')

    tab1, tab2 = st.tabs(["By age group", "By gender group"])

    with tab1:
        df_groupby_age = df.groupby(['ageGroup', 'status'], as_index=False).count()
        df_groupby_age = df_groupby_age.merge(
            df_groupby_age[['ageGroup', 'ssno']].groupby(['ageGroup'], as_index=False).sum(), on='ageGroup'
        )
        df_groupby_age = df_groupby_age.rename(columns={'ssno_x': "number_of_people",
                                                        'ssno_y': "total_number_of_people"})
        df_groupby_age['proportion'] = df_groupby_age['number_of_people'] / df_groupby_age[
            'total_number_of_people'] * 100
        df_groupby_age['proportion'] = df_groupby_age['proportion'].fillna(0)

        kind = st.radio("Show", ('Number of people', 'Proportion of people'), key='age', horizontal=True)

        if kind == "Number of people":
            fig = px.bar(df_groupby_age, x='ageGroup', y='number_of_people', color='status')
            st.plotly_chart(fig)
        else:
            fig = px.bar(df_groupby_age, x='ageGroup', y='proportion', color='status')
            st.plotly_chart(fig)

    with tab2:
        df_groupby_gender = df.groupby(['gender', 'status'], as_index=False).agg({'ssno': 'count'})
        df_groupby_gender = df_groupby_gender.merge(
            df_groupby_gender[['gender', 'ssno']].groupby(['gender']).sum(), on='gender'
        )
        df_groupby_gender = df_groupby_gender.rename(columns={'ssno_x': 'number_of_people',
                                                              'ssno_y': 'total_number_of_people'})
        df_groupby_gender['proportion'] = \
            df_groupby_gender['number_of_people'] / df_groupby_gender['total_number_of_people'] * 100

        kind = st.radio("Show", ('Number of people', 'Proportion of people'), key='gender', horizontal=True)

        if kind == "Number of people":
            fig = px.bar(df_groupby_gender, x='gender', y='number_of_people', color='status')
            st.plotly_chart(fig)
        else:
            fig = px.bar(df_groupby_gender, x='gender', y='proportion', color='status')
            st.plotly_chart(fig)

# Shift finder
with st.container():

    st.subheader("Find the shifts here")

    tab3, tab4 = st.tabs(['By worker', 'By station and weekday'])

    with tab3:
        ssno = st.text_input("Enter your social security number:")

        if ssno:
            df = find_shift(ssno, conn)

            if len(df) == 0:
                st.markdown(f'Couldn\'t find any shifts for person with the social security number "{ssno}"')
            else:
                st.dataframe(df, width=600, hide_index=True)

    with tab4:
        available_stations = conn.query("SELECT DISTINCT station FROM shifts;")

        station_options = st.multiselect(
            "Select your working station",
            available_stations,
            []
        )

        weekday_options = st.multiselect(
            "Select your working day",
            ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'),
            []
        )

        if station_options and weekday_options:
            query = f"""
                    SELECT *
                    FROM shifts
                        WHERE station IN ({format_list_to_sql(station_options)})
                            AND weekday IN ({format_list_to_sql(weekday_options)});
                    """

            st.dataframe(conn.query(query), width=600, hide_index=True)

# Horizontal line
st.divider()

# Map
with st.container():
    st.subheader("Health station map")
    df = conn.query("SELECT * FROM healthstation;")

    fig = px.scatter_mapbox(df, lat='lat', lon='lon', hover_name='station', zoom=9)
    fig.update_layout(mapbox_style='carto-positron')
    st.plotly_chart(fig, use_container_width=True)
