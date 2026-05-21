# Viser ligatabellen for en valgt sæson .
# Henter alle tilgængelige sæsoner fra backend.
# Brugeren vælger sæson via en dropdown

import streamlit as st
import requests
import os


#Henter backend url, bruges i docker.
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("Premier League Tabel")

# Kalder /seasons endpoint og får en liste tilbage
seasons = requests.get(f"{BACKEND_URL}/seasons").json()["seasons"]

#dropdown viser alle sæsoner 
selected_season = st.selectbox("Vælg sæson", seasons)

# Hent tabel for valgt sæson. Kalder /table/{selected_season endpoint og får dictionaries tilbage
response = requests.get(f"{BACKEND_URL}/table/{selected_season}")
table = response.json()["table"]



# Tilføj placering
# Enumerate giver både index og værdi, Tabellen er allerede sorteret efter point. Så vi tilføjer bare # som 1,2,3 osv
for i, team in enumerate(table):
    team["#"] = i + 1


#Viser selve tabellen.
st.dataframe(
    table,
    column_order=["#", "team", "played", "wins", "draws", "losses", "points"], #bestemmer hvilke kolonner, der vises og i hvilken rækkefølge
    hide_index=True, #skjuler pandas index
    use_container_width=True,
)
