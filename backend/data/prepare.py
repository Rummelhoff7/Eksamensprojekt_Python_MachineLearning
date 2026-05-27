# Beregner statistik for hvert hold ud fra historisk data.
# Bruges af: train.py til at bygge træningsdata og main.py til forudsigelser.
# Input: Dataframe fra loader.py
# Output: Features som XGboost modellen kan bruge

# Al statistik beregnes før kampens data, så ingen data leakage
# Betyder at modellen kun ser data der var tilgængeligt før kampen


import pandas as pd


N_GAMES = 5

FEATURE_COLS = [
    "h_home_gs", "h_home_gc", "h_home_wr",
    "a_away_gs", "a_away_gc", "a_away_wr",
    "h_form", "a_form",
    "h2h_h", "h2h_d", "h2h_a",
]

#Returnerer hjemmeholdets gennemsnitlige statistik fra de seneste (N) hjemmekampe før given dato
def get_home_stats(df, team, date):

    #Filtrerer hjemmekampe i dataframe før given dato med sidste 5(N).
    matches = df[(df["HomeTeam"] == team) & (df["Date"] < date)].tail(N_GAMES)

    
    if len(matches) == 0:
        return {"gs": 1.5, "gc": 1.1, "wr": 0.46} #gennemsnits værdier

    return {
        "gs": matches["FTHG"].mean(),   # mål scoret hjemme
        "gc": matches["FTAG"].mean(),   # mål lukket ind hjemme
        "wr": (matches["FTR"] == "H").mean(),  # vinder-rate hjemme
    }

# Returnerer Udeholdets statistik fra de seneste N udekampe før given dato. 
def get_away_stats(df, team, date):

    #Filtrerer udekampe i dataframe før given dato med sidste 5(N).
    matches = df[(df["AwayTeam"] == team) & (df["Date"] < date)].tail(N_GAMES)

    if len(matches) == 0:
        return {"gs": 1.1, "gc": 1.5, "wr": 0.27} #gennemsnits værdier

    return {
        "gs": matches["FTAG"].mean(),   # mål scoret ude
        "gc": matches["FTHG"].mean(),   # mål lukket ind ude
        "wr": (matches["FTR"] == "A").mean(),  # vinder-rate ude
    }


# Returnerer gennemsnitlige point per kamp de seneste N kampe (hjemme + ude)
def get_form(df, team, date):
    
    #Henter de seneste ude- og hjemme kampe. 
    home_games = df[(df["HomeTeam"] == team) & (df["Date"] < date)].tail(N_GAMES).copy() #.copy = så vi ikke ændre den originale df
    away_games = df[(df["AwayTeam"] == team) & (df["Date"] < date)].tail(N_GAMES).copy()

    #Konvertere resultater til point. Både ude og hjemme
    home_games["pts"] = home_games["FTR"].map({"H": 3, "D": 1, "A": 0}) #3 sejr, 1, uafgjort, 0 tabt
    away_games["pts"] = away_games["FTR"].map({"H": 0, "D": 1, "A": 3})

    #Slår begge sammen.
    #pd.concat : pandas bibliotek der sætter to dataframes til én
    all_games = pd.concat([home_games[["Date", "pts"]], away_games[["Date", "pts"]]])
    all_games = all_games.sort_values("Date").tail(N_GAMES)

    
    if len(all_games) == 0:
        return 1.3 #Ingen historik = 1.3 (gennemsnit)

    #Returnerer og beregner gennemsnit af point-kolonnen
    return all_games["pts"].mean()


#Head-to-head historik mellem to hold.
def get_h2h(df, home_team, away_team, date):

    #Filtrerer alle kampe hvor de to hold har mødt hinanden (hjemme/ude)
    matches = df[
        (df["HomeTeam"] == home_team) &
        (df["AwayTeam"] == away_team) &
        (df["Date"] < date)
    ].tail(10) #sidste 10 

    if len(matches) == 0:
        return {"h": 0.40, "d": 0.27, "a": 0.33} #Hvis ingen historik: Gennemsnitlige værdier

    #.mean() beregner gennemsnittet af kolonne eller liste
    return {
        "h": (matches["FTR"] == "H").mean(),
        "d": (matches["FTR"] == "D").mean(),
        "a": (matches["FTR"] == "A").mean(),
    }



#Bygger features til træning. Går igennem alle kampe og beregner features FØR hver kamp — ingen data leakage.
def build_features(df):
    #Laver kopi af df
    df = df.copy()

    #Konverterer dato-kolonne til datetime format.
    #Sorterer alle kampe kronologisk.
    df["Date"] = pd.to_datetime(df["Date"], format="mixed", errors="coerce")
    df = df.sort_values("Date").reset_index(drop=True) #.rest_index() = nulstiller rækkernes nummering efter sortering

    rows = []

    # for løkke med alle kampe, én ad gangen. .iterrows() går igennem df og returnerer rækkenr og row.
    for _, row in df.iterrows():
        home = row["HomeTeam"]
        away = row["AwayTeam"]
        date = row["Date"]

        #Kalder hjælpe funktioner med kampens dato, statistikken kun beregnes på data før kampen
        h = get_home_stats(df, home, date)
        a = get_away_stats(df, away, date)
        h2h = get_h2h(df, home, away, date)

        #Tilføjer en række med alle 11 feautures.
        #df skal forudsige FTR
        rows.append({
            "h_home_gs": h["gs"], #goal scoret
            "h_home_gc": h["gc"], #goal conceeded
            "h_home_wr": h["wr"], #home winrate
            "a_away_gs": a["gs"],
            "a_away_gc": a["gc"],
            "a_away_wr": a["wr"], #away winrate
            "h_form":    get_form(df, home, date),
            "a_form":    get_form(df, away, date),
            "h2h_h":     h2h["h"],
            "h2h_d":     h2h["d"],
            "h2h_a":     h2h["a"],
            "FTR":       row["FTR"], #Full time result
            "HomeTeam":  home,
            "AwayTeam":  away,
        })

    return pd.DataFrame(rows)



# Beregner features til en kommende kamp.
# Bruges af API'en — bruger den nyeste tilgængelige data.
def get_prediction_features(df, home_team, away_team):
    #kopi af df
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], format="mixed", errors="coerce")

    # Sætter datoen til i dag så vi bruger al historisk data
    future = pd.Timestamp.now()

    #Samme hjælpefunktioner som build_features(). Dog til kampe ikke spillet endnu
    h   = get_home_stats(df, home_team, future)
    a   = get_away_stats(df, away_team, future)
    h2h = get_h2h(df, home_team, away_team, future)

    #Returnerer en enkelt række som en df med samme features som trænet.
    return pd.DataFrame([{
        "h_home_gs": h["gs"],
        "h_home_gc": h["gc"],
        "h_home_wr": h["wr"],
        "a_away_gs": a["gs"],
        "a_away_gc": a["gc"],
        "a_away_wr": a["wr"],
        "h_form":    get_form(df, home_team, future),
        "a_form":    get_form(df, away_team, future),
        "h2h_h":     h2h["h"],
        "h2h_d":     h2h["d"],
        "h2h_a":     h2h["a"],
    }])[FEATURE_COLS] #sikrer kolonner er i den rigtige rækkefølge

#Returnerer point per kamp for de seneste n kampe i nyeste sæson.
def get_form_history(df, team, n=10):
    #Finder den nyeste sæson og filtrere så vi kun kigger på den. Bruges til form graf
    latest_season = df["season"].max()
    df = df[df["season"] == latest_season]

    #Konverterer resultater til point, som i get_form
    home_games = df[df["HomeTeam"] == team].copy()
    away_games = df[df["AwayTeam"] == team].copy()

    home_games["pts"] = home_games["FTR"].map({"H": 3, "D": 1, "A": 0})
    away_games["pts"] = away_games["FTR"].map({"H": 0, "D": 1, "A": 3})

    #Slår ude og hjemme sammen til all_games
    all_games = pd.concat([home_games[["Date", "pts"]], away_games[["Date", "pts"]]])
    all_games = all_games.sort_values("Date").tail(n)

    #Returenerer en liste af point i stedet for df. 
    return all_games["pts"].tolist()
