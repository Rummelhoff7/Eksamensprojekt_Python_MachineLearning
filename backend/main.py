#Selve API'en — modtager forespørgsler og sender svar tilbage
#https://fastapi.tiangolo.com/tutorial/

import os
import pickle
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import pandas as pd

from schemas import PredictionRequest, PredictionResponse, AnalysisRequest, AnalysisResponse, TeamListResponse, ChatRequest
from data.loader import load_data
from data.prepare import get_prediction_features, FEATURE_COLS
from data.prepare import get_home_stats, get_away_stats, get_form
from data.prepare import get_form_history
from dotenv import load_dotenv
load_dotenv()

MODEL_PATH = Path(__file__).parent / "model" / "pl_predictor.pkl"

# Global state
_model = None
_df = None


print(" Indlæser data...")
_df = load_data()

print(" Indlæser model...")
if not MODEL_PATH.exists():
    raise RuntimeError(f"Model ikke fundet: {MODEL_PATH}. Kør train.py først.")

with open(MODEL_PATH, "rb") as f:
    _model = pickle.load(f)

print(" Klar!")

app = FastAPI(title="Premier League Predictor")


# Tillader Streamlit at snakke med API'en
#https://fastapi.tiangolo.com/tutorial/cors/#use-corsmiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/teams", response_model=TeamListResponse)
def get_teams():
    teams = sorted(set(_df["HomeTeam"].unique()) | set(_df["AwayTeam"].unique()))
    return TeamListResponse(teams=teams)

@app.get("/stats/{team}/{side}")
def get_team_stats(team: str, side: str):
    if side not in ["home", "away"]:
        raise HTTPException(status_code=400, detail="Side skal være 'home' eller 'away'")


    future = pd.Timestamp.now()

    if side == "home":
        stats = get_home_stats(_df, team, future)
    else:
        stats = get_away_stats(_df, team, future)

    stats["form"] = get_form(_df, team, future)

    return stats

@app.post("/predict", response_model=PredictionResponse)
def predict(req: PredictionRequest):
    if req.home_team == req.away_team:
        raise HTTPException(status_code=400, detail="Hjemme- og udehold må ikke være ens")

    features = get_prediction_features(_df, req.home_team, req.away_team)
    X = features[FEATURE_COLS].values

    probs = _model.predict_proba(X)[0]
    predicted = ["H", "D", "A"][probs.argmax()]

    return PredictionResponse(
        home_team=req.home_team,
        away_team=req.away_team,
        home_win_prob=float(probs[0]),
        draw_prob=float(probs[1]),
        away_win_prob=float(probs[2]),
        predicted_result=predicted,
    )


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


@app.get("/form/{team}")
def form_history(team: str):
    return {"form": get_form_history(_df, team)}


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
        played = wins + draws + losses
        points = wins * 3 + draws

        table.append({
            "team":    team,
            "played":  int(played),
            "wins":    int(wins),
            "draws":   int(draws),
            "losses":  int(losses),
            "points":  int(points),
        })

    table = sorted(table, key=lambda x: x["points"], reverse=True)

    return {"table": table}


@app.get("/seasons")
def get_seasons():
    seasons = sorted(_df["season"].unique().tolist(), reverse=True)
    return {"seasons": seasons}