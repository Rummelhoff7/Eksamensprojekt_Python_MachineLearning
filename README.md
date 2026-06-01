# Premier League Match Predictor
Et eksamensprojekt der forudsiger resultater af Premier League kampe ved hjælp af machine learning.
Begge valgfag er slået sammen i dette projekt.

## Funktionalitet
- Forudsig kampresultater (hjemme/uafgjort/ude) med sandsynligheder
- AI matchanalyse drevet af Mistral
- Fodbold chatbot
- Holdstatistik med grafer
- Ligatable per sæson med zoneopdeling
- Model Info med confusion matrix, feature importance og classification report

## Python version
- Python 3.11

## Teknologier
- **FastAPI** — Backend API
- **Streamlit** — Frontend
- **XGBoost** — Machine learning model
- **Optuna** — Automatisk hyperparameter tuning
- **Pandas** — Databehandling
- **Numpy** — Databehandling i grafer
- **Matplotlib** — Grafer
- **Mistral AI** — AI analyse og chat
- **Docker** — Deployment
- **pytest** — Tests
- **ruff** — Code analysis
- **pyright** — Type checking

## Sådan starter man projektet

### Med Docker (anbefalet)
```bash
docker compose up
```
Åbn http://localhost:8501

### Lokalt
Kræver Python 3.11

```bash
# 1. Opret og aktiver virtual environment
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1

# Mac/Linux
source .venv/bin/activate

# 2. Installer pakker
pip install -r requirements.txt

# 3. Træn modellen (skal kun gøres én gang)
cd backend
python model/train.py
cd ..

# 4. Start backend (nyt terminal vindue)
cd backend
python -m uvicorn main:app --reload

# 5. Start frontend (nyt terminal vindue)
cd frontend
streamlit run Premier_League_Spåkuglen.py
```

### Miljøvariabler
Opret en `.env` fil i roden af projektet:
```
MISTRAL_API_KEY = Din nøgle
```

## Projektstruktur
```
├── backend/
│   ├── data/
│   │   ├── raw/          # CSV-filer med kampdata
│   │   ├── loader.py     # Indlæser CSV-filer
│   │   └── prepare.py    # Feature engineering
│   ├── model/
│   │   ├── train.py          # Træner XGBoost modellen med Optuna tuning
│   │   └── model_metrics.json # Gemmer accuracy, confusion matrix og feature importance
│   ├── schemas.py        # API datastrukturer
│   └── main.py           # FastAPI endpoints
├── frontend/
│   ├── pages/
│   │   ├── 1_FutbalGPT.py
│   │   ├── 2_Premier_League_Tabel.py
│   │   ├── 3_Hold_Statistik.py
│   │   └── 4_Model_Info.py
│   └── Premier_League_Spåkuglen.py
├── test/
│   └── test_api.py
└── docker-compose.yml
```

## Data
Kampdata fra https://datahub.io/football/english-premier-league — 11+ Premier League sæsoner.

## Model
XGBoost klassifikationsmodel trænet på 11 features:
- Hjemme/ude statistik (mål scoret, lukket ind, vinder-rate)
- Form (gennemsnitlige point per kamp)
- Head-to-head historik

Hyperparametre optimeres automatisk med Optuna (30 forsøg per træning).

Accuracy: ~52% (realistisk for fodboldforudsigelse)
