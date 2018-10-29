from google.cloud import bigquery
from google.oauth2 import service_account
import json
import numpy as np

CREDENTIALS = service_account.Credentials.from_service_account_file(
    "/Users/jennyxue/Desktop/6S198/redbull_creds.json")
PROJECT_ID = "spurs-sp2018"

def get_best_champ_select(request):
    """
    Parses the request and returns the list of champs that should be selected next.
    """
    payload = json.loads(request.data)
    team = payload["team"]
    enemy = payload["enemy"]
    preferred = payload.get("preferred", None)
    bans = payload.get("bans", None)
    num = payload.get("num", None)
    return get_pick_given_selections_by_winrate(team, enemy, preferred=preferred, bans=bans)[:num]

def get_pick_given_selections_by_winrate(team, opponent, preferred=None, bans=None):
    """
    Compiles and runs the SQL query 
    """
    client = bigquery.Client(credentials=CREDENTIALS, project=PROJECT_ID)

    query = "SELECT * FROM `spurs-sp2018.league_of_legends.PositionalMatchups` "
    games_query = "ORDER BY WinRate ASC, Games ASC LIMIT {}".format(500)
    
    champ_query = get_champ_query(team, opponent)
    ban_query = get_ban_query(bans, team, opponent)

    if champ_query != "" and ban_query != "":
        champ_query += " AND "
    
    if champ_query != "" or ban_query != "":
        query += "WHERE "

    query = query + champ_query + ban_query + games_query 
    print(query)
    # if champ_query == "" and ban_query == "":
    #     return [("Aurelion Sol", "MIDDLE", 0.5402390438247012),
    #             ("Heimerdinger", "ADC", 0.5385117493472585),
    #             ("Shaco", "JUNGLE", 0.5328070232908573),
    #             ("Viktor", "TOP", 0.5205676676264912),
    #             ("Sona", "SUPPORT", 0.5189737286833614)]
    query_job = client.query(query)
    results = query_job.result().to_dataframe().to_dict("records")
    return get_champions_for_position_given_opp_by_winrate(results, preferred, bans)

def get_champ_query(team, opponent):
    """
    Helper function for champ query
    """
    champ_query = "("
    for r in team.keys():
        if opponent[r] != "" and team[r] == "":
            champ_query += """(Champ="{}" AND Position="{}" AND GAMES > 60) OR """.format(opponent[r], r)
    
    if champ_query != "(":
        champ_query = champ_query[:-4] + ")"
    else:
        champ_query = ""
    
    return champ_query

def get_ban_query(bans, team, enemy):
    """
    Helper function for ban query
    """
    ban_query = "("
    
    if bans != None:
        for ban in bans:
            ban_query += """(Matchup!="{}") AND """.format(ban)
    
    for t in list(team.values()):
        if t != "":
            ban_query += """(Matchup!="{}") AND """.format(t)
        
    for t in list(enemy.values()):
        if t != "":
            ban_query += """(Matchup!="{}") AND """.format(t)

    if ban_query != "(":
        ban_query = ban_query[:-5] + ")"
    else:
        ban_query = "" 

    return ban_query

def get_champions_for_position_given_opp_by_winrate(results, preferred, bans):
    """
    Helper function for ban query
    """
    # find enemy matchup with lowest winrate
    possible_champs = []
    for matchup in results:
        matchup_champ = matchup["Matchup"]
        win_rate = round((0.5 - matchup["WinRate"]) * 100, 2)
        position = matchup["Position"]
        # only considers matchups with greater than 100 games, in preferred, and not in bans
        # if(preferred == None or (preferred != None and matchup_champ in preferred)) and (bans == None or (bans != None and matchup_champ not in bans)):
        if position == "ADCSUPPORT" or position == "DUO_SUPPORT":
            position = "SUPPORT"
        if position == "DUO_CARRY":
            position = "ADC"
        if position != "SYNERGY":
            possible_champs.append((matchup_champ, win_rate, position))
    possible_champs.sort(key=lambda x: x[1])
    return possible_champs[::-1]


# team = {"TOP": "", "JUNGLE": "", "MIDDLE": "", "DUO_CARRY": "Tristana", "DUO_SUPPORT": "Leona"}
# enemy = {"TOP": "", "JUNGLE": "", "MIDDLE": "Zed", "DUO_CARRY": "", "DUO_SUPPORT": "Nami"}
# bans = ["Gallio", "Shyvana"]
# print(get_pick_given_selections_by_winrate(team, enemy, bans=bans))