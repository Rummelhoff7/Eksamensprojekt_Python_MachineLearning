# Viser statistik og grafer for et valgt hold.

import streamlit as st  #Streamlit framework til frontend
import requests #HTTP request
import os #Læser backend env til docker
import matplotlib.pyplot as plt #tegner graferne
import numpy as np #beregne positioner på grafer


#Henter backend url, bruges i docker.
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("Hold Statistik")


#Tager team logo images fra disse urls.
#Alternativ ville være at downloade det ned til projektet.
# st.image kan direkte vise billeder fra en URL — derfor behøver jeg ikke downloade dem.
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

#.keys() returnerer alle "nøglerne i dictionarien , altså holdnavnene"
#list konverterer det til en almindelig python lite
teams = list(TEAM_LOGOS.keys())


# Cacher data for et hold i 1 time så siden ikke kalder backend ved hvert klik
# Henter hjemme/ude statistik, formhistorik og resultater for et hold fra backend
@st.cache_data(ttl=3600)
def get_team_data(team: str):
    stats      = requests.get(f"{BACKEND_URL}/stats/{team}/home").json()
    away_stats = requests.get(f"{BACKEND_URL}/stats/{team}/away").json()
    form       = requests.get(f"{BACKEND_URL}/form/{team}").json()["form"]
    results    = requests.get(f"{BACKEND_URL}/results/{team}").json()
    return stats, away_stats, form, results


#Laver 10 kolonner og placeret hvert hold i den rigtige kolonne.
cols = st.columns(10)
for i, team in enumerate(teams):
    with cols[i % 10]:
        logo_url = TEAM_LOGOS.get(team, "")
        if logo_url:
            st.image(logo_url, width=80)
        if st.button(team, key=team):
            # Session_state er en måde at gemme data mellem Streamlit kørsler, vi gemmer hvilket hold der er valgt til at vise data.
            st.session_state["selected_team"] = team


#Vises kun hvis der er valgt et hold
if "selected_team" in st.session_state:
    selected_team = st.session_state["selected_team"]
    st.divider()
    st.subheader(f"{selected_team}")

    # Henter al data fra backend for det valgte hold
    stats, away_stats, form, results = get_team_data(selected_team)


    # Viser samme data for holdet, så der kommer lidt mere fyld
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Mål scoret (hjemme)", f"{stats['gs']:.2f}")
    col2.metric("Mål lukket ind (hjemme)", f"{stats['gc']:.2f}")
    col3.metric("Vinder-rate (hjemme)", f"{stats['wr']:.0%}")
    col4.metric("Form (gns. point)", f"{stats['form']:.2f}")

    st.divider()

    # Grafer ved siden af hinanden
    graph_col1, graph_col2, graph_col3 = st.columns(3)

    #Graf 1:
    #form er en liste af point. 
    with graph_col1:
        st.subheader("Form over tid")
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(form, marker="o", color="#1e90ff") #linjediagram med en cirkel på datapunkt
        ax.set_xticks(range(len(form))) #sætter tick position på x-akse. En per kamp
        ax.set_xticklabels(range(1, len(form) + 1)) #sætter labels på
        ax.set_ylabel("Point")
        ax.set_xlabel("Kamp")
        ax.set_yticks([0, 1, 3]) # kun mulige point værdier
        ax.set_ylim(-0.2, 3.2)  # lidt luft over og under
        ax.spines["top"].set_visible(False) #ren look
        ax.spines["right"].set_visible(False) # look
        st.pyplot(fig,use_container_width=False) # Viser graf i streamlit
        plt.close() #Frigiver hukommelse

    #Graf 2: 
    #gs er gennemsnit per kamp
    with graph_col2:
        st.subheader("Hjemme vs. Ude")
        categories  = ["Mål scoret", "Mål lukket ind"]
        home_values = [round(stats["gs"] * 5), round(stats["gc"] * 5)] # ganges med 5 for at få total antal mål
        away_values = [round(away_stats["gs"] * 5), round(away_stats["gc"] * 5)]
        x     = np.arange(len(categories)) # x-positioner for søjlerne
        width = 0.35
        fig, ax = plt.subplots(figsize=(6, 3))
        # forskydes med width/2 så hjemme og ude søjler står ved siden af hinanden
        bars_home = ax.bar(x - width/2, home_values, width, label="Hjemme", color="#1e90ff")
        bars_away = ax.bar(x + width/2, away_values, width, label="Ude",    color="#ff4444")

        #Tilføjer tal oven på hver sølje med præcis værdi
        for bar in bars_home:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    f"{bar.get_height():.0f}", ha="center", fontsize=9)
        for bar in bars_away:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    f"{bar.get_height():.0f}", ha="center", fontsize=9)

        ax.set_xticks(x) #sætter x aksens tick position
        ax.set_xticklabels(categories) #sætter labels på dem
        ax.legend() # Viser forklaring med hjemme/ude farver
        #Skjuler øverste og højre kant, rent look og style
        ax.spines["top"].set_visible(False) #Skjuler øverste og højre kant, rent look og style
        ax.spines["right"].set_visible(False) # 
        st.pyplot(fig,use_container_width=False) # viser graf i ST
        plt.close() #Frigiver hukommelse


    #Graf 3
    #Pie chart med procentfordeling.
    with graph_col3:
        st.subheader("Sejr/Uafgjort/Tab")

        labels = [f"Sejr ({results['wins']})", f"Uafgjort ({results['draws']})", f"Tab ({results['losses']})"] # Tekst labels, f.eks. sejr (15)
        values = [results["wins"], results["draws"], results["losses"]] #De tre værdier
        colors = ["#1e90ff", "#a0a0a0", "#ff4444"]

        fig, ax = plt.subplots(figsize=(6, 3)) #str på chart
        ax.pie(values, labels=None, colors=colors, autopct="%1.0f%%") #pie chart
        ax.legend(labels, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.1)) # placerer legenden under grafen i 3 kolonner
        st.pyplot(fig,use_container_width=False)
        plt.close()
        