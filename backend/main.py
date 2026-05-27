#Selve API'en — modtager forespørgsler fra frontend og sender svar tilbage

#Bruges af Streamlit via frontend til HTTP request

# Endpoints:
#   GET  /health               — tjekker om API'en kører
#   GET  /teams                — returnerer liste af alle hold
#   GET  /stats/{team}/{side}  — returnerer statistik for et hold (home/away)
#   GET  /form/{team}          — returnerer form historik for et hold
#   GET  /table/{season}       — returnerer ligatable for en sæson
#   GET  /seasons              — returnerer liste af alle sæsoner
#   GET  /results/{team}       — returnerer sejre/uafgjort/tab for et hold
#   GET  /model/info           — returnerer model metrics (accuracy, confusion matrix, feature importance)
#   POST /predict              — forudsiger kampresultat med XGBoost modellen (ml)
#   POST /analyze              — genererer AI matchanalyse via Mistral
#   POST /chat                 — fodbold chatbot via Mistral


import os                # Læser envvariabel
import pickle            # Indlæser XGBOOST model
import json              # Læser model.metrics.json
from pathlib import Path # til filstier

#Kilde: https://fastapi.tiangolo.com/tutorial/
from fastapi import FastAPI, HTTPException          #FastAPI framework
from fastapi.middleware.cors import CORSMiddleware  #Tillader frontend at kalte api
import requests          # Bruges til Mistral API
import pandas as pd      # Bruges til at filtrere og arbejde med kampdata

#egne filer
from schemas import PredictionRequest, PredictionResponse, AnalysisRequest, AnalysisResponse, TeamListResponse, ChatRequest
from data.loader import load_data # Henter CSV  
from data.prepare import get_home_stats, get_away_stats, get_form, get_form_history, get_prediction_features, FEATURE_COLS

from dotenv import load_dotenv    #Indlæser .env 
load_dotenv()

# Sti til den gemte XGBoost model (.pkl = pickle fil)
MODEL_PATH = Path(__file__).parent / "model" / "pl_predictor.pkl"


# Data og model indlæses én gang ved opstart — ikke per request — for at spare tid
print("Indlæser data...")
_df = load_data()

print("Indlæser model...")
if not MODEL_PATH.exists():
    raise RuntimeError(f"Model ikke fundet: {MODEL_PATH}. Kør train.py først.")

with open(MODEL_PATH, "rb") as f:
    _model = pickle.load(f)

print("Klar!")

app = FastAPI(title="Premier League Predictor")


# Tillader Streamlit at snakke med API'en
#Kilde: https://fastapi.tiangolo.com/tutorial/cors/#use-corsmiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Tjekker om API'en kører
@app.get("/health")
def health():
    return {"status": "ok"}


# Returnerer en sorteret liste af alle hold fra datasættet
@app.get("/teams", response_model=TeamListResponse)
def get_teams():
    teams = sorted(set(_df["HomeTeam"].unique()) | set(_df["AwayTeam"].unique()))
    return TeamListResponse(teams=teams)


# Returnerer statistik for et hold baseret på hjemme eller ude kampe i seneste sæson
@app.get("/stats/{team}/{side}")
def get_team_stats(team: str, side: str):
    if side not in ["home", "away"]:
        raise HTTPException(status_code=400, detail="Side skal være 'home' eller 'away'")

    latest_season = _df["season"].max()
    df = _df[_df["season"] == latest_season]
    future = pd.Timestamp.now()

    if side == "home":
        stats = get_home_stats(df, team, future)
    else:
        stats = get_away_stats(df, team, future)

    stats["form"] = get_form(df, team, future)

    return stats


# Forudsiger kampresultat med XGBoost modellen og returnerer sandsynligheder for H/D/A
@app.post("/predict", response_model=PredictionResponse)
def predict(req: PredictionRequest):
    if req.home_team == req.away_team:
        raise HTTPException(status_code=400, detail="Hjemme- og udehold må ikke være ens")

    features = get_prediction_features(_df, req.home_team, req.away_team)
    X = features[FEATURE_COLS].values

    # predict_proba returnerer sandsynligheder for hver kategori: [H, D, A]
    probs = _model.predict_proba(X)[0]
    # argmax finder indekset med højest sandsynlighed og mapper til H/D/A
    predicted = ["H", "D", "A"][probs.argmax()]

    return PredictionResponse(
        home_team=req.home_team,
        away_team=req.away_team,
        home_win_prob=float(probs[0]),
        draw_prob=float(probs[1]),
        away_win_prob=float(probs[2]),
        predicted_result=predicted,
    )

# Genererer en AI matchanalyse via Mistral baseret på modellens forudsigelse
@app.post("/analyze", response_model=AnalysisResponse)
def analyze(req: AnalysisRequest):
    api_key = os.getenv("MISTRAL_API_KEY", "")

    if not api_key:
        return AnalysisResponse(analysis="Mistral API nøgle mangler.")

    prompt = f"""Du er en Premier League fodboldekspert. Analyser denne kamp:
{req.home_team} (hjemme) vs {req.away_team} (ude)

Model forudsigelse:
- {req.home_team} vinder: {req.home_win_prob:.1%}
- Uafgjort: {req.draw_prob:.1%}
- {req.away_team} vinder: {req.away_win_prob:.1%}

Skriv en kort matchanalyse på 3-4 sætninger."""

    response = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "mistral-small-latest",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200,
        },
        timeout=30,
    )

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Mistral API fejl")

    content = response.json()["choices"][0]["message"]["content"]
    return AnalysisResponse(analysis=content)


# Fodbold chatbot — sender brugerens besked til Mistral og returnerer svar
#Kilde https://docs.mistral.ai/api
@app.post("/chat")
def chat(req: ChatRequest):
    api_key = os.getenv("MISTRAL_API_KEY", "")
    
    response = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "mistral-small-latest",
            "messages": [
                {"role": "system", "content": "Du er en Premier League fodboldekspert."},
                {"role": "user", "content": req.message}
            ],
            "max_tokens": 300,
        },
        timeout=30,
    )
    return {"response": response.json()["choices"][0]["message"]["content"]}


# Returnerer formhistorik som liste af point for de seneste kampe
@app.get("/form/{team}")
def form_history(team: str):
    return {"form": get_form_history(_df, team)}


# Beregner og returnerer ligatabellen for en given sæson sorteret efter point
@app.get("/table/{season}")
def get_table(season: str):
    df = _df[_df["season"] == season]

    table = []
    teams = sorted(set(df["HomeTeam"].unique()) | set(df["AwayTeam"].unique()))

    for team in teams:
        home_games = df[df["HomeTeam"] == team]
        away_games = df[df["AwayTeam"] == team]

        wins   = (home_games["FTR"] == "H").sum() + (away_games["FTR"] == "A").sum()
        draws  = (home_games["FTR"] == "D").sum() + (away_games["FTR"] == "D").sum()
        losses = (home_games["FTR"] == "A").sum() + (away_games["FTR"] == "H").sum()

        goals_for     = int(home_games["FTHG"].sum() + away_games["FTAG"].sum())
        goals_against = int(home_games["FTAG"].sum() + away_games["FTHG"].sum())
        goal_diff     = goals_for - goals_against

        played = wins + draws + losses
        points = wins * 3 + draws

        table.append({
            "team":    team,
            "played":  int(played),
            "wins":    int(wins),
            "draws":   int(draws),
            "losses":  int(losses),
            "gf":      goals_for,
            "ga":      goals_against,
            "gd":      goal_diff,
            "points":  int(points),
        })

    # Sorterer tabellen efter point — flest point øverst
    table = sorted(table, key=lambda x: x["points"], reverse=True)

    return {"table": table}


# Returnerer en liste af alle tilgængelige sæsoner sorteret nyeste først
@app.get("/seasons")
def get_seasons():
    seasons = sorted(_df["season"].unique().tolist(), reverse=True)
    return {"seasons": seasons}


# Returnerer antal sejre, uafgjort og tab for et hold i seneste sæson
@app.get("/results/{team}")
def get_results(team: str):
    latest_season = _df["season"].max()
    df = _df[_df["season"] == latest_season]

    home_games = df[df["HomeTeam"] == team]
    away_games = df[df["AwayTeam"] == team]

    wins   = (home_games["FTR"] == "H").sum() + (away_games["FTR"] == "A").sum()
    draws  = (home_games["FTR"] == "D").sum() + (away_games["FTR"] == "D").sum()
    losses = (home_games["FTR"] == "A").sum() + (away_games["FTR"] == "H").sum()

    return {
        "wins":   int(wins),
        "draws":  int(draws),
        "losses": int(losses),
    }

# Indlæser og returnerer model metrics fra model_metrics.json
@app.get("/model/info")
def model_info():
    metrics_path = Path(__file__).parent / "model" / "model_metrics.json"
    with open(metrics_path) as f:
        return json.load(f)