#	Beregner statistik for hvert hold (form, mål, head-to-head)

import pandas as pd

N_GAMES = 5

FEATURE_COLS = [
    "h_home_gs", "h_home_gc", "h_home_wr",
    "a_away_gs", "a_away_gc", "a_away_wr",
    "h_form", "a_form",
    "h2h_h", "h2h_d", "h2h_a",
]


def get_home_stats(df, team, date):
    """Hjemmeholdets statistik fra de seneste N hjemmekampe før given dato."""
    kampe = df[(df["HomeTeam"] == team) & (df["Date"] < date)].tail(N_GAMES)

    if len(kampe) == 0:
        return {"gs": 1.5, "gc": 1.1, "wr": 0.46}

    return {
        "gs": kampe["FTHG"].mean(),   # mål scoret hjemme
        "gc": kampe["FTAG"].mean(),   # mål lukket ind hjemme
        "wr": (kampe["FTR"] == "H").mean(),  # vinder-rate hjemme
    }


def get_away_stats(df, team, date):
    """Udeholdets statistik fra de seneste N udekampe før given dato."""
    kampe = df[(df["AwayTeam"] == team) & (df["Date"] < date)].tail(N_GAMES)

    if len(kampe) == 0:
        return {"gs": 1.1, "gc": 1.5, "wr": 0.27}

    return {
        "gs": kampe["FTAG"].mean(),   # mål scoret ude
        "gc": kampe["FTHG"].mean(),   # mål lukket ind ude
        "wr": (kampe["FTR"] == "A").mean(),  # vinder-rate ude
    }


def get_form(df, team, date):
    """Gennemsnitlige point per kamp de seneste N kampe (hjemme + ude)."""
    hjemme = df[(df["HomeTeam"] == team) & (df["Date"] < date)].tail(N_GAMES).copy()
    ude    = df[(df["AwayTeam"] == team) & (df["Date"] < date)].tail(N_GAMES).copy()

    hjemme["pts"] = hjemme["FTR"].map({"H": 3, "D": 1, "A": 0})
    ude["pts"]    = ude["FTR"].map({"H": 0, "D": 1, "A": 3})

    alle = pd.concat([hjemme[["Date", "pts"]], ude[["Date", "pts"]]])
    alle = alle.sort_values("Date").tail(N_GAMES)

    if len(alle) == 0:
        return 1.3

    return alle["pts"].mean()


def get_h2h(df, home_team, away_team, date):
    """Head-to-head historik mellem to hold."""
    kampe = df[
        (df["HomeTeam"] == home_team) &
        (df["AwayTeam"] == away_team) &
        (df["Date"] < date)
    ].tail(10)

    if len(kampe) == 0:
        return {"h": 0.40, "d": 0.27, "a": 0.33}

    return {
        "h": (kampe["FTR"] == "H").mean(),
        "d": (kampe["FTR"] == "D").mean(),
        "a": (kampe["FTR"] == "A").mean(),
    }


def build_features(df):
    """
    Bygger features til træning.
    Går igennem alle kampe og beregner features FØR hver kamp — ingen data leakage.
    """
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], format="mixed", errors="coerce")
    df = df.sort_values("Date").reset_index(drop=True)

    rows = []

    for _, row in df.iterrows():
        home = row["HomeTeam"]
        away = row["AwayTeam"]
        date = row["Date"]

        h = get_home_stats(df, home, date)
        a = get_away_stats(df, away, date)
        h2h = get_h2h(df, home, away, date)

        rows.append({
            "h_home_gs": h["gs"],
            "h_home_gc": h["gc"],
            "h_home_wr": h["wr"],
            "a_away_gs": a["gs"],
            "a_away_gc": a["gc"],
            "a_away_wr": a["wr"],
            "h_form":    get_form(df, home, date),
            "a_form":    get_form(df, away, date),
            "h2h_h":     h2h["h"],
            "h2h_d":     h2h["d"],
            "h2h_a":     h2h["a"],
            "FTR":       row["FTR"],
            "HomeTeam":  home,
            "AwayTeam":  away,
        })

    return pd.DataFrame(rows)


def get_prediction_features(df, home_team, away_team):
    """
    Beregner features til en kommende kamp.
    Bruges af API'en — bruger den nyeste tilgængelige data.
    """
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], format="mixed", errors="coerce")
    
    # Sætter datoen til i dag så vi bruger al historisk data
    future = pd.Timestamp.now()

    h   = get_home_stats(df, home_team, future)
    a   = get_away_stats(df, away_team, future)
    h2h = get_h2h(df, home_team, away_team, future)

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
    }])[FEATURE_COLS]