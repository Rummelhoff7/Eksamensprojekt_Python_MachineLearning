# Tester at API'en virker korrekt
# Køres med pytest test/test_api.py

import sys                  # bruges til at tilføje stier
from pathlib import Path   # til filstier

# Sørger for at Python kan finde backend filerne
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from fastapi.testclient import TestClient  # simulerer HTTP requests uden at starte serveren
from main import app                       # importerer selve API'en

client = TestClient(app)


# Tester at API'en svarer med status 200 og ok
def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# Tester at holdlisten ikke er tom
def test_get_teams():
    response = client.get("/teams")
    assert response.status_code == 200
    assert len(response.json()["teams"]) > 0


# Tester at forudsigelse virker med gyldige hold
def test_predict_gyldig():
    response = client.post("/predict", json={
        "home_team": "Arsenal",
        "away_team": "Chelsea"
    })
    assert response.status_code == 200

    data = response.json()
    assert "home_win_prob" in data
    assert "draw_prob" in data
    assert "away_win_prob" in data

    # Sandsynligheder skal summe til ca. 1
    total = data["home_win_prob"] + data["draw_prob"] + data["away_win_prob"]
    assert abs(total - 1.0) < 0.01


# Tester at man ikke kan vælge samme hold to gange
def test_predict_samme_hold():
    response = client.post("/predict", json={
        "home_team": "Arsenal",
        "away_team": "Arsenal"
    })
    assert response.status_code == 400


# Tester at man kan hente statistik for et hjemmehold
def test_stats_hjemme():
    response = client.get("/stats/Arsenal/home")
    assert response.status_code == 200
    data = response.json()
    assert "gs" in data
    assert "gc" in data
    assert "wr" in data


# Tester at forkert side giver fejl
def test_stats_forkert_side():
    response = client.get("/stats/Arsenal/midt")
    assert response.status_code == 400


# Tester at formhistorik returneres korrekt
def test_form():
    response = client.get("/form/Arsenal")
    assert response.status_code == 200
    assert "form" in response.json()
    assert len(response.json()["form"]) > 0


# Tester at sejre/uafgjort/tab returneres korrekt
def test_results():
    response = client.get("/results/Arsenal")
    assert response.status_code == 200
    data = response.json()
    assert "wins" in data
    assert "draws" in data
    assert "losses" in data


# Tester at model metrics returneres korrekt
def test_model_info():
    response = client.get("/model/info")
    assert response.status_code == 200
    data = response.json()
    assert "accuracy" in data
    assert "confusion_matrix" in data
    assert "feature_importance" in data