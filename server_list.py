import socket
import json
from collections import defaultdict

from config import *
from steam_list import *
from klei_list import * 



""" Server list is like dictionary of lists 

The logic behind:

serverList[int(SERVER_ID)] = LIST_OF_SERVERS

Methods usually returns a message which is processed by the bot 
"""
class ServerList(defaultdict):
    """ Inits dictionary, loads saved data """
    def __init__(self):
        super(ServerList, self).__init__(list)
        self.load()

    """ Load saved data from `JSON_FILENAME` """
    def load(self):
        self.clear(list)
        with open(JSON_FILENAME, 'r') as fp:
            discordServers = json.load(fp)
            for discordID in discordServers:
                self[int(discordID)] = discordServers[discordID]
    """ Save data into `JSON_FILENAME` """
    def save(self):
        with open(JSON_FILENAME, 'w') as fp:
            json.dump(self, fp)

    """ Removes the server list of `discordID` 
    
    @return string  A message for the bot
    """
    def clear(self, discordID):
        try:
            del self[discordID]
            self.save()
            return f'Cleared server list for this discord.'
        except KeyError:
            return '*Smeg*, server list seems to be empty.'

    """ Adds into the array an IP with specific port 
    
    @param discordID  int   
    @param ip  string
    @return string  A message for the bot
    """
    def add(self, discordID, ip, port=None):
        saved_servers = self[discordID]
        # Checks the maximum number of servers
        if len(saved_servers) >= MAX_SERVER_LENGTH:
            return f'*Smeg*, you already have {MAX_SERVER_LENGTH} servers in your list!'

        # Check if IP is in correct format
        try:
            socket.inet_aton(ip)
        except socket.error:
            return '*Smeg*, IP format is wrong'      



        # Resulting string and save format
        response = ''
        save_flag = False

        # Iterate through the servers 
        for server in getServerListSteam(ip):
            # We are finding for specific port
            if port is not None and int(port) != server[2]:
                continue
            # Save IP, port (for steam) and klei ID 
            rowID, servername = getServerRowID(server[0], int(server[2]))
            new_server = {'ip': server[0],
                          'port': server[1], # steam port
                          'kleiID_row' : rowID}

            # Check if the server is in the list
            if self.checkServer(discordID, new_server):
                # then we do not add it and print some message
                response += f'**Smeg**, `{server[0]}:{server[1]}` is already in the server list!\n'
                continue
            # Add server into the list
            self[discordID] += [new_server]
            # Set the flag, so we save 
            save_flag = True
            # Prints the message
            idx = str(len(self[discordID]))
            if rowID:
                response += f'Added `{server[0]}:{server[1]}` to sever list with number `{idx}` ({servername})  Klei row id = {rowID}\n'
            else:
                response += f'Added `{server[0]}:{server[1]}` to sever list with number `{idx}`  **Klei row id was not found!**\n'

        if response == '':
            return f'Couldn\'t find IP {ip} in steam server list.'

        # Some kind of update
        if save_flag:
            self.save()
            # Two threads one file? :o Inform admins to check server list
            response += 'This bot is *smeghead*. Please check the serverlist by typing command `.dst server`'
        else: 
            response += 'Meow! Nothing updated.'
        return response;
    

    """ Check if `discordID` is not in the main dictionary `self`

    @param disocrdID  int
    @return boolean  
    """
    def notExists(self, discordID):
        return discordID not in self or len(self[discordID]) == 0

    """ Check if `new_server` is in the list `self[discordID]` 

    @param discordID  int
    @param new_server  dictionary
    @return boolean
    """
    def checkServer(self, discordID, new_server):
        # Checks if `self[discordID]` exists
        if self.notExists(discordID):
            return False

        # Compare Klei ID rows. 
        # I suppose they should be unique
        if new_server['kleiID_row']:
            for dictionary in self[discordID]:
                if dictionary['kleiID_row'] == new_server['kleiID_row']:
                    return True
        else:
            # We didn't get `kleiID_row`
            # So we need to check ip and port
            for dictionary in self[discordID]:
                ip_equal = dictionary['ip'] == new_server['ip']
                port_equal = dictionary['port'] == new_server['port']
                if ip_equal and port_equal:
                    return True
        # We didn't find `new_server` in the `self[discordID]`
        return False

    """ Returns server list of specific `discordID`. 

    Return format: `{idx} > {ip}:{steam_port}  {klei_id_row}`

    @param discordID  int
    @return string
    """
    def serverList(self, discordID):
        result = ""
        # We read it from the file.. 
        # It may happen that we do updates in dictionary. 
        # HOwever the file is not updated 
        with open(JSON_FILENAME, 'r') as fp:
            jsonServers = json.load(fp)
            if str(discordID) not in jsonServers:
                return 'Server list is empty.'
            result = '```'
            for idx, server in enumerate(jsonServers[str(discordID)]):
                result += f"{str(idx).rjust(2)} >  {server['ip']}:{server['port']}  Klei ID row: {server['kleiID_row']}\n"
        result += '``` *The ports are for Steam API. They are different than game ports!*'
        return result

    

    """ Get information from single server which is determined by discordID and idx.

    Note that users don't know that array starts from 0! 
    
    @param discordID int
    @param idx int        Indexing starts from 1 
    @return tuple (`response`, `warning`)  where `response` and `warning` are strings
    """
    def getInfoSingleServer(self, discordID, idx, admin=False):
        # Lazy function 

        """ Returns `player` from `kleiPlayers` which has name `playerName`
        @param playerName string 
        @param kleiPlayers list of player dictionaries 
        """
        #print("Getting fun")
        def findInPlayers(playerName, kleiPlayers):
            for player in kleiPlayers:
                if player['name'] == playerName:
                    player['steamLink'] = f"https://steamcommunity.com/profiles/{player['netid']}"
                    return player
            return {'steamLink': '', 'prefab':'N/A'}

        # Get server dictionary
        try:
            server = self[discordID][idx-1]
        except (KeyError, IndexError):
            return [f'Couldn\'t find {idx} in the server list', '']

        # init values
        dSteam = {}
        dKlei = {}
        try:
            # Get steam info and klei info
            dSteam = getServerInfoSteam(server['ip'], server['port'])
            dKlei = getServerInfoKlei(server['kleiID_row'])
        except socket.error:
            # Fix dynamic IP address problem
            # Check if we didn't get steam info
            if dSteam == {}:
                # Try to get klei info 
                #print(server)
                try:
                    dKlei = getServerInfoKlei(server['kleiID_row'])
                    dSteam = getServerInfoSteam(dKlei['__addr'], server['port'])
                    # Load changes
                    self.load() 
                    # Update IP address. 
                    # Might be dynamic or changed by ISP
                    self[discordID][idx-1]['ip'] = dKlei['__addr']
                    # Save changes
                    self.save()
                except (socket.error, KeyError):
                    return 'Couldn\'t connect to the server!'

        # Set default values 
        try:
            day = f"{dKlei['data']['day']} ({dKlei['season']})"
            kleiPlayers = dKlei['players']
        except KeyError:
            day = "N/A"
            kleiPlayers = []
        
        # Render response
        totalPlayers = len(dSteam['players'])
        response = ''
        response += f"`.dst info {idx}` - **{dSteam['info']['name']}** "
        response += f"Day {day}\n"
        response += f"Total players: {dSteam['info']['players']}/{dSteam['info']['max_players']}\n"

        # Get longest name and day in the list
        if dSteam['players']:
            m_chars = max(map(len, [p['name'] for p in dSteam['players']]))
            m_chars_days = max(map(lambda x: len(str(x)), [p['score'] for p in dSteam['players']]))
        # TODO merge Klei list with Steam list in the future
        for player in dSteam['players']:
            # This might be buggy function
            kleiPlayer = findInPlayers(player['name'], kleiPlayers)
            # Get icon and name
            icon = GET_ICON[kleiPlayer['prefab']] 
            name = player['name'].replace('`', '\\`').ljust(m_chars, ' ')
            score = str(player['score']).rjust(m_chars_days, ' ')
            
            # Render it down
            response += f"`{kleiPlayer['steamLink']}` " if admin and kleiPlayer['steamLink'] else ''
            response += f"{icon} `{name}ᅚ{score} "
            if player['score'] == 1:
                response += f"day.`\n"
            else:
                response += f"days`\n"
        warning = None
        # Get version
        if CHECK_VERSIONS and int(dSteam['info']['version']) not in self.versions:
            warning = f"[Server {idx} with name `{dSteam['info']['name']}` is running an older version of DST!] Version {dSteam['info']['version']} is not {self.versions_str}.\n"
        
        return response, warning

    """ 
    @param discordID int
    @param idx int        Indexing starts from 1 
    @param admin bool     Shoul print admin stuff?
    @return `list` of tuples (`response`, `warning`)  where `response` and `warning` are strings
    """
    def getInfo(self, discordID, id=None, admin=False):
        if self.notExists(discordID):
            return 'This discord doesnt have binded any servers!'
        # Save versions
        if CHECK_VERSIONS:
            with open(VERSION_CHECKER_FILENAME, 'r') as f:
                self.versions = [int(line) for line in f]
                self.versions_str = ' or '.join(map(str,self.versions))
                

        if id is None:
            # Iterate through the list
            return [self.getInfoSingleServer(discordID, id, admin) for id in range(1, len(self[discordID]) + 1)]
        else:
            # `id` is set
            return [self.getInfoSingleServer(discordID, id, admin)]
            


        

# debugging porposes
if __name__ == '__main__':
    DFT = '94.76.229.42'
    DID = 42
    x = ServerList()
    print(x.clear(DID))
    print(x.add(DID, DFT))

    #print(x.getInfo(DID, admin=True))



