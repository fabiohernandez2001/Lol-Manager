import requests
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("RIOT_API_KEY")
#Todas las funciones requieren de una API_Key como esta

#Función que devuelve el uuid, icono y nivel del usuario aportando username y tag. Se puede modificar para que devuelva cualquiera de los otros campos nombrados

def get_puuid(name, tag, api_key):
    api_url  = f'https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}?api_key={api_key}'
    res = requests.get(api_url, timeout=10)
    player_info = res.json()
    player_uuid = [player_info['puuid']]
    return(player_uuid)

# print(get_puuid("koldi","doggy",api_key))
#Ejemplo

PUUID = get_puuid("koldi", "doggy", api_key)
# print( "get_uuid devuelve:", PUUID)

#Función que devuelve el icono y nivel del summoner

def get_icon_lvl (puuid, api_key):
    icon_url = f"https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}?api_key={api_key}"
    res =  requests.get(icon_url, timeout=10).json()
    icon_id =res["profileIconId"]
    icon = f"https://static.bigbrain.gg/assets/lol/riot_static/15.20.1/img/profileicon/{icon_id}"
    lvl = res["summonerLevel"]
    return icon, lvl

#Ejemplo
# print( "Get_icon_lvl devuelve: ", get_icon_lvl(PUUID, api_key))

#Función que devuelve una cantidad de matchs ids personalizables a partir del count a partir del UUID obtenido medienta el get_puuid().
#No estoy seguro de si hay que modificar algo para que lo devuleva en formato string tal como está ahora.

def matches_ids(id, api_key, start, count):
    matchlist_url = f"https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{id}/ids?type=ranked&start={start}&count={count}&api_key={api_key}"
    res = requests.get(matchlist_url, timeout=10).json()
    return res

#Ejemplo
Matches = matches_ids(PUUID, api_key, 0, 5)
# print( "Estos son los match id de las últimas 5 partidas de koldi : " + ", ".join(Matches))

#Función que devuelve toda la información respecto a una partida a partir de un Match ID.
# Para extraer datos específicos consultar https://developer.riotgames.com/apis#match-v5/GET_getMatch

def match_info(id, api_key):
    match_url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{id}?api_key={api_key}"
    res = requests.get(match_url, timeout=10)
    match_info = res.json()
    return match_info

#Ejemplo
Game = match_info(Matches[0], api_key)
participants = []
for player in Game["info"]["participants"]:
    participants.append(player['riotIdGameName'])
print("Estos son los nombres de usuario de cada participante de la partida: "+ ", ".join(participants))

def timeline(matchid, api_key):
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{matchid}/timeline?api_key={api_key}"
    res = requests.get(url, timeout=10)
    return res.json()

#Ejemplo
with  open("test.json", "w") as a:
    a.write(str(timeline(Matches[0], api_key)))
# print("Esto es todo lo que devuelve la api relacionado al timeline:\n ", timeline(Matches[0], api_key))

#Devuelve los datos de Flex y soloQ de la ultima season
def get_all_ranks(Puuid, api_key):
    url = f"https://euw1.api.riotgames.com/lol/league/v4/entries/by-puuid/{Puuid}?api_key={api_key}"
    res = requests.get(url, timeout=10).json()
    Ranked_Flex = [res[0]["queueType"],res[0]["tier"], res[0]["rank"], res[0]["leaguePoints"], res[0]["wins"], res[0]["losses"] ]
    SoloQ = [res[1]["queueType"],res[1]["tier"], res[1]["rank"], res[1]["leaguePoints"], res[1]["wins"], res[1]["losses"] ]
    return Ranked_Flex, SoloQ

#Ejemplo
# res = get_all_ranks(PUUID, api_key)
# print(res)

#Completar que por cada game saque toda la informacion relacionada a
#cada participante para posteriormente guardarlo en la db.
games= matches_ids(PUUID, api_key,0, 1)

for game in games:
    consulta = match_info(game, api_key)
    gameid = consulta["metadata"]["matchId"]
    participants = consulta["info"]["participants"]
    for participant in participants:
        print(gameid,
              consulta["info"]["gameMode"],
              participant["puuid"],
              participant["win"],
              participant["kills"],
              participant["deaths"],
              participant["assists"],
              participant["championId"],
              participant["item0"],
              participant["item1"],
              participant["item2"],
              participant["item3"],
              participant["item4"],
              participant["item5"],
              participant["item6"],
              "Faltan runas",
              "falta el skill order",
              participant["totalMinionsKilled"],
              participant["wardsPlaced"],
              participant["visionScore"],
              participant["totalDamageDealt"],
              participant["totalDamageTaken"],
              participant["totalHeal"],
              participant["damageSelfMitigated"],
              participant["goldEarned"],
              participant["lane"],
              participant["perks"]["styles"],
              participant["perks"]["statPerks"] )
