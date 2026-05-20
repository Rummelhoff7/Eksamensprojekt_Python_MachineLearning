import streamlit as st
import requests
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("FutbalGPT")

question = st.text_input("Stil et spørgsmål om Premier League")

if st.button("Send"):
    with st.spinner("Tænker..."):
        answer = requests.post(f"{BACKEND_URL}/chat", json={"message": question})
        st.write(answer.json()["response"])