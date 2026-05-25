# Tester at API'en virker korrekt
# Køres med pytest test/test_api.py

#


import sys
from pathlib import Path

# Sørger for at Python kan finde backend filerne
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    """Tester at API'en kører."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_get_teams():
    """Tester at holdlisten ikke er tom."""
    response = client.get("/teams")
    assert response.status_code == 200
    assert len(response.json()["teams"]) > 0


def test_predict_gyldig():
    """Tester at forudsigelse virker med gyldige hold."""
    response = client.post("/predict", json={
        "home_team": "Arsenal",
        "away_team": "Chelsea"
    })
    assert response.status_code == 200

    data = response.json()
    assert "home_win_prob" in data
    assert "draw_prob" in data
    assert "away_win_prob" in data

    # Sandsynligheder skal summer til ca. 1
    total = data["home_win_prob"] + data["draw_prob"] + data["away_win_prob"]
    assert abs(total - 1.0) < 0.01


def test_predict_samme_hold():
    """Tester at man ikke kan vælge samme hold to gange."""
    response = client.post("/predict", json={
        "home_team": "Arsenal",
        "away_team": "Arsenal"
    })
    assert response.status_code == 400


def test_stats_hjemme():
    """Tester at man kan hente statistik for et hjemmehold."""
    response = client.get("/stats/Arsenal/home")
    assert response.status_code == 200
    data = response.json()
    assert "gs" in data
    assert "gc" in data
    assert "wr" in data


def test_stats_forkert_side():
    """Tester at forkert side giver fejl."""
    response = client.get("/stats/Arsenal/midt")
    assert response.status_code == 400