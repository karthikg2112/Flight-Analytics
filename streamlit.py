import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns

#to connect to the database
def get_data(query):
    conn = sqlite3.connect('flight_data.db')
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Title
st.title("Flight Data Analysis Dashboard")  

# sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Select a page:", ["Home", "Arrival and Departure Data","Arrival & Departure Visualizations","Query Execution","Creator Info"])

#---------------- Home Page ----------------
if page == "Home":
    st.title("Flight Data Analytics Home")
    st.image("C:/Users/karth/Downloads/Code/env/Scripts/airplane-taking-off-stockcake-1.jpg")
    st.write("""
    Welcome to the Flight Data Analytics Dashboard! This application provides insights into flight operations, including arrivals and departures.
    Navigate through the sidebar to explore different sections of the dashboard.

    **Features:**
    - Detailed arrival and departure data Airport city-wise.
    - Interactive visualizations of Arrival and Departure data based on Airport city.
    - Execute predefined SQL queries on the flight database to view the results.
    - Information about the creator of this dashboard.
    """)

#---------------- Query Execution Page ----------------
elif page == "Query Execution":
    st.title("Pre defined SQL Query Execution")
    st.write("Execute predefined SQL queries on the flight database and view the results.")

    queries = {
    "1. Total number of flights for each aircraft model": """
    SELECT
        aircraft_model,
        COUNT(*) AS total_flights
    FROM (
        SELECT aircraft_model FROM new_departures_data
        UNION ALL
        SELECT aircraft_model FROM new_arrivals_data
    )
    WHERE aircraft_model IS NOT NULL
    GROUP BY aircraft_model
    ORDER BY total_flights DESC;
    """,
    "2. all aircraft (registration, model) that have been assigned to more than 5 flights": """
    SELECT
        aircraft_registration AS registration,
        aircraft_model AS model,
        COUNT(*) AS total_assignments
    FROM (
        SELECT aircraft_registration, aircraft_model FROM new_departures_data WHERE aircraft_registration IS NOT NULL
        UNION ALL
        SELECT aircraft_registration, aircraft_model FROM new_arrivals_data WHERE aircraft_registration IS NOT NULL
    )
    GROUP BY registration, model
    HAVING total_assignments > 5
    ORDER BY total_assignments DESC;
    """,
    "3. In each airport, display its name and the number of outbound flights, but only for airports with more than 5 flights.": """
    SELECT
        destination_airport_name AS airport_name,
        COUNT(*) AS outbound_flights_count
    FROM new_departures_data
    WHERE destination_airport_name IS NOT NULL AND destination_airport_name != 'Unknown'
    GROUP BY airport_name
    HAVING outbound_flights_count > 5
    ORDER BY outbound_flights_count DESC;
    """,
    "4. Top 3 destination airports (name, city) by number of arriving flights, sorted by count descending.": """
    SELECT
        ad.full_name AS destination_airport_name,
        ad.municipality_name AS destination_airport_city,
        COUNT(*) AS total_arriving_flights
    FROM new_arrivals_data na
    LEFT JOIN airports_data ad ON na.arrival_airport_iata = ad.iata_code
    WHERE ad.full_name IS NOT NULL
    GROUP BY destination_airport_name, destination_airport_city
    ORDER BY total_arriving_flights DESC
    LIMIT 3;
    """,
    "5. For each flight: number, origin, destination, and a label 'Domestic' or 'International' using CASE WHEN on country match.": """
    SELECT
        nd.flight_number AS flight_number,
        ad_orig.full_name AS origin_airport,
        ad_dest.full_name AS destination_airport,
        CASE
            WHEN ad_orig.country_name = ad_dest.country_name THEN 'Domestic'
            ELSE 'International'
        END AS flight_type
    FROM
        new_departures_data nd
    LEFT JOIN
        airports_data ad_orig ON nd.origin_airport_iata = ad_orig.iata_code
    LEFT JOIN
        airports_data ad_dest ON nd.destination_airport_iata = ad_dest.iata_code
    WHERE
        ad_orig.full_name IS NOT NULL AND ad_dest.full_name IS NOT NULL
    ORDER BY
        flight_number ASC;
    """,
    "6. 5 most recent arrivals at “DEL” airport.": """
    SELECT
        flight_number,
        aircraft_model,
        origin_airport_name AS departure_airport_name,
        scheduled_arrival_time_utc AS scheduled_arrival_time
    FROM
        new_arrivals_data
    WHERE
        arrival_airport_iata = 'DEL'
    ORDER BY
        scheduled_arrival_time DESC
    LIMIT 5;
    """,
    "7. Airports with no arriving flights": """
    SELECT
        ad.full_name AS airport_name,
        ad.iata_code AS airport_iata
    FROM
        airports_data ad
    LEFT JOIN
        new_arrivals_data na ON ad.iata_code = na.arrival_airport_iata
    WHERE
        na.arrival_airport_iata IS NULL;
    """,
    "8.For each airline, count the number of flights by status using CASE WHEN.": """
    SELECT
        airline_name,
        COUNT(CASE WHEN flight_status = 'Departed' THEN 1 ELSE NULL END) AS departed_flights,
        COUNT(CASE WHEN flight_status = 'Expected' THEN 1 ELSE NULL END) AS expected_flights,
        COUNT(CASE WHEN flight_status NOT IN ('Departed', 'Expected') THEN 1 ELSE NULL END) AS other_status_flights,
        COUNT(*) AS total_flights
    FROM
        new_departures_data
    WHERE
        airline_name IS NOT NULL
    GROUP BY
        airline_name
    ORDER BY
        total_flights DESC;
    """,
    "9.All delayed flights with details": """
    SELECT
        nd.flight_number,
        nd.aircraft_model,
        ad_origin.full_name AS origin_airport,
        ad_destination.full_name AS destination_airport,
        nd.scheduled_departure_time_utc
    FROM
        new_departures_data nd
    LEFT JOIN
        airports_data ad_origin ON nd.origin_airport_iata = ad_origin.iata_code
    LEFT JOIN
        airports_data ad_destination ON nd.destination_airport_iata = ad_destination.iata_code
    WHERE
        nd.flight_status = 'Delayed'
    ORDER BY
        nd.scheduled_departure_time_utc DESC;
    """,
    "10.All city pairs that have more than 2 different aircraft models.": """
    SELECT
        ad_orig.full_name AS origin_airport,
        ad_dest.full_name AS destination_airport,
        COUNT(DISTINCT nd.aircraft_model) AS distinct_aircraft_models
    FROM
        new_departures_data nd
    JOIN
        airports_data ad_orig ON nd.origin_airport_iata = ad_orig.iata_code
    JOIN
        airports_data ad_dest ON nd.destination_airport_iata = ad_dest.iata_code
    WHERE
        nd.aircraft_model IS NOT NULL
    GROUP BY
        origin_airport,
        destination_airport
    HAVING
        COUNT(DISTINCT nd.aircraft_model) > 2
    ORDER BY
        distinct_aircraft_models DESC;
    """,
    "11. percentage of delayed flights for each destination airport": """
    SELECT
        ad.full_name AS destination_airport_name,
        SUM(CASE WHEN na.flight_status = 'Delayed' THEN 1 ELSE 0 END) AS delayed_arrivals_count,
        COUNT(na.flight_number) AS total_arrivals_count,
        CAST(SUM(CASE WHEN na.flight_status = 'Delayed' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(na.flight_number) AS percentage_delayed
    FROM
        new_arrivals_data na
    JOIN
        airports_data ad ON na.arrival_airport_iata = ad.iata_code -- Corrected column name to 'arrival_airport_iata'
    GROUP BY
        ad.full_name
    HAVING
        total_arrivals_count > 0
    ORDER BY
        percentage_delayed DESC;
    """
    }
    selected_query = st.selectbox("Select a SQL query to execute:", list(queries.keys()))
    if selected_query:
        query = queries[selected_query]
        df_result = get_data(query)
        st.write("Query Result:")
        st.dataframe(df_result)

#---------------- Arrival and Departure Data with respect to Airport city ----------------
elif page == "Arrival and Departure Data":
    st.title("Arrival and Departure Data with respect to Airport city")
    st.write("View arrival and departure data for a specific airport city.")

    airport_city = st.selectbox("Select an Airport City:", {municipality for municipality in pd.read_sql_query("SELECT DISTINCT municipality_name FROM airports_data WHERE municipality_name IS NOT NULL;", sqlite3.connect('flight_data.db'))['municipality_name']})


    if airport_city:        
        query_arrivals = f"""
        SELECT
            na.flight_number,
            na.aircraft_model,
            ad_origin.full_name AS origin_airport,
            ad_dest.full_name AS destination_airport,
            na.scheduled_arrival_time_utc AS scheduled_arrival_time,
            na.flight_status
        FROM
            new_arrivals_data na
        LEFT JOIN
            airports_data ad_origin ON na.origin_airport_iata = ad_origin.iata_code
        LEFT JOIN
            airports_data ad_dest ON na.arrival_airport_iata = ad_dest.iata_code
        WHERE
            ad_dest.municipality_name = '{airport_city}' AND ad_origin.full_name IS NOT NULL
        ORDER BY
            na.scheduled_arrival_time_utc DESC;
        """
        query_departures = f"""
        SELECT
            nd.flight_number,
            nd.aircraft_model,
            ad_origin.full_name AS origin_airport,
            ad_dest.full_name AS destination_airport,
            nd.scheduled_departure_time_utc AS scheduled_departure_time,
            nd.flight_status
        FROM
            new_departures_data nd
        LEFT JOIN
            airports_data ad_origin ON nd.origin_airport_iata = ad_origin.iata_code
        LEFT JOIN
            airports_data ad_dest ON nd.destination_airport_iata = ad_dest.iata_code
        WHERE
            ad_dest.municipality_name = '{airport_city}'
        ORDER BY
            nd.scheduled_departure_time_utc DESC;
        """

        df_departures = get_data(query_departures)
        df_arrivals = get_data(query_arrivals)
        st.subheader(f"Departures to {airport_city}")
        st.dataframe(df_departures)
        st.subheader(f"Arrivals to {airport_city}")
        st.dataframe(df_arrivals)


#---------------- Arrival & Departure Visualizations Page ----------------
elif page == "Arrival & Departure Visualizations":
    st.title("Arrival & Departure Visualizations")
    st.write("Visualize flight data with interactive charts.")

    departure_city_viz = st.selectbox("Select a Departure City for Visualization:", {municipality for municipality in pd.read_sql_query("SELECT DISTINCT municipality_name FROM airports_data WHERE municipality_name IS NOT NULL;", sqlite3.connect('flight_data.db'))['municipality_name']})

    if departure_city_viz:
        query_viz = f"""
        SELECT
            nd.flight_status,
            COUNT(*) AS count
        FROM
            new_departures_data nd
        LEFT JOIN
            airports_data ad_orig ON nd.origin_airport_iata = ad_orig.iata_code
        WHERE
            ad_orig.municipality_name = '{departure_city_viz}'
        GROUP BY
            nd.flight_status;
        """
        df_viz = get_data(query_viz)

    # Bar chart
        st.subheader(f"Flight Departure Status Plot for {departure_city_viz}")
        fig, ax = plt.subplots()
        sns.barplot(data=df_viz, x='flight_status', y='count', ax=ax)
        ax.set_xlabel("Flight Status")
        ax.set_ylabel("Count")
        ax.set_title(f"Flight Departure Status Plot for {departure_city_viz}")
        st.pyplot(fig)

    airport_city_viz = st.selectbox("Select an Arrival City for Visualization:", {municipality for municipality in pd.read_sql_query("SELECT DISTINCT municipality_name FROM airports_data WHERE municipality_name IS NOT NULL;", sqlite3.connect('flight_data.db'))['municipality_name']})

    if airport_city_viz:
        query_viz = f"""
        SELECT
            na.flight_status,
            COUNT(*) AS count
        FROM
            new_arrivals_data na
        LEFT JOIN
            airports_data ad_dest ON na.arrival_airport_iata = ad_dest.iata_code
        WHERE
            ad_dest.municipality_name = '{airport_city_viz}'
        GROUP BY
            na.flight_status;
        """
        df_viz = get_data(query_viz)

    # Bar chart
        st.subheader(f"Flight Arrival Status Plot for {airport_city_viz}")
        fig, ax = plt.subplots()
        sns.barplot(data=df_viz, x='flight_status', y='count', ax=ax)
        ax.set_xlabel("Flight Status")
        ax.set_ylabel("Count")
        ax.set_title(f"Flight Arrival Status Plot for {airport_city_viz}")
        st.pyplot(fig)


#---------------- Creator Info Page ----------------
elif page == "Creator Info":
    st.title("Creator Information")
    st.image("C:/Users/karth/Downloads/Code/env/Scripts/Profile-Pic.jpeg", width=200)
    st.write("""
    **Name:** Karthik G 
    **Email:** karthikg2112@gmail.com
    **GitHub:** [karthikg2112](https://github.com/karthikg2112)
    **LinkedIn:** [Karthik G](https://www.linkedin.com/in/karthik-g-620760369?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=android_app)
    """
    )
