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