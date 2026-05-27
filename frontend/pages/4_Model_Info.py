# Viser information om XGBoost modellen — accuracy, confusion matrix og feature importance

import streamlit as st  #Streamlit framework til frontend
import requests #Henter model metrics fra /model/info
import matplotlib.pyplot as plt #tegner confusion metrics og FI
import numpy as np #konvertere matrix til et array
import os #Læser backend env til docker

#Henter backend url, bruges i docker.
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("Model Info")
st.caption("Indblik i XGBoost modellens ydeevne")

# Henter model metrics fra backend
data = requests.get(f"{BACKEND_URL}/model/info").json()

st.divider()

# Accuracy
st.metric("Model Accuracy", f"{data['accuracy']:.1%}")

# Trænings- og testdata størrelse
st.metric("Træningsdata", f"{data['train_size']} kampe")
st.metric("Testdata", f"{data['test_size']} kampe")

st.divider()

# Bedste Optuna parametre
st.subheader("Bedste hyperparametre")
st.caption("Fundet automatisk af Optuna")
st.json(data["best_params"])

st.divider()

# Classification report som tabel
st.subheader("Classification Report")
st.caption("Precision, recall og f1-score for hver kategori")

report = data["classification_report"]
rows = []
for label in ["Hjemme", "Uafgjort", "Ude"]:
    row = report[label]
    rows.append({
        "Kategori":  label,
        "Precision": f"{row['precision']:.2f}",
        "Recall":    f"{row['recall']:.2f}",
        "F1-score":  f"{row['f1-score']:.2f}",
        "Antal":     int(row['support']),
    })

st.dataframe(rows, hide_index=True, use_container_width=True)

st.divider()

# Confusion matrix og feature importance vises side om side
cm_col, fi_col = st.columns(2)

with cm_col:
    st.subheader("Confusion Matrix")
    st.caption("Viser hvor mange kampe modellen forudsagde korrekt og forkert")

    cm = np.array(data["confusion_matrix"])
    labels = ["Hjemme", "Uafgjort", "Ude"]

    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(cm, cmap="Blues") # tegner heatmap med blå farvepalette

    ax.set_xticks(range(3))
    ax.set_yticks(range(3))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Forudsagt")
    ax.set_ylabel("Faktisk")

    # Tal inde i hver celle
    for i in range(3):
        for j in range(3):
            ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=12, fontweight="bold")

    plt.colorbar(im, ax=ax) #Farvebjælker
    plt.tight_layout() #Justerer margin og spacing
    st.pyplot(fig, use_container_width=False) 
    plt.close()

with fi_col:
    st.subheader("Feature Importance")
    st.caption("Hvilke features vejer mest i modellen")

    fi = data["feature_importance"]
    features = list(fi.keys())
    values = list(fi.values())

    # Sorterer så vigtigste feature er øverst
    sorted_pairs = sorted(zip(values, features), reverse=True)
    values, features = zip(*sorted_pairs) # pakker de sorterede par ud igen i to separate lister

    # Oversætter tekniske navne til dansk. Dictionary
    feature_labels = {
        "h_home_gs": "Hjemmehold mål scoret",
        "h_home_gc": "Hjemmehold mål lukket ind",
        "h_home_wr": "Hjemmehold vinder-rate",
        "a_away_gs": "Udehold mål scoret",
        "a_away_gc": "Udehold mål lukket ind",
        "a_away_wr": "Udehold vinder-rate",
        "h_form":    "Hjemmehold form",
        "a_form":    "Udehold form",
        "h2h_h":     "H2H hjemme vinder",
        "h2h_d":     "H2H uafgjort",
        "h2h_a":     "H2H ude vinder",
    }
    features = [feature_labels.get(f, f) for f in features]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.barh(features, values, color="#1e90ff") #Vandret søjlediagram 
    ax.set_xlabel("Importance")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=False)
    plt.close()