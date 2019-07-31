""" Steam communication

Methods:
    getServerListSteam(ip_list : string) : list
    getServerInfoSteam(ip, steam_port) : dictionary


By: github.com/iamflea
Licence: who cares July 2019
"""
import socket
from steam import game_servers as gs

from config import *

QUERY_STEAM_APP = r'\appid\322330'

''' Get all servers having `ip` '''
def getServerListSteam(ip):
    #print("getServerListSteam()")
    result = []
    try:
        for address in gs.query_master(QUERY_STEAM_APP, STEAM_SERVERLIST_TIMEOUT_MS):
            if address[0] == ip:
                server = gs.a2s_info(address)
                if server['visibility'] == 0:
                    result += [(address, server)]
    except socket.timeout as e:
        #print("Socket timeout")
        pass
    # Sort the result by server name.
    if result:
        result.sort(key = lambda item: item[1]['name'])
        result = result[:MAX_SERVER_LENGTH]
    return result

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
