""" Steam communication

Methods:
    getServerListSteam(ip_list : string) : list
    getServerInfoSteam(ip, steam_port) : dictionary


By: github.com/iamflea
Licence: who cares July 2019
"""
import socket
import http.client
import json 
from steam import game_servers as gs


from config import *

#QUERY_STEAM_APP = r'\appid\322330'

''' Get all servers having `ip` '''
# https://94.76.229.42
def getServerListSteam(ip):
    # Connect
    conn = http.client.HTTPSConnection('api.steampowered.com', 443)
    conn.request("GET", f'/ISteamApps/GetServersAtAddress/v1/?addr={ip}')
    res = conn.getresponse()
    # Check if everything is all right
    if res.status != 200: 
        return []
    # Get data and close connection
    data = res.read()
    conn.close()
    # Get json data
    data = json.loads(data)
    try:
        servers = data['response']['servers']
    except (KeyError, IndexError):
        return []
    for s in servers:
        #print(s)
        try:
            if s['appid'] == 322330:
                ip, port = s['addr'].split(':')
                yield (ip, int(port), int(s['gameport']))
        except (KeyError, IndexError, ValueError):
            continue


""" Get steam info 

@param `ip` string, IP address 
@param `port`  int, port for STEAM (not same as DST port)
"""
def getServerInfoSteam(ip, port):
    #print("getServerInfoSteam()")
    server = (ip, int(port))
    return {"info": gs.a2s_info(server),
            "players": gs.a2s_players(server),
            "rules": gs.a2s_rules(server)}


if __name__ == '__main__':
    #import print
    DFT = '94.76.229.42'
    DST_EU = '46.101.212.23'
    x = getServerListSteam(DFT)
    t = list(x)
    print("---") 
    print(t)