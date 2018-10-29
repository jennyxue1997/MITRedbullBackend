from google.cloud import bigquery
from google.oauth2 import service_account
import json
import matplotlib.pyplot as plt

CREDENTIALS = service_account.Credentials.from_service_account_file(
    "redbull_creds.json")
PROJECT_ID = "spurs-sp2018"

def get_best_time_to_win(request):
    """
    Parses the request and returns the list of champs that should be selected next.
    """
    payload = json.loads(request.data)
    team = payload["team"]
    enemy = payload["opponent"]
    return get_win_rate_over_time(team, enemy)

def get_time_given_selections_by_winrate(team, enemy):
    """
    Compiles and runs the SQL query 
    """
    client = bigquery.Client(credentials=CREDENTIALS, project=PROJECT_ID)

    query = "SELECT * FROM `spurs-sp2018.league_of_legends.ChampOptimalWinTime`"
    games_query = "LIMIT {}".format(500)

    champ_query = "("
    for pos in team.keys():
        champ_query += """(Champ="{}" AND Position="{}") OR """.format(team[pos], pos)
    
    if champ_query != "WHERE (":
        champ_query = champ_query[:-4] + ")"
    else:
        champ_query = ""
    
    query = query + "WHERE " + champ_query + games_query 
    query_job = client.query(query)
    results = query_job.result().to_dataframe().to_dict("records")
    
    times = {}
    count = 0
    # max_win_rate = (0, 0)
    for result in results:
        win_time = result["WinTime"]
        win_rate = result["WinRate"]
        count += result["Count"]
        if win_time not in times:
            times[win_time] = win_rate
        else:
            times[win_time] += win_rate
        
        # if times[win_time] > max_win_rate[0]:
        #     max_win_rate = (times[win_time], win_time)
    return times, count

def get_win_rate_over_time(team, opponent):
    team, team_count = get_time_given_selections_by_winrate(team, opponent)
    opponent, opponent_count = get_time_given_selections_by_winrate(opponent, team)
    
    keys = sorted(team.keys())

    win_rates = []
    optimal_win_time = (0, -9999999)
    for key in keys:
        team[key] /= 7
        opponent[key] /= 7
        win_rate = team[key] - opponent[key]
        if win_rate > optimal_win_time[1]:
            optimal_win_time = (key, win_rate)

        win_rates.append(win_rate)
    # plt.ion()
    # plt.plot(keys, win_rate_blue, "b")
    # plt.plot(keys, win_rate_red, "r")
    # plt.show()
    return {"win_rates": win_rates, "optimal_win_time": optimal_win_time[0], "max_win_rate": optimal_win_time[1], "count": team_count + opponent_count}
    

# team = {"TOP": "Aatrox", "JUNGLE": "Warwick", "MID": "Zed", "DUO_CARRY": "Tristana", "DUO_SUPPORT": "Leona"}
# enemy = {"TOP": "Riven", "JUNGLE": "Sejuani", "MID": "Zed", "DUO_CARRY": "Vayne", "DUO_SUPPORT": "Nami"}
# print(get_win_rate_over_time(team, enemy))