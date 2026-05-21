#Bygger docker image til frontend. (backend har også egen dockerfile)

# 1. installere python dependencies(fra requirements)
# 2. kopierer frontend kode
# 3. starter streamlit app på porten 8501

#kilde: https://docs.docker.com/reference/dockerfile/

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY frontend/ .

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]