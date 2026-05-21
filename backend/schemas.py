#Denne fil defininerer datastruktur for API request og response
#Bruges a main.py til at validere data, som sendes til og fra api'en

# Request  = data der sendes til API'en (f.eks. hvilke hold skal forudsiges)
# Response = data der returneres fra API'en (f.eks. sandsynligheder og resultat)

#Pydantic sikrer at data har de rigtige typer.
#kilde: https://pydantic.dev/docs/validation/latest/concepts/models
from pydantic import BaseModel


class PredictionRequest(BaseModel):
    home_team: str
    away_team: str


class PredictionResponse(BaseModel):
    home_team: str
    away_team: str
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    predicted_result: str  # "H", "D" eller "A"


class AnalysisRequest(BaseModel):
    home_team: str
    away_team: str
    home_win_prob: float
    draw_prob: float
    away_win_prob: float


class AnalysisResponse(BaseModel):
    analysis: str


class TeamListResponse(BaseModel):
    teams: list[str]

class ChatRequest(BaseModel):
    message: str