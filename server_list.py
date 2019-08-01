import socket
import json
from collections import defaultdict
from itertools import zip_longest

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
        try:
            with open(JSON_FILENAME, 'r') as fp:
                discordServers = json.load(fp)
                for discordId in discordServers:
                    self[int(discordId)] = discordServers[discordId]
        except FileNotFoundError:
            pass
    """ Save data into `JSON_FILENAME` """
    def save(self):
        with open(JSON_FILENAME, 'w') as fp:
            json.dump(self, fp)

    """ Removes the server list of `discordId` 
    
    @return string  A message for the bot
    """
    def clear(self, discordId):
        try:
            del self[discordId]
            self.save()
            return f'Cleared server list for this discord.'
        except KeyError:
            return '*Smeg*, server list seems to be empty.'


    """ Adds into the array an IP with specific port 
    
    @param discordId  int   
    @param ip  string
    @return string  A message for the bot
    """
    def add(self, discordId, ip, port=None):
        saved_servers = self[discordId]
        # Checks the maximum number of servers
        if len(saved_servers) >= MAX_SERVER_LENGTH:
            return f'*Smeg*, you already have {MAX_SERVER_LENGTH} servers in your list!'

        # Check if IP is in correct format
        try:
            socket.inet_aton(ip)
        except socket.error:
            return '*Smeg*, IP format is wrong'      

        # Get server ports from Steam API having this IP 
        steamServers = list(getServerListSteam(ip))
        # Get server info from Klei API 
        kleiServers = list(filter(lambda s: s is not None, [getServerRowID(server[0], server[2]) for server in steamServers]))

        # I am sorry for nested def -.- 
        # I would use some oneliner, however it wouldn't be readable as this
        def findSteamPort(ip, port, serverList=steamServers):
            for server in serverList:
                if ip == server[0] and port == server[2]: # remove ip? 
                    return int(server[1])
        # Function that creates dictionary from IP, port and adds steamport
        getServer = lambda ip, port: (ip, port, findSteamPort(ip, port))

        response = ''
        save_flag = False
        for server in kleiServers:
            # Skip unwanted servers
            if port is not None and int(port) != server['port']:
                continue

            rowId = server['__rowId']
            if self.isInList(discordId, rowId):
                response += f"**Smeg!** {server['name']} is already in the server list with address `{server['__addr']}:{server['port']}`, `{rowId}`!\n"
                continue
            # Master server is first
            servers = [getServer(server['__addr'], server['port'])]
            # Slaves are appended
            slaves = server['slaves']
            slaves = [(slaves[key]['__addr'], int(slaves[key]['port'])) for key in slaves]
            servers += list(map(lambda x: getServer(*x), slaves))
            # Add server into the list
            self[discordId] += [{'rowId': rowId, 'servers': servers}]
            save_flag = True
            response += f"Added *{server['name']}* `{rowId}` to sever list with number **{len(self[discordId])}**. `{str(servers)}`\n"

        if response == '':
            return f'Couldn\'t find IP {ip} in the Klei or Steam server list.'

        if save_flag:
            self.save()
            # Two threads one file? :o Inform admins to check server list
            response += 'This bot is *smeghead*. Please check the serverlist by typing command `.dst server` in this channel'
        else: 
            response += 'Meow! Nothing updated.'
        return response

    """ Check if `discordId` is not in the main dictionary `self`

    @param disocrdID  int
    @return boolean  
    """
    def notExists(self, discordId):
        return discordId not in self or len(self[discordId]) == 0

    """ Check if `rowId` is in the list `self[discordId]` 

    @param discordId  int
    @param rowId   string
    @return boolean
    """
    def isInList(self, discordId, rowId):
        # Checks if `self[discordId]` exists
        if self.notExists(discordId):
            return False

        for dictionary in self[discordId]:
            # Found the needle
            if dictionary['rowId'] == rowId:
                return True
        return False 

    """ Returns server list of specific `discordId`. 

    Return format: `{idx} > {ip}:{steam_port}  {klei_id_row}`

    @param discordId  int
    @return string
    """
    def serverList(self, discordId):
        result = ""
        # We read it from the file.. 
        # It may happen that we do updates in dictionary. 
        # HOwever the file is not updated 
        try:
            with open(JSON_FILENAME, 'r') as fp:
                jsonServers = json.load(fp)
                if str(discordId) not in jsonServers:
                    return 'Server list is empty.'
                result = '```\n'
                result += '| ID |                      Klei Row ID | Master Server IP | DSTPort | SteamPort |  Slave Server IP | DSTPort | SteamPort |\n'
                #          |                                         1234123412341234    123456 |    123456 | 1234123412341234 |  123456 |    123456 |
                for idx, server in enumerate(jsonServers[str(discordId)]):
                    result += f"| {str(idx+1).rjust(2)} | {server['rowId']} | "
                    #{str(list(map(tuple, server['servers'])))}
                    for ip, gamePort, steamPort in server['servers']:
                        ip = ip.rjust(16, ' ')
                        gamePort = str(gamePort).rjust(7, ' ')
                        steamPort = str(steamPort).rjust(9, ' ')
                        result += f'{ip} | {gamePort} | {steamPort} | '
                    result += "\n"
        except FileNotFoundError:
            return 'Server list is empty.'

        result += '``` '
        return result

    

    """ Get information from single server which is determined by discordId and idx.

    Note that users don't know that array starts from 0! 
    
    @param discordId int
    @param idx int        Indexing starts from 1 
    @return tuple (`response`, `warning`)  where `response` and `warning` are strings
    """
    def getInfoSingleServer(self, discordId, idx, admin=False):
        # Lazy function 

        """ Returns `player` from `kleiPlayers` which has name `playerName`

        Be glad python doesn't have `goto` statement

        @param playerName string 
        @param kleiPlayers list of player dictionaries 
        """
        def findInPlayers(playerName, kleiPlayers):
            for player in kleiPlayers:
                if player['name'] == playerName:
                    player['steamLink'] = f"https://steamcommunity.com/profiles/{player['netid']}"
                    return player
            return {'steamLink': '', 'prefab':'N/A'}

        # Get server dictionary
        try:
            server = self[discordId][idx-1]
        except (KeyError, IndexError):
            return [f'Couldn\'t find {idx} in the server list', '']

        #print(server)
        # init values
        dSteam = {}
        dKlei = {}
        try:
            # Get steam info and klei info
            dSteam = getServerInfoSteam(server['servers'][0][0], server['servers'][0][2])
            for player in dSteam['players']:
                player['cave'] = False
            # Merge players and find out who is in the caves
            for slave in server['servers'][1:]:
                for player in getServerInfoSteam(slave[0], slave[2])['players']:
                    player['cave'] = True
                    dSteam['players'] += [player]


            dKlei = getServerInfoKlei(server['rowId'])
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
                    self[discordId][idx-1]['ip'] = dKlei['__addr']
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
                response += f"day.`"
            else:
                response += f"days`"
            if player['cave']:
                response += '<:minerhat:606489390457421855>' 
            response += "\n"
        #response = response + response + response + response +response + response + response + response +response + response + response + response +response + response + response + response +response + response + response + response 
        #warning = ''
        # Get version
        #if CHECK_VERSIONS and int(dSteam['info']['version']) not in self.versions:
        #    warning = f"[Server {idx} with name `{dSteam['info']['name']}` is running an older version of DST!] Version {dSteam['info']['version']} is not {self.versions_str}.\n"
        
        return response, ''

    """ 
    @param discordId int
    @param idx int        Indexing starts from 1 
    @param admin bool     Shoul print admin stuff?
    @return `list` of tuples (`response`, `warning`)  where `response` and `warning` are strings
    """
    def getInfo(self, discordId, id=None, admin=False):
        if self.notExists(discordId):
            return 'This discord doesnt have binded any servers!'
        # Save versions
        if CHECK_VERSIONS:
            with open(VERSION_CHECKER_FILENAME, 'r') as f:
                self.versions = [int(line) for line in f]
                self.versions_str = ' or '.join(map(str,self.versions))
                

        if id is None:
            # Iterate through the list
            result = [self.getInfoSingleServer(discordId, id, admin) for id in range(1, len(self[discordId]) + 1)]
        else:
            # `id` is set
            result = [self.getInfoSingleServer(discordId, id, admin)]
        # beep boop
        _text = ''
        _warning = ''
        for t, w in result: 
            if t[-1] != '\n':
                t += '\n'
            _text += t
            if w:
                if w[-1] != '\n':
                    w += '\n'
                _warning += w

        return list(zip_longest(self.strDecompose(_text), self.strDecompose(_warning), fillvalue=""))



    

    """ Decompose long string into a list of strings ended with new line character `\n` or end of line `\x00`

    Rises an MemoryError if any line is longer than horse's penis.
    """
    def strDecompose(self, string):

        #string = "`.dst info 2` - **Don't Fight Together 2** Day N/A\nTotal players: 20/20\n<:minerhat:606489390457421855>  `       Zero III      ᅚ11 days`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       Zero III      ᅚ11 days`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       Ewaly ≡       ᅚ11 days`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       Numbskull     ᅚ 6 days`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       NukePigg      ᅚ 9 days`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       Shinra        ᅚ 9 days`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       kiba23x       ᅚ 9 days`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       TinObama      ᅚ 3 days`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       Publisher 2016ᅚ 5 days`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       WHITENIGGA    ᅚ 5 days`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       Kova          ᅚ 1 day.`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       Zero III      ᅚ11 days`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       Zero III      ᅚ11 days`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       Ewaly ≡       ᅚ11 days`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       Numbskull     ᅚ 6 days`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       NukePigg      ᅚ 9 days`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       Shinra        ᅚ 9 days`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       kiba23x       ᅚ 9 days`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       TinObama      ᅚ 3 days`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       Publisher 2016ᅚ 5 days`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       WHITENIGGA    ᅚ 5 days`<:minerhat:606489390457421855>\n<:minerhat:606489390457421855>  `       Kova          ᅚ 1 day.`<:minerhat:606489390457421855>"
        # One long line => error
        #string = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        # `\n` is in 1998-th position 
        #string = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n"
    
        #string = "meow"
        # Discord allows maximally 2000 characters. Encoding in that case was UTF-8!  
        # If Discord codign monkeys change it to ASCII, then the BUG is possible here!
        # However, to prevent some possible bugs and errors in development of this script 
        # I reduced it by two. Meow meow. :cat:
        BUFFER_LENGTH = 1998
        
        # Main index! 
        idx = 0
        string_length = len(string)
        
        # Skip the dog
        if string_length < BUFFER_LENGTH:
            return [string[idx:]]
    
        result = []
            
        # Since this is while loop I put here some kind of watchdog 
        # Note that we don't kick the dog
        # Message can be 1 998 000 characters long. 
        meow = 0 
        while True:
            if meow > 1000: 
                # Kova is retard
                raise RecursionError('Too many meows in one loop!') 
            meow += 1
    
            # Append everything if the buffer is long enough 
            if string_length - idx < BUFFER_LENGTH:
                #print("waat")
                result += [string[idx:]]
                break
    
            # Get the last index of new line character `\n`
            last_idx = string.rfind('\n', idx, idx + BUFFER_LENGTH)  
    
            # Did we found the ending character? 
            if last_idx == -1 or last_idx == string_length - 1:
                #print("too")
                # There is still something to parse => remove buffer 
                if last_idx - idx +1 < BUFFER_LENGTH:
                    raise MemoryError(f"Can not print message longer than {BUFFER_LENGTH} characters")
                result += [string[idx:]]
                break
            # Append the substring ended with `\n`
            result += [string[idx:last_idx + 1]]
            # Add index
            idx = last_idx + 1
            # Repeat
        # while True ends
        return result
    #for i in x:
    #    x = decompose(string)
    #    print(len(i), x)


            


        

# debugging porposes
if __name__ == '__main__':
    SERVERS = ['217.182.197.183', '94.76.229.42']
    DID = 42
    x = ServerList()
    print(x.serverList(DID))
    print(x.getInfoSingleServer(DID, 3)[0])
    print("---Clearing---")
    print(x.clear(DID))
    print(x.add(DID, SERVERS[1], 11000))
    print(x.serverList(DID))
    print(x.add(DID, SERVERS[1]))
    print(x.add(DID, SERVERS[0]))
    print(x.serverList(DID))
    #print(x.getInfoSingleServer(DID, 2)[0])
    print(x.getInfo(DID, admin=True))
    for info, warn in x.getInfo(DID, admin=True):
        print(len(info), len(warn))



