#Brugergrænsefladen — dropdowns, diagram og AI analyse med LLM
#Hovedsiden i streamlit, det her er den der skal kaldes med run kommando

# Her kan man vælge to hold og forudsige resulatet af kampen. 


import streamlit as st
import requests
import matplotlib.pyplot as plt 
import os


#Henter backend url, bruges i docker.
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

#Sætter config for siden, skal kaldes som det første
st.set_page_config(page_title="Premier League Predictor", layout="wide")

st.title("Premier League Match Predictor")

st.divider()


#Cacher = den henter én gang per time. Så den ikke skal kalde backend hver gang
@st.cache_data(ttl=3600)
#Kalder /teams endpoint og returnerer liste af hold
def get_teams():
    r = requests.get(f"{BACKEND_URL}/teams")
    return r.json()["teams"]

#simpel try catch: stopper siden backend ikke kører
try:
    teams = get_teams()
except Exception:
    st.error("Kunne ikke forbinde til backend. Sørg for at API'en kører.")
    st.stop()


#2 col med dropdowns: hjemme og ude hold
col1, col2 = st.columns(2)

with col1:
    home_team = st.selectbox("Hjemmehold", teams)

with col2:
    away_options = [t for t in teams if t != home_team] # man skal ikke kunne vælge samme hold
    away_team = st.selectbox("Udehold", away_options)


# Cacher.
#Henter seneste 5 kampes statisik for begge hold og viser dem som metrics
@st.cache_data(ttl=3600)
def get_team_stats(team: str, side: str):
    r = requests.get(f"{BACKEND_URL}/stats/{team}/{side}") # Kalder dette endpoint
    if r.status_code == 200:
        return r.json()
    return None


st.divider()

st.text("De sidste 5 kampe")

stat_col1, stat_col2 = st.columns(2)

home_stats = get_team_stats(home_team, "home")
away_stats = get_team_stats(away_team, "away")



with stat_col1:
    st.subheader(f"{home_team}")
    if home_stats:
        st.metric("Form (gns. point)", f"{home_stats['form']:.2f}")
        st.metric("Mål scoret (hjemme)", f"{home_stats['gs']:.2f}")
        st.metric("Mål lukket ind (hjemme)", f"{home_stats['gc']:.2f}")
        st.metric("Vinder-rate (hjemme)", f"{home_stats['wr']:.0%}")

with stat_col2:
    st.subheader(f"{away_team}")
    if away_stats:
        st.metric("Form (gns. point)", f"{away_stats['form']:.2f}")
        st.metric("Mål scoret (ude)", f"{away_stats['gs']:.2f}")
        st.metric("Mål lukket ind (ude)", f"{away_stats['gc']:.2f}")
        st.metric("Vinder-rate (ude)", f"{away_stats['wr']:.0%}") 


st.divider()

#Når man trykker på knappen her, så sendes en POST request til /predict. svaret indeholder 3 sansynligheder.
if st.button("Forudsig kamp", type="primary", use_container_width=True):

    #st.spinner = laver et spinner icon mens den finder output
    with st.spinner("Analyserer..."):
        pred_resp = requests.post(
            f"{BACKEND_URL}/predict", #endpoint
            json={"home_team": home_team, "away_team": away_team},
        )

    #Error handling
    if pred_resp.status_code != 200:
        st.error("Forudsigelse fejlede.")
        st.stop()

    # konverterer HTTP-svaret fra backend til et json.
    pred = pred_resp.json()

    # Selve grafen der viser resultatet visuelt fra modellen
    fig, ax = plt.subplots(figsize=(5, 3))
    labels = [f"{home_team}\nVinder", "Uafgjort", f"{away_team}\nVinder"]
    probs  = [pred["home_win_prob"], pred["draw_prob"], pred["away_win_prob"]]
    colors = ["#1e90ff", "#a0a0a0", "#ff4444"]

    bars = ax.barh(labels, [p * 100 for p in probs], color=colors, height=0.5)

    for bar, prob in zip(bars, probs):
        ax.text(
            bar.get_width() + 0.5,
            bar.get_y() + bar.get_height() / 2,
            f"{prob:.1%}",
            va="center",
            fontsize=12,
            fontweight="bold",
        )

    ax.set_xlim(0, 100)
    ax.set_xlabel("Sandsynlighed (%)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    st.pyplot(fig)
    plt.close()

    # 
    result_map = {
        "H": f" {home_team} vinder",
        "D": "🤝 Uafgjort",
        "A": f" {away_team} vinder",
    }
    st.success(f"**Forudsagt resultat: {result_map[pred['predicted_result']]}**")

    #
    st.divider()

    #Sandsynlighederne sendes til /analyze POST endpoint som Kalder Mistral og returener tekstanalyse af resulat
    st.subheader("AI Matchanalyse")
    with st.spinner("Genererer analyse..."):
        analysis_resp = requests.post(
            f"{BACKEND_URL}/analyze", #endpoint
            json={
                "home_team": home_team,
                "away_team": away_team,
                "home_win_prob": pred["home_win_prob"],
                "draw_prob": pred["draw_prob"],
                "away_win_prob": pred["away_win_prob"],
            },
        )

    #error handling
    if analysis_resp.status_code == 200:
        st.write(analysis_resp.json()["analysis"])


