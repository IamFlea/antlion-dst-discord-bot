Ladies and gantleman, 

I present you 

# Antlion bot for Discord servers!

It is not a boss. It is a bot. 

Player just type `.dst` and the bot prints down online players. See: 

![Discord bot in the action](https://i.imgur.com/pvrRqwu.png)


## Setting up Discord
1. Invite bot to your server
2. You need to create one Discord channel `#admin-dst-info` with permission for that bot.
3. Type `.dst server add {dst-ip}` in `#admin-dst-info`
4. You can type `.dst` anywhere channels in order to get the list of online players.

## Discord public commands
```.dst``` 

Prints list of your servers, with a brief information - day, season, name.
Prints all players in the servers, player name, day, character
If there is a DST version mismatch, the bot can print it below the list. 

```.dst [n]```

where `n` is an integer (number), prints information of your `n`-th server in the "list". 

```.meow```

prints :cat:

```.help```

Prints some smeggy help.

```.smeg```

Red dwarf! 

## Discord private commands
```.dst server```

Prints saved server number, ip, Steam port and Klei row id.

```.dst server add [IP]```

Adds all servers having `[IP]` into your serverlist.

```.dst server add [IP:PORT]```

Adds single server having `[IP:PORT]` into your serverlist.
Note that Port is a game port.

```.dst server clear```

Remove all servers from the server list.

# Known bugs 
## Help, bot didn't find Klei row ID!
The bot parses Steam servers only which are NOT based in China region due to performace.

## Help, bot doesn't print days nor selected character!
Solution: spam **Klei** boys! 
They haven't give me pernament client token, yet :( 

# Coding stuff
## Installing 
1. Download the source codes
2. The project was programmed for Python 3.7.3
3. Run `pip install discord, steam`
4. You should run python ./version_checker/version.py in corn periodically (15 minutes is ok).
5. Generate Discord token, spam Klei for pernament client token. Set it up in `config.py`
6. Run `python ./bot.py`

## File description

```bot.py```  

Use discord API and parse user's input data

```server_list.py```

For each server, the script creates a list of game servers. The server is represented as `(ip, steamPort, KleiRow_ID)`.

```steam_list.py```

Utilizes Steam API, doc: https://steam.readthedocs.io/en/stable/  Uses `ip` and `steamPort`

```klei_list.py```

Getting the list of lobbies does not require Klei token `getServerRowID(ip, dstPort)`. 
However if you would like to get the detailed information `getServerInfoKlei(rowID)`, you need to set Klei's token at `config.py`. 

```config.py```

Basic config.

```const.py```

Help strings.

```./version_checker/```

Older script that checks current version of DST. 
