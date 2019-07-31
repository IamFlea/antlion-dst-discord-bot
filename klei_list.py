""" Klei rowid communication

Methods:
* getRegionalLobbies(ip_list) : list
* getServerInfoStea(ip, steam_port) : dictionary


By: github.com/iamflea
Licence: who cares July 2019
"""
import http.client
import json 
from config import *

import zlib
import re

import os.path as op # For checking when the file `KLEI_SERVER_LIST_FILENAME` was modified
import datetime as dt


# Not sure if this is correct address

KEY_REGEX = re.compile(r'<Key>([^<]*)</Key>')

""" Get lobbies from regionPathURL 
@param regionPatnURL  string
@return  JSON data (list)
"""
def getRegionalLobbies(regionPathURL):
    # Parse only `.json.gz` files
    if not regionPathURL.endswith(".json.gz"):
        return []
    #print(regionPathURL)
    # Parse steam versions
    if not "Steam" in regionPathURL:
        return []
    # China: 1989: Man vs. Chinese tank Tiananmen square 
    if "China" in regionPathURL: 
        return [] # sudo make revolution 

    # Connect
    conn = http.client.HTTPSConnection(KLEI_CLOUD_URL, 443)
    conn.request("GET", f'/{regionPathURL}')
    res = conn.getresponse()
    # Check if everything is all right
    if res.status != 200: 
        return []
    # Get data and close connection
    data = res.read()
    conn.close()
    # Deflate and parse json 
    data = zlib.decompress(data, zlib.MAX_WBITS|32).decode("utf-8") 
    data = json.loads(data)['GET']
    if data is None:
        return []
    else:
        return data

    
""" Get lobbies regions from the cloud. 
@raise StopIteration
@yield Region from a cloud
"""
def getRegions(): 
    #print("Getting new list")
    # Connect
    conn = http.client.HTTPSConnection(KLEI_CLOUD_URL, 443)
    conn.request("GET", '/')
    res = conn.getresponse()
    
    if res.status != 200: 
        raise StopIteration
    
    data = res.read()
    data = data.decode("utf-8") # TEST comment it?
    conn.close()

    # Here we have some server groups 
    for i in re.finditer(KEY_REGEX, data):
        yield i.group(1) 


""" Returns list of lobbies """ 
def getLobbies():
    return [lobby for region in getRegions() for lobby in getRegionalLobbies(region)]

""" Load servers from file, if needed 
@return list of lobbies (servers)
"""
def getServerListKlei():
    # Get time of the last modification of `KLEI_SERVER_LIST_FILENAME`
    t = op.getmtime(KLEI_SERVER_LIST_FILENAME)
    # If the file is older than 10 minutes, we will update it
    needUpdate = dt.datetime.fromtimestamp(t) < dt.datetime.now() - dt.timedelta(minutes=60)
    if needUpdate:
        # Load new lobbies
        lobbies = getLobbies()
        # Save lobbies into the file
        with open(KLEI_SERVER_LIST_FILENAME, 'w') as fp:
            json.dump(lobbies, fp)
        # Return lobbies
        return lobbies
    else: 
        # We updated the list racently 
        with open(KLEI_SERVER_LIST_FILENAME, 'r') as fp:
            return json.load(fp)

""" Get server's Klei row id
@param ip string
@param port int   DST game port (Do not mistake with Steam port)
@return string    klei row id
"""
def getServerRowID(ip, port):
    port = int(port)
    for lobby in getServerListKlei(): 
        if lobby['__addr'] == ip and int(lobby['port']) == port:
            #print(server)
            return lobby['__rowId']




""" Lua string to dictionary """
def parsePlayerNames(names):
    # remove `return {...}` and makes it list `[...]`
    names = "["+names[8:-1]+"]" 
    #print(names)
    x = re.sub(r"{\n *colour=", '{"colour":',names)
    x = re.sub(r",\n *eventlevel=", ',"eventlevel":',x)
    x = re.sub(r",\n *name=", ',"name":',x)
    x = re.sub(r",\n *netid=", ',"netid":',x)
    x = re.sub(r",\n *prefab=", ',"prefab":',x)
    return json.loads(x)

""" Lua string to dictionary """
def parseData(data):
    data = data[7:]
    x = re.sub(r" *day=", '"day":',data)
    x = re.sub(r" *dayselapsedinseason=", '"dayselapsedinseason":',x)
    x = re.sub(r" *daysleftinseason=", '"daysleftinseason":',x)
    return json.loads(x)

""" Returns server info in JSON format  (Klei API?)

Returns empty dictionary on error

@param string rowID
@return dictionary (json)
"""
def getServerInfoKlei(rowID):
    #print("getServerInfoKlei()")
    # Is it walid row ID?
    if rowID == '':
        return {}

    # Prepare connection and 
    conn = http.client.HTTPSConnection(KLEI_LOBBY_EU_URL, 443)
    post = { "__gameId": "DontStarveTogether", 
                "__token": KLEI_TOKEN,  # How the hack can i get token 
                "query": {
                    "__rowId": rowID
                }
            }
    
    conn.request("POST", '/lobby/read', json.dumps(post))
    res = conn.getresponse()
    # If everything is all right, then parse data, else returns the stuff 
    if res.status != 200: 
        return {}
    data = res.read()
    conn.close()
    data = json.loads(data)
    if 'error' in data: # AUTH_ERROR_E_EXPIRED_TOKEN
        return {}
    data = data['GET'][0]
    data['players'] = parsePlayerNames(data['players'])
    data['data'] = parseData(data['data'])
    return data 

if __name__ == '__main__':
    getServerListKlei()
    x = getServerRowID('94.76.229.42', 11000)
    print(x)
    #print(getServerInfoKlei('waat'))
    pass
    
