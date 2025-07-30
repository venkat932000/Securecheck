import streamlit as st
import pandas as pd
from tabulate import tabulate
import mysql.connector

# Connect to MySQL
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="securecheck"
)
mycursor = mydb.cursor(buffered=True)

st.title("SecureCheck Dashboard")

# Query options
query_options = [
    "Top 10 vehicle numbers involved in drug-related stops",
    "Vehicles most frequently searched",
    "Driver age group with highest arrest rate",
    "Gender distribution of drivers stopped in each country",
    "Race and gender combination with highest search rate",
    "Time of day with most traffic stops",
    "Average stop duration for different violations",
    "Are stops during the night more likely to lead to arrests?",
    "Violations most associated with searches or arrests",
    "Violations most common among younger drivers (<25)",
    "Violation that rarely results in search or arrest",
    "Countries with highest rate of drug-related stops",
    "Arrest rate by country and violation",
    "Country with most stops with search conducted",
    "Yearly breakdown of stops and arrests by country",
    "Driver violation trends based on age and race",
    "Time period analysis of stops",
    "Violations with high search and arrest rates",
    "Driver demographics by country",
    "Top 5 violations with highest arrest rates"
]

selected_query = st.selectbox("Select a query to view:", query_options)

query_dict = {
    query_options[0]: "SELECT vehicle_number, COUNT(*) AS drug_stop_count FROM ledger WHERE drugs_related_stop = 'Yes' GROUP BY vehicle_number ORDER BY drug_stop_count DESC LIMIT 10;",
    query_options[1]: "SELECT vehicle_number, COUNT(*) AS search_count FROM ledger WHERE search_conducted = 'Yes' GROUP BY vehicle_number ORDER BY search_count DESC LIMIT 10;",
    query_options[2]: "SELECT driver_age, ROUND(AVG(is_arrested = 'Yes') * 100, 2) AS arrest_rate FROM ledger GROUP BY driver_age ORDER BY arrest_rate DESC LIMIT 1;",
    query_options[3]: "SELECT country_name, driver_gender, COUNT(*) AS total_stops FROM ledger GROUP BY country_name, driver_gender;",
    query_options[4]: "SELECT driver_race, driver_gender, ROUND(AVG(search_conducted = 'Yes') * 100, 2) AS search_rate FROM ledger GROUP BY driver_race, driver_gender ORDER BY search_rate DESC LIMIT 1;",
    query_options[5]: "SELECT stop_time, COUNT(*) AS stop_count FROM ledger GROUP BY stop_time ORDER BY stop_count DESC LIMIT 1;",
    query_options[6]: "SELECT violation, AVG(CAST(SUBSTRING_INDEX(stop_duration, ' ', 1) AS UNSIGNED)) AS avg_duration FROM ledger GROUP BY violation;",
    query_options[7]: "SELECT CASE WHEN HOUR(stop_time) BETWEEN 20 AND 6 THEN 'Night' ELSE 'Day' END AS period, ROUND(AVG(is_arrested = 'Yes') * 100, 2) AS arrest_rate FROM ledger GROUP BY period;",
    query_options[8]: "SELECT violation, ROUND(AVG(search_conducted = 'Yes') * 100, 2) AS search_rate, ROUND(AVG(is_arrested = 'Yes') * 100, 2) AS arrest_rate FROM ledger GROUP BY violation ORDER BY search_rate DESC, arrest_rate DESC;",
    query_options[9]: "SELECT violation, COUNT(*) AS count FROM ledger WHERE driver_age < 25 GROUP BY violation ORDER BY count DESC LIMIT 5;",
    query_options[10]: "SELECT violation, ROUND(AVG(search_conducted = 'Yes') * 100, 2) AS search_rate, ROUND(AVG(is_arrested = 'Yes') * 100, 2) AS arrest_rate FROM ledger GROUP BY violation ORDER BY search_rate, arrest_rate LIMIT 1;",
    query_options[11]: "SELECT country_name, COUNT(*) AS drug_related_count FROM ledger WHERE drugs_related_stop = 'Yes' GROUP BY country_name ORDER BY drug_related_count DESC;",
    query_options[12]: "SELECT country_name, violation, ROUND(AVG(is_arrested = 'Yes') * 100, 2) AS arrest_rate FROM ledger GROUP BY country_name, violation ORDER BY arrest_rate DESC;",
    query_options[13]: "SELECT country_name, COUNT(*) AS search_count FROM ledger WHERE search_conducted = 'Yes' GROUP BY country_name ORDER BY search_count DESC;",
    query_options[14]: "SELECT stop_year, country_name, total_stops, total_arrests, ROUND(total_arrests / total_stops * 100, 2) AS arrest_rate FROM (SELECT YEAR(stop_date) AS stop_year, country_name, COUNT(*) AS total_stops, SUM(is_arrested = 'Yes') AS total_arrests FROM ledger GROUP BY stop_year, country_name) AS yearly_data;",
    query_options[15]: "SELECT v.driver_age, v.driver_race, v.violation, v.violation_count FROM (SELECT driver_age, driver_race, violation, COUNT(*) AS violation_count FROM ledger GROUP BY driver_age, driver_race, violation) v;",
    query_options[16]: "SELECT CASE WHEN HOUR(stop_time) BETWEEN 6 AND 12 THEN 'Morning' WHEN HOUR(stop_time) BETWEEN 12 AND 18 THEN 'Afternoon' WHEN HOUR(stop_time) BETWEEN 18 AND 24 THEN 'Evening' ELSE 'Night' END AS time_period, COUNT(*) AS stop_count FROM ledger GROUP BY time_period ORDER BY stop_count DESC;",
    query_options[17]: "SELECT violation, search_rate, arrest_rate FROM (SELECT violation, ROUND(AVG(search_conducted = 'Yes') * 100, 2) AS search_rate, ROUND(AVG(is_arrested = 'Yes') * 100, 2) AS arrest_rate, RANK() OVER (ORDER BY AVG(search_conducted = 'Yes') DESC) AS search_rank FROM ledger GROUP BY violation) AS ranked WHERE search_rank <= 5",
    query_options[18]: "SELECT country_name, AVG(driver_age) AS avg_age, COUNT(DISTINCT driver_gender) AS gender_diversity, COUNT(DISTINCT driver_race) AS race_diversity FROM ledger GROUP BY country_name;",
    query_options[19]: "SELECT violation, ROUND(AVG(is_arrested = 'Yes') * 100, 2) AS arrest_rate FROM ledger GROUP BY violation ORDER BY arrest_rate DESC LIMIT 5;"
}

if st.button("Run Query"):
    query = query_dict[selected_query]
    mycursor.execute(query)
    out = mycursor.fetchall()
    columns = [i[0] for i in mycursor.description]
    df = pd.DataFrame(out, columns=columns)
    st.dataframe(df)
    st.markdown("### Query Result")

# Prediction Section
st.header("Predict Arrest Probability")

# Load data for prediction options
@st.cache_data
def load_prediction_data():
    # Get unique values for each dropdown
    mycursor.execute("SELECT DISTINCT country_name FROM ledger")
    countries = [row[0] for row in mycursor.fetchall()]
    
    mycursor.execute("SELECT DISTINCT driver_gender FROM ledger")
    genders = [row[0] for row in mycursor.fetchall()]
    
    mycursor.execute("SELECT DISTINCT driver_race FROM ledger")
    races = [row[0] for row in mycursor.fetchall()]
    
    mycursor.execute("SELECT DISTINCT violation FROM ledger")
    violations = [row[0] for row in mycursor.fetchall()]
    
    return countries, genders, races, violations

countries, genders, races, violations = load_prediction_data()

# Create selectboxes with actual data
stop_date   = st.selectbox("stop_date", pd.date_range(start="2020-01-01", end="2023-12-31").strftime("%Y-%m-%d").tolist())
stop_time  = st.selectbox("stop_time ", pd.date_range(start="00:00", end="23:59", freq='H').strftime("%H:%M").tolist())
country = st.selectbox("Country", countries)
gender = st.selectbox("Driver Gender", genders)
age = st.number_input("Driver Age", min_value=16, max_value=100, value=30)
race = st.selectbox("Driver Race", races)
was_search_conducted = st.selectbox("Search Type", ["Yes", "No"])
was_it_drug_related = st.selectbox("Was it drug related?", ["Yes", "No"])
stop_duration = st.number_input("Stop Duration (minutes)", min_value=1, max_value=120, value=10)
vehicle_number = st.text_input("Vehicle Number", "")
violation = st.selectbox("Violation", violations)

if st.button("Predict"):
    # Query to get historical arrest rate for similar records
    query = """
    SELECT AVG(is_arrested = 'Yes') AS arrest_probability
    FROM ledger
    WHERE country_name = %s
      AND driver_gender = %s
      AND driver_race = %s
      AND driver_age = %s
      AND violation = %s
    """
    
    mycursor.execute(query, (country, gender, race, age, violation))
    result = mycursor.fetchone()
    
    if result and result[0] is not None:
        prob = result[0]
        st.success(f"Estimated arrest probability: {prob:.2%}")
    else:
        st.warning("No matching records found for prediction.")
