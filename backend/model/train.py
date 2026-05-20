#XGBOOST:
#Xgboost er god til at strukturet tabeldata, hvilket vi har at gøre med i dette projekt.
#Hurtigt at træne ift. DNN.
#Formålet er at forudsige 3 kategorier (H/D/A)
#DNN ville være overkill i dette projekt.
#Træner XGBoost modellen og gemmer den som .pkl fil


import pickle          # bruges til at gemme modellen som en fil
from pathlib import Path  # bruges til filstier
from sklearn.model_selection import train_test_split  # splitter data i træning/test
from sklearn.metrics import accuracy_score, classification_report  # evaluering
import xgboost as xgb  # selve ML modellen
import sys             # bruges til at tilføje stier

# Sørger for at Python kan finde mine andre filer
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.loader import load_data
from data.prepare import build_features, FEATURE_COLS

MODEL_PATH = Path(__file__).parent / "pl_predictor.pkl"


def train():
    print("Indlæser data...")
    df = load_data() #Henter alle CSV kampe

    print("⚙️  Bygger features...")
    features_df = build_features(df) #Berenger statistik for hvert hold

    # Fjern rækker uden resultat
    features_df = features_df.dropna(subset=FEATURE_COLS + ["FTR"]) #Fjerne rækker med manglende data

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

    #XGBOOST model 
    print("Træner modellen")
    model = xgb.XGBClassifier(
        n_estimators=200, #antal estimationer
        max_depth=4, #hvor dybt træet er
        learning_rate=0.05, #hvor store skridt modellen tager
        random_state=42,
        eval_metric="mlogloss",
    )
    model.fit(X_train, y_train) #Træner modellen

    # Evaluering
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n Accuracy: {acc:.1%}")
    print(classification_report(y_test, y_pred, target_names=["Hjemme", "Uafgjort", "Ude"]))

    # Gem model
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    print(f" Model gemt: {MODEL_PATH}")


if __name__ == "__main__":
    train()