# Læser alle CSV-filer og kombinerer dem til én stor DataFrame
# Bruges af train.py til træning og main.py til API
# Input: CSV filer i data/raw
# Output en pandas dataframe med alle kampe fra alle sæsoner

#Dataset: https://datahub.io/football/english-premier-league

import pandas as pd
from pathlib import Path

def load_data() -> pd.DataFrame:

    #finder csv mappen med filerne
    raw_path = Path(__file__).parent / "raw"
    
    all_seasons = []
    
    #Går igennem alle filer i /data/raw og indlæser
    for file in sorted(raw_path.glob("*.csv")):
        #Indlæser og kombinere
        df = pd.read_csv(file)
        df["season"] = file.stem  # tilføj sæson-kolonne
        all_seasons.append(df)
    
    #Kombinerer alle sæsoner til en dataframe
    #https://pandas.pydata.org/docs/reference/api/pandas.concat.html
    combined = pd.concat(all_seasons, ignore_index=True)
    
    # Beholder kun relevante kolonner
    cols = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", 
            "FTR", "HTHG", "HTAG", "HS", "AS", "HST", "AST",
            "HC", "AC", "HY", "AY", "HR", "AR", "season"]
    
    combined = combined[[c for c in cols if c in combined.columns]]

    #fjerner kampe hvor resultat mangler
    combined = combined.dropna(subset=["FTR"])

    #Konverterer dato kolononnen til datetime format
    combined["Date"] = pd.to_datetime(combined["Date"], format="mixed", errors="coerce")
    
    return combined

if __name__ == "__main__":
    df = load_data()
    print(f"Loaded {len(df)} matches")
    print(df.head())