# Remove if you want to publish this!
DISCORD_TOKEN = ''

KLEI_TOKEN = "" # seems to be base 64

# Public channel name... Maybe remove? 
# CHANNEL_NAME_PUBLIC = 'dst-info' # 

# Private / admin channel name 
CHANNEL_NAME_PRIVATE = 'admin-dst-info'

# Saving file
JSON_FILENAME = './server_list.json'

# Maximal amount of servers in the list
MAX_SERVER_LENGTH = 10

# How long we browse lobbies in Steam API
STEAM_SERVERLIST_TIMEOUT_MS = 5000

CHECK_VERSIONS = False
VERSION_CHECKER_FILENAME = './version_checker/version.txt'

# Klei config
# Remove if you want to publish this!
KLEI_ID = ""
# Merge ID with TOken 
KLEI_TOKEN = f"pcl-usc^{KLEI_ID}^DontStarveTogether^{KLEI_TOKEN}"
# For performance porposes
KLEI_SERVER_LIST_FILENAME = './klei_list.json'
# Klei Cloud server list
KLEI_CLOUD_URL = "d2fr86khx60an2.cloudfront.net"
# Lobby json
KLEI_LOBBY_EU_URL = "lobby-eu.kleientertainment.com"


# Icons beep poop
GET_ICON = { 'N/A' : '···· ',
             '' : ':question:',
             'wilson': '<:wilson:604740107618091050>',
             'willow': '<:willow:604743774467391523>',
             'wolfgang': '<:wolfgang:604743736727044214>',

             'wendy': '<:wendy:604743838468276248>',
             'wx78': '<:wx78:604740705843412992>',
             'wickerbottom': '<:wickerbottom:604743867303985183>',

             'woodie' : '<:woodie:604743715877289998>',
             'wes' : '<:wes:604743790909063178>',
             'waxwell' : '<:maxwell:604745023052840972>',

             'wathgrithr' : '<:wathgrithr:604743691944591381>',
             'webber' : '<:webber:604743821028491294>',
             'winona' : '<:winona:604746132098121748>',
             'wortox' :  '<:wortox:604744137320824843>',
             'warly': '<:warly:604740689972035676>',
             'wormwood' : '<:wormwood:604743954319015956>',
             }