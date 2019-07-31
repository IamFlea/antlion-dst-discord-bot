import discord
import json
import socket

from server_list import ServerList
from config import *
from const import *

#import cProfile


client = discord.Client()

dst_server_list = ServerList()

async def commands(message): 
    channel_name = message.channel.name
    # Sets admin boolean, if we are on private/admin channel
    ch_admin = channel_name == CHANNEL_NAME_PRIVATE
    # Checks if we are not in public or private channel
    #if channel_name != CHANNEL_NAME_PUBLIC and ch_admin == False:
    #    return

    #print("parsing command")
    # Get command and guid
    command = message.content
    guild_id = message.channel.guild.id

    ###################
    # PUBLIC COMMANDS #
    ###################

    # Hello worlds
    ###############
    if command.startswith('.hello'):
        response = 'Hello cruel world! I am the soulless finite state automaton.'

    elif command.startswith('.smeg'):
        response = 'https://tenor.com/t8qc.gif'

    elif command.startswith('.meow'):
        response = ":cat: Meow meow, I am dangerous kitten."

    # Printing help - difference between admin and normal channel
    ###############
    elif command.startswith('.help'):
        response = HELP_MSG_ADMIN if ch_admin else HELP_MSG

    # Printing who is online
    ########################
    elif command.startswith('.dst info'):
        try:
            id_ = int(command[10:])
        except ValueError: 
            id_ = None
        #response = cProfile.runctx('dst_server_list.getInfo(guild_id, id=id_, admin=ch_admin)', {'guild_id' : guild_id, 'id_':id_, 'ch_admin':ch_admin, 'dst_server_list': dst_server_list}, {})
        response = dst_server_list.getInfo(guild_id, id=id_, admin=ch_admin)
        if isinstance(response, list):
            w = ''
            for text, warning in response:
                await message.channel.send(text)
                if warning:
                    w += warning
            if w:
                await message.channel.send(f'```css\n{w}```')
            return


    elif command.startswith('.dst whois'):
        try:
            id_ = int(command[11:])
        except ValueError: 
            id_ = None
        #response = cProfile.runctx('dst_server_list.getInfo(guild_id, id=id_, admin=ch_admin)', {'guild_id' : guild_id, 'id_':id_, 'ch_admin':ch_admin, 'dst_server_list': dst_server_list}, {})
        response = dst_server_list.getInfo(guild_id, id=id_, admin=ch_admin)
        if isinstance(response, list):
            w = ''
            for text, warning in response:
                await message.channel.send(text)
                if warning:
                    w += warning
            if w:
                await message.channel.send(f'```css\n{w}```')
            return


    ###########################
    # Administration commands #
    ###########################

    # Adding a server
    #################
    elif ch_admin and command.startswith('.dst server add '):
        sec = (STEAM_SERVERLIST_TIMEOUT_MS // 1000) + 1
        await message.channel.send(f'It will take about {sec*2} seconds to find this server in the server lists.')
        ip_port = command[16:]
        try: 
            ip, port = ip_port.split(':')
            response = dst_server_list.add(guild_id, ip, int(port))
        except ValueError:
            response = dst_server_list.add(guild_id, command[16:])
    
    # Clearing the servers
    elif ch_admin and command.startswith('.dst server clear'):
        response = dst_server_list.clear(guild_id)

    # Server list
    elif ch_admin and command.startswith('.dst server'):
        response = dst_server_list.serverList(guild_id)

    ################
    # Public again #
    ################

    # Printing who is online
    ########################
    elif command.startswith('.dst'):
        try:
            id_ = int(command[5:])
        except ValueError: 
            id_ = None
        #response = cProfile.runctx('dst_server_list.getInfo(guild_id, id=id_, admin=ch_admin)', {'guild_id' : guild_id, 'id_':id_, 'ch_admin':ch_admin, 'dst_server_list': dst_server_list}, {})
        response = dst_server_list.getInfo(guild_id, id=id_, admin=ch_admin)
        if isinstance(response, list):
            w = ''
            for text, warning in response:
                await message.channel.send(text)
                if warning:
                    w += warning
            if w:
                await message.channel.send(f'```css\n{w}```')
            return

    else:
        return
    await message.channel.send(response)


@client.event
async def on_message(message):
    #if message.content.lower() == "meow":
    #    message.channel.send(':cat:')        
    # Lie: We check if the content starts with Pacman's favourite character `.`
    # Truth: This is our special character for this bot. Should improve performance
    try:
        if message.content[0] != '.': 
            return 
    except IndexError: # Sometimes it parses empty messages, wtf? 
        print("Empty msg")
        return
    # Lie: Protection of robots killing all humans
    # Truth: We do not want bots replying to themselves
    # if message.author == client.user:
    if message.author.bot:
        return

    # Lie: Use deep learning so the bot passes Turing test.
    # Truth: Process the incoming message in one big if condition.
    await commands(message)


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run(DISCORD_TOKEN)
