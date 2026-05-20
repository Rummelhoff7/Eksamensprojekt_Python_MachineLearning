import streamlit as st
import requests
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("Premier League Tabel")

# Hent alle sæsoner
seasons = requests.get(f"{BACKEND_URL}/seasons").json()["seasons"]
selected_season = st.selectbox("Vælg sæson", seasons)

# Hent tabel for valgt sæson
response = requests.get(f"{BACKEND_URL}/table/{selected_season}")
table = response.json()["table"]

# Tilføj placering
for i, team in enumerate(table):
    team["#"] = i + 1

st.dataframe(
    table,
    column_order=["#", "team", "played", "wins", "draws", "losses", "points"],
    hide_index=True,
    use_container_width=True,
)
