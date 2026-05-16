import pandas as pd
import os
from pathlib import Path

def load_data() -> pd.DataFrame:

    #finder csv filer
    raw_path = Path(__file__).parent / "raw"
    
    all_seasons = []
    
    #Går igennem alle filer i /data/raw
    for file in sorted(raw_path.glob("*.csv")):
        #Indlæser og kombinere
        df = pd.read_csv(file)
        df["season"] = file.stem  # tilføj sæson-kolonne
        all_seasons.append(df)
    
    combined = pd.concat(all_seasons, ignore_index=True)
    
    # Beholder kun relevante kolonner
    cols = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", 
            "FTR", "HTHG", "HTAG", "HS", "AS", "HST", "AST",
            "HC", "AC", "HY", "AY", "HR", "AR", "season"]
    
    combined = combined[[c for c in cols if c in combined.columns]]
    #fjerner kampe hvor resultat mangler
    combined = combined.dropna(subset=["FTR"])
    
    return combined

if __name__ == "__main__":
    df = load_data()
    print(f"✅ Loaded {len(df)} matches")
    print(df.head())