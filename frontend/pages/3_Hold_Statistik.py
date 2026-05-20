import streamlit as st
import requests
import os
import matplotlib.pyplot as plt

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("Hold Statistik")

TEAM_LOGOS = {
    "Arsenal":        "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg",
    "Aston Villa":    "https://r2.thesportsdb.com/images/media/team/badge/jykrpv1717309891.png",
    "Bournemouth":    "https://upload.wikimedia.org/wikipedia/en/e/e5/AFC_Bournemouth_%282013%29.svg",
    "Brentford":      "https://upload.wikimedia.org/wikipedia/en/2/2a/Brentford_FC_crest.svg",
    "Brighton":       "https://r2.thesportsdb.com/images/media/team/badge/ywypts1448810904.png",
    "Burnley":        "https://r2.thesportsdb.com/images/media/team/badge/ql7nl31686893820.png",
    "Chelsea":        "https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg",
    "Crystal Palace": "https://upload.wikimedia.org/wikipedia/en/a/a2/Crystal_Palace_FC_logo_%282022%29.svg",
    "Everton":        "https://upload.wikimedia.org/wikipedia/en/7/7c/Everton_FC_logo.svg",
    "Fulham":         "https://upload.wikimedia.org/wikipedia/en/e/eb/Fulham_FC_%28shield%29.svg",
    "Leeds":          "https://upload.wikimedia.org/wikipedia/en/5/54/Leeds_United_F.C._logo.svg",
    "Liverpool":      "https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg",
    "Man City":       "https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg",
    "Man United":     "https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg",
    "Newcastle":      "https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg",
    "Nott'm Forest":  "https://upload.wikimedia.org/wikipedia/en/e/e5/Nottingham_Forest_F.C._logo.svg",
    "Sunderland":     "https://upload.wikimedia.org/wikipedia/en/7/77/Logo_Sunderland.svg",
    "Tottenham":      "https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg",
    "West Ham":       "https://upload.wikimedia.org/wikipedia/en/c/c2/West_Ham_United_FC_logo.svg",
    "Wolves":         "https://upload.wikimedia.org/wikipedia/en/f/fc/Wolverhampton_Wanderers.svg",
}

#Henter Holdliste fra backend
teams = list(TEAM_LOGOS.keys())

# Vis logoer i grid med 5 kolonner
cols = st.columns(10)

for i, team in enumerate(teams):
    with cols[i % 10]:
        logo_url = TEAM_LOGOS.get(team, "")
        if logo_url:
            st.image(logo_url, width=80)
        if st.button(team, key=team):
            st.session_state["valgt_hold"] = team


if "valgt_hold" in st.session_state:
    hold = st.session_state["valgt_hold"]
    st.divider()
    st.subheader(f"{hold}")

    # Hent stats og form historik fra backend
    stats = requests.get(f"{BACKEND_URL}/stats/{hold}/home").json()
    form  = requests.get(f"{BACKEND_URL}/form/{hold}").json()["form"]

    # Vis metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Mål scoret (hjemme)", f"{stats['gs']:.2f}")
    col2.metric("Mål lukket ind (hjemme)", f"{stats['gc']:.2f}")
    col3.metric("Vinder-rate (hjemme)", f"{stats['wr']:.0%}")
    col4.metric("Form (gns. point)", f"{stats['form']:.2f}")

    # Form over tid
    st.subheader("Form over tid")
    fig, ax = plt.subplots()
    ax.plot(form, marker="o", color="#1e90ff")
    ax.set_ylabel("Point")
    ax.set_xlabel("Kamp")
    ax.set_yticks([0, 1, 3])
    ax.set_ylim(-0.2, 3.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    st.pyplot(fig)
    plt.close()


"""""
Input Widgets (Left Sidebar):

st.text_input() - Name field
st.number_input() - Age field
st.selectbox() - Color dropdown
st.multiselect() - Hobbies selection
st.slider() - Rating slider
st.select_slider() - Price range
st.date_input() - Birth date picker
st.time_input() - Meeting time
st.checkbox() - Notification preferences
st.radio() - Gender selection
st.text_area() - Comments field
st.button() - Submit button
Display & Output Components (Main Area):

st.metric() - KPI cards with deltas
st.progress() - Progress bars
st.success(), st.info(), st.warning(), st.error() - Status messages
st.code() - Syntax highlighted code
st.json() - Formatted JSON display
"""""