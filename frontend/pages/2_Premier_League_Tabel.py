# Viser ligatabellen for en valgt sæson .
# Henter alle tilgængelige sæsoner fra backend.
# Brugeren vælger sæson via en dropdown

import streamlit as st #Streamlit framework til frontend
import requests #HTTP request til backend
import pandas as pd #style tabel
import os ##Læser backend env til docker



#Henter backend url, bruges i docker.
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("Premier League Tabel")

# Cacher sæsoner og tabel i 1 time
@st.cache_data(ttl=3600)
def get_seasons():
    return requests.get(f"{BACKEND_URL}/seasons").json()["seasons"]

@st.cache_data(ttl=3600)
def get_table(season: str):
    return requests.get(f"{BACKEND_URL}/table/{season}").json()["table"]


# Kalder /seasons endpoint og får en liste tilbage
seasons = get_seasons()

#dropdown viser alle sæsoner
selected_season = st.selectbox("Vælg sæson", seasons)

# Hent tabel for valgt sæson
table = get_table(selected_season)

# Tilføj placering
# Enumerate giver både index og værdi, Tabellen er allerede sorteret efter point. Så vi tilføjer bare # som 1,2,3 osv
for i, team in enumerate(table):
    team["#"] = i + 1

df = pd.DataFrame(table)

# Forklaring af farvemarkering
st.caption("🔵 Top 4 — Champions League &nbsp;&nbsp; 🟠 5. plads — Europa League &nbsp;&nbsp; 🟢 6. plads — Conference League &nbsp;&nbsp; 🔴 18.-20. — Nedrykning")

# Farver rækker baseret på placering i Premier League
def highlight_position(row):
    pos = row["#"]
    if pos <= 4:
        return ["background-color: #1a3a5c"] * len(row)  # Champions League — blå
    elif pos == 5:
        return ["background-color: #4a3000"] * len(row)  # Europa League — orange
    elif pos == 6:
        return ["background-color: #2a3a1a"] * len(row)  # Conference League — grøn
    elif pos >= len(df) - 2:
        return ["background-color: #5c1a1a"] * len(row)  # Nedrykning — rød
    else:
        return [""] * len(row)

styled = df.style.apply(highlight_position, axis=1)

#Viser selve tabellen med farvemarkering
st.dataframe(
    styled,
    column_order=["#", "team", "played", "wins", "draws", "losses", "gf", "ga", "gd", "points"],
    hide_index=True,
    use_container_width=True,
)
