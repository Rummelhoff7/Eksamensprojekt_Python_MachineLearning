#XGBOOST:
#Xgboost er god til at strukturet tabeldata, hvilket vi har at gøre med i dette projekt.
#Hurtigt at træne ift. DNN.
#Formålet er at forudsige 3 kategorier (H/D/A)
#DNN ville være overkill i dette projekt.

#Bruger CSV-filer via loader.py og features via prepare.py
#Træner XGBoost modellen og gemmer den som .pkl fil. (pl_predictor_pkl)


import pickle          # bruges til at gemme modellen som en fil
from pathlib import Path  # bruges til filstier
from sklearn.model_selection import train_test_split  # splitter data i træning/test
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix  # evaluering
import xgboost as xgb  # selve ML modellen
import optuna          # automatisk hyperparameter tuning
import sys             # bruges til at tilføje stier
import json            # Bruges til at gemme metrics som .json


optuna.logging.set_verbosity(optuna.logging.WARNING) # Skjuler verbose output fra Optuna

# Sørger for at Python kan finde mine andre filer
sys.path.insert(0, str(Path(__file__).parent.parent))

# https://docs.astral.sh/ruff/linter/#error-suppression
from data.loader import load_data # noqa: E402
from data.prepare import build_features, FEATURE_COLS # noqa: E402

MODEL_PATH = Path(__file__).parent / "pl_predictor.pkl"  # sti til den gemte model

#Metoder der træner selve XGBOOST model
def train():
    print("Indlæser data...")
    df = load_data() #Henter alle CSV kampe

    print("Bygger features...")
    features_df = build_features(df) #Beregner statistik for hvert hold

    # Fjern rækker uden resultat
    features_df = features_df.dropna(subset=FEATURE_COLS + ["FTR"]) #Fjerner rækker med manglende data

    # Input og target
    #H = homewin
    #D = draw
    #A = Away Win
    X = features_df[FEATURE_COLS].values
    y = features_df["FTR"].map({"H": 0, "D": 1, "A": 2}).values #Det modellen skal gætte

    # Split i træning og test
    #80 procent til træning
    #20 procent til test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Optuna finder automatisk de bedste hyperparametre ved at teste 30 kombinationer
    def objective(trial):
        params = {
            "n_estimators":     trial.suggest_int("n_estimators", 100, 400), #antal træer
            "max_depth":        trial.suggest_int("max_depth", 3, 7), #dybde på træet
            "learning_rate":    trial.suggest_float("learning_rate", 0.01, 0.3, log=True), #hvor store skridt pr. træ
            "subsample":        trial.suggest_float("subsample", 0.6, 1.0), #forsøger at forhindre overfitting
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0), #forsøger at forhindre overfitting
            "random_state": 42,
            "eval_metric": "mlogloss",
        }
        #Træner model med parametre og returnerer accuracy
        m = xgb.XGBClassifier(**params)
        m.fit(X_train, y_train)
        return accuracy_score(y_test, m.predict(X_test))

    print("Finder bedste hyperparametre med Optuna (30 forsøg)...")
    study = optuna.create_study(direction="maximize") # maksimerer accuracy
    study.optimize(objective, n_trials=30) #30 forsøg
    print(f"Bedste parametre: {study.best_params}")

    # Træner den endelige model med de bedste parametre
    print("Træner modellen med bedste parametre...")
    model = xgb.XGBClassifier(**study.best_params, random_state=42, eval_metric="mlogloss")
    model.fit(X_train, y_train)

    # Evaluering
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n Accuracy: {acc:.1%}")
    print(classification_report(y_test, y_pred, target_names=["Hjemme", "Uafgjort", "Ude"], zero_division=0))
    
    # Gemmer metrics som JSON så frontend kan hente dem
    cm = confusion_matrix(y_test, y_pred)
    metrics = {
        "accuracy": float(acc),
        "confusion_matrix": cm.tolist(),
        "feature_importance": dict(zip(FEATURE_COLS, [float(x) for x in model.feature_importances_])),
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
        "best_params": study.best_params,
        # output_dict=True returnerer en dictionary i stedet for en string — bruges til at gemme i JSON
        "classification_report": classification_report(
            y_test, y_pred,
            target_names=["Hjemme", "Uafgjort", "Ude"],
            zero_division=0,
            output_dict=True
        ),
    }
    #bygger metrics fil og gemmer i model mapppe
    metrics_path = Path(__file__).parent / "model_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f)
    print(f" Metrics gemt: {metrics_path}")

    # Gem model
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    print(f" Model gemt: {MODEL_PATH}")


if __name__ == "__main__":
    train()
