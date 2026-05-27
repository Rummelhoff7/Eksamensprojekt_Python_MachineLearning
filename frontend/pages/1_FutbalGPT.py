#Her er LLM med chat implementeret i frontend.
#Drevet af Mistral.

import streamlit as st #streamlit framework som frontend
import requests #Til mistral
import os #Læser backend env til docker

#Henter backend url, bruges i docker.
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("FutbalGPT")

#Kilde: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
# Initialiserer samtalehistorik hvis den ikke findes
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# Vis tidligere beskeder
for message in st.session_state["chat_history"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input fastgjort i bunden — sender med Enter
question = st.chat_input("Stil et spørgsmål om Premier League")

if question:
    # Tilføj brugerens spørgsmål til historik
    st.session_state["chat_history"].append({"role": "user", "content": question})

    with st.spinner("Tænker..."):
        answer = requests.post(f"{BACKEND_URL}/chat", json={"message": question})

    if answer.status_code == 200:
        response = answer.json()["response"]
        # Tilføj svar til historik
        st.session_state["chat_history"].append({"role": "assistant", "content": response})
    else:
        st.error("Noget gik galt. Prøv igen.")

    # Genindlæs siden så historikken vises
    st.rerun()