#Denne fil defininerer datastruktur for API request og response
#Bruges a main.py til at validere data, som sendes til og fra api'en

# Request  = data der sendes til API'en (f.eks. hvilke hold skal forudsiges)
# Response = data der returneres fra API'en (f.eks. sandsynligheder og resultat)

#Pydantic sikrer at data har de rigtige typer.
#kilde: https://pydantic.dev/docs/validation/latest/concepts/models
from pydantic import BaseModel

# Hvilke hold skal spille mod hinanden
class PredictionRequest(BaseModel):
    home_team: str
    away_team: str


# Modellens forudsigelse med sandsynligheder for hvert udfald
class PredictionResponse(BaseModel):
    home_team: str
    away_team: str
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    predicted_result: str  # "H", "D" eller "A"


# Kampdata sendt til Mistral for at generere en analyse
class AnalysisRequest(BaseModel):
    home_team: str
    away_team: str
    home_win_prob: float
    draw_prob: float
    away_win_prob: float


# AI-analysen returneret fra Mistral
class AnalysisResponse(BaseModel):
    analysis: str


# Liste af alle hold i datasættet
class TeamListResponse(BaseModel):
    teams: list[str]


# Brugerens besked til chatbotten
class ChatRequest(BaseModel):
    message: str