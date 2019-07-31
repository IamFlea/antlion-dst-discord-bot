HELP_MSG = '''
`.help`
Prints this help 

`.dst` OR `.dst info` OR `.dst whois`
Prints list of your servers, with a brief information - day, season, name.
Prints all players in the servers, player name, day, character

`.dst [n]` OR `.dst info [n]` OR `.dst whois [n]`
where n is an integer (number), prints information of your n-th server in the "list". 

'''

HELP_MSG_ADMIN = HELP_MSG + '''
**Hidden commands**

`.hello`
Prints hello world. Works also in public channel.

`.smeg`
You smeeee heeee. 

`.meow`
:cat:

**ADMIN ONLY**

`.dst server`
Prints server number, ip, Steam port and Klei row id.

`.dst server add [IP]`
Adds all servers having `[IP]` into your serverlist.

`.dst server add [IP:PORT]`
Adds single server having `[IP:PORT]` into your serverlist.
Note that Port is a game port.


`.dst server clear`
Remove all servers from the server list.

https://github.com/IamFlea/antlion-dst-discord-bot
'''

HELP_MSG += "\nhttps://github.com/IamFlea/antlion-dst-discord-bot"