#Her er LLM med chat implementeret i frontend.
#Drevet af Mistral.


import streamlit as st
import requests
import os

#Henter backend url, bruges i docker.
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("FutbalGPT")

question = st.text_input("Stil et spørgsmål om Premier League")


if st.button("Send"):
    with st.spinner("Tænker..."):
        #sender question til til /chat endpoint i backend som en json body
        answer = requests.post(f"{BACKEND_URL}/chat", json={"message": question})

        #Error handling
        if answer.status_code == 200:
            st.write(answer.json()["response"]) #konverterer svaret til dictionary
        else:
            st.error("Noget gik galt. Prøv igen.")