import streamlit as st
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import plotly.graph_objects as go

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
st.title("Dashboard :bar_chart:")


# First chart
with st.container():
    st.subheader("Cumulative number of vaccinated people")

    query = """
    SELECT t1.date AS date, num_of_vaccinated, num_of_fully_vaccinated
    FROM (SELECT date1 AS date, COUNT(date1) AS num_of_vaccinated
          FROM "PatientVaccineInfo"
          GROUP BY date1
          ORDER BY date1) t1
             LEFT JOIN (SELECT date2 AS date, COUNT(date2) AS num_of_fully_vaccinated
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
        ),
        legend_title_text='',
        xaxis_title='Date',
        yaxis_title='Cumulative number of people',
    )
    new_names = {'cumsum_num_of_vaccinated': 'Vaccinated people',
                 'cumsum_num_of_fully_vaccinated': 'Fully vaccinated people'}
    fig.for_each_trace(lambda t: t.update(name=new_names[t.name],
                                          hovertemplate=t.hovertemplate.replace(t.name, new_names[t.name])))
    st.plotly_chart(fig, use_container_width=True)

# Horizontal line
st.divider()

# Vaccine allocation
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
        fig = px.bar(
            df,
            x='vaccine',
            y='count',
            color='vaccine',
            category_orders={'vaccine': ['V01', 'V02', 'V03']},
            text_auto=True
        )
        fig.update_layout(
            xaxis_title='Vaccine type',
            yaxis_title='Number of people',
            legend_title='Vaccine type'
        )
        st.plotly_chart(fig)

    with tab2:
        fig = px.pie(df, names='vaccine', values='count', color='vaccine',
                     category_orders={'vaccine': ['V01', 'V02', 'V03']})
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            legend_title='Vaccine type'
        )
        st.plotly_chart(fig)

# Horizontal line
st.divider()

# Vaccination status of patients
with st.container():
    st.subheader("Vaccination status of patients")
    st.markdown("*We assume that patients' status is the number of dose(s) that they took*")

    query = """
    SELECT p.*, pvi.vaccinetype1, pvi.vaccinetype2
    FROM patients p
        LEFT JOIN "PatientVaccineInfo" pvi
            ON p.ssno = pvi.patientssno;
    """

    df = conn.query(query)
    bins = [0, 10, 20, 40, 60, float('inf')]
    labels = ['0-10', '11-20', '22-40', '41-60', '60+']
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
            fig.update_layout(
                xaxis_title='Age group',
                yaxis_title='Number of people',
                legend_title='Status'
            )
            st.plotly_chart(fig)
        else:
            fig = px.bar(df_groupby_age, x='ageGroup', y='proportion', color='status')
            fig.update_layout(
                xaxis_title='Age group',
                yaxis_title='Proportion',
                legend_title='Status'
            )
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
            fig.update_layout(
                xaxis_title='Age group',
                yaxis_title='Number of people',
                legend_title='Status'
            )
            st.plotly_chart(fig)
        else:
            fig = px.bar(df_groupby_gender, x='gender', y='proportion', color='status')
            fig.update_layout(
                xaxis_title='Age group',
                yaxis_title='Proportion',
                legend_title='Status'
            )
            st.plotly_chart(fig)

# Horizontal line
st.divider()

# Vaccination status of staffs
with st.container():
    st.subheader("Vaccination status of staffs")
    st.markdown("*We assume that staffs' status is (1) if he/she is fully vaccinated or (0) if he/she hasn't received "
                "any vaccination*")

    df = conn.query("SELECT * FROM staffmembers;")
    df['status'] = df['status'].astype('category')
    bins = [0, 10, 20, 40, 60, float('inf')]
    labels = ['0-10', '11-20', '22-40', '41-60', '60+']
    df['ageGroup'] = pd.cut(df['birthday'].apply(lambda x: relativedelta(date.today(), x).years), bins=bins,
                            labels=labels,
                            right=False)
    df = df.groupby(['ageGroup', 'status'], as_index=False).count().loc[:, ['ageGroup', 'status', 'ssno']]
    df = df.merge(df[['ageGroup', 'ssno']].groupby(['ageGroup'], as_index=False).sum(), on='ageGroup')
    df = df.rename(columns={'ssno_x': "number_of_people",
                            'ssno_y': "total_number_of_people"})
    df['proportion'] = df['number_of_people'] / df['total_number_of_people'] * 100
    df['proportion'] = df['proportion'].fillna(0)

    kind = st.radio("Show", ('Number of people by age group', 'Proportion of people by age group'), key='staff_age',
                    horizontal=True)

    if kind == "Number of people by age group":
        fig = px.bar(df, x='ageGroup', y='number_of_people', color='status')
        fig.update_layout(
            xaxis_title='Age group',
            yaxis_title='Number of people',
            legend_title='Status'
        )
        st.plotly_chart(fig)
    else:
        fig = px.bar(
            df,
            x='ageGroup',
            y='proportion',
            color='status')
        fig.update_layout(
            xaxis_title='Age group',
            yaxis_title='Proportion',
            legend_title='Status'
        )
        st.plotly_chart(fig)

# Horizontal line
st.divider()

# Diagnosis chart
with st.container():
    st.subheader("Symptoms chart")

    #
    query = """
    SELECT d.symptom, COUNT(*) AS cases
    FROM diagnosis d
    GROUP BY d.symptom;
    """
    df_general = conn.query(query)

    #
    query = """
    WITH symptom_report AS (SELECT DISTINCT vp.patientssno,
                                        d.symptom,
                                        d.date  AS recorded_date,
                                        vp.date AS vaccination_date,
                                        vp.location
                        FROM diagnosis d
                                 JOIN vaccinepatients vp
                                      ON d.date >= vp.date
                                          AND d.patient = vp.patientssno
                                 JOIN vaccinatedpatients vdp
                                      ON vdp.ssno = vp.patientssno
                        WHERE vdp.vaccinationStatus = 0
                        UNION
                        SELECT *
                        FROM (SELECT DISTINCT vp.patientssno,
                                              d.symptom,
                                              d.date                                          AS recorded_date,
                                              MAX(vp.date) OVER (PARTITION BY vp.patientssno) AS vaccination_date,
                                              vp.location
                              FROM diagnosis d
                                       JOIN vaccinepatients vp
                                            ON d.patient = vp.patientssno
                                       JOIN vaccinatedpatients vdp
                                            ON vdp.ssno = vp.patientssno
                              WHERE vdp.vaccinationStatus = 1) dvv
                        WHERE dvv.recorded_date >= dvv.vaccination_date)
    SELECT symptom, COUNT(*) AS cases
    FROM symptom_report
    GROUP BY symptom;
    """
    df_vaccine = conn.query(query)

    #
    df_symptom = conn.query("SELECT * FROM symptoms;")

    df = df_general.merge(df_vaccine, on='symptom', suffixes=['_general', '_vaccine'])
    df = df.merge(df_symptom, left_on='symptom', right_on='name').drop(columns='name')
    df['criticality'] = df['criticality'].astype('bool')

    _hovertemplate = '<b>Symptom: %{x}</b>' + '<br>Cases: %{y}'

    fig = go.Figure(data=[
        go.Bar(name='General', x=df.loc[~df['criticality'], 'symptom'], y=df.loc[~df['criticality'], 'cases_general'],
               marker={'color': '#285AC2'}, legendgroup='not-critical', legendgrouptitle_text='Not critical',
               hovertemplate=_hovertemplate),
        go.Bar(name='Vaccine', x=df.loc[~df['criticality'], 'symptom'], y=df.loc[~df['criticality'], 'cases_vaccine'],
               marker={'color': '#87BFFF'}, legendgroup='not-critical', legendgrouptitle_text='Not critical',
               hovertemplate=_hovertemplate),
        go.Bar(name='General', x=df.loc[df['criticality'], 'symptom'], y=df.loc[df['criticality'], 'cases_general'],
               marker={'color': '#EB3E2D'}, legendgroup='critical', legendgrouptitle_text='Critical',
               hovertemplate=_hovertemplate),
        go.Bar(name='Vaccine', x=df.loc[df['criticality'], 'symptom'], y=df.loc[df['criticality'], 'cases_vaccine'],
               marker={'color': '#FF7A74'}, legendgroup='critical',
               hovertemplate=_hovertemplate),
    ])

    fig.update_layout(legend=dict(
        orientation='h',
        y=1.02,
        yanchor='bottom',
        x=0.5,
        xanchor='center'
    ))

    st.plotly_chart(fig, use_container_width=True)

# Horizontal line
st.divider()

# Map
with st.container():
    st.subheader("Health station map")
    df = conn.query("SELECT * FROM healthstation;")

    fig = px.scatter_mapbox(df, lat='lat', lon='lon', hover_name='station', zoom=10)
    fig.update_layout(mapbox_style='carto-positron',
                      mapbox_bounds={"west": 18, "east": 33, "south": 59.5, "north": 70.5},
                      height=1000)
    st.plotly_chart(fig, use_container_width=True)

# Horizontal line
st.divider()

# Shift finder
with st.container():
    st.subheader("Find the shifts")

    tab3, tab4 = st.tabs(['By worker', 'By station and weekday'])

    with tab3:
        staff_name = st.text_input("Enter your name:")

        if staff_name:
            df = find_shift(staff_name, conn)

            if len(df) == 0:
                st.error(f'Couldn\'t find any shifts of "{staff_name}"', icon="❌")
            else:
                st.success(f'Founded the shifts for "{staff_name}"', icon="✔")
                st.dataframe(df, width=600, hide_index=True)

    with tab4:
        available_stations = conn.query("SELECT DISTINCT station FROM shifts;")

        station_option = st.selectbox(
            "Select your working station",
            available_stations,
        )

        weekday_options = st.multiselect(
            "Select your working day(s)",
            ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'),
            []
        )

        if station_option and weekday_options:
            query = f"""
                    SELECT s.station, s.weekday, sm.name
                    FROM shifts s 
                        JOIN staffmembers sm
                            ON s.worker = sm.ssno
                        WHERE station = '{station_option}'
                            AND weekday IN ({format_list_to_sql(weekday_options)})
                        ORDER BY s.weekday;
                    """

            st.dataframe(conn.query(query), width=600, hide_index=True)

# Horizontal line
st.divider()

# Find transportation log
with st.container():
    st.subheader("Find the transportation log")

    arrival_info_query = """
    WITH cte AS (SELECT *
             FROM (SELECT *, MAX(tl.datearr) OVER (PARTITION BY tl.batchid) AS last_date
                   FROM transportationlog tl) t1
             WHERE t1.last_date = t1.datearr)
    SELECT vb.batchid, vb.location, cte.arrival
    FROM cte
    RIGHT JOIN vaccinebatch vb
    ON cte.batchid = vb.batchid;
    """

    arrival_info_df = conn.query(arrival_info_query)
    arrival_info_df['status'] = arrival_info_df['location'] == arrival_info_df['arrival']
    arrival_info_df = arrival_info_df.set_index('batchid')

    batchid = st.text_input("Enter the vaccine batch ID:")
    if batchid:
        query = f"""
        SELECT *
        FROM transportationlog
        WHERE batchid = '{batchid}';
        """

        df = conn.query(query)

        if len(df) > 0:
            st.success(f'Founded the transportation log for "{batchid}"', icon="✔")
            st.dataframe(df, hide_index=True, width=600)
            if not arrival_info_df.loc[f'{batchid}', 'status']:
                st.warning(f'The vaccine batch "{batchid}" has not yet arrived at the right destination! '
                           f'(The last arrival destination is different from the current location)', icon="❗")

        else:
            st.error(f'Couldn\'t find the transportation log for "{batchid}"', icon="❌")
