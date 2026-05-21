# Bygger docker image til backend. (frontend har også egen dockerfile)

# 1. Installerer python dependencies
# 2. Kopierer backend kode
# 3. Træn er XGBOOST modellen (pkl fil gemmes i image)
# 4. Starter FastAPI serveren på port 8000

#kilde: https://docs.docker.com/reference/dockerfile/

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .

RUN python -m model.train

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]