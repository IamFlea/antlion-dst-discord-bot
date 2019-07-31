"""
Finds if there is any new version of DST. 


Possible improvements:
  - Use websocket and steam API 
  - Check version from game files

Script made by Petr Dvoracek 2019 

github.com/iamflea
"""
import datetime
import re
import http.client
import traceback
import json 
import os
import sys


_DISCORD_WEBHOOK_URL_ = "https://discordapp.com/api/webhooks/575624544195444756/wAuKREMkYZZJxvZRJCDnIDWkf1XlPNeDwlzOTPYePjtQKc9cDu1ssX5noK9J4iFk0i4Q"

#_PATH_LATEST_VERSION_FILENAME_ = 'c:\\Program Files (x86)\\Steam\\steamapps\\common\\Don\'t Starve Together\\version.txt'
_PATH_LATEST_VERSION_FILENAME_ = 'version.txt'

# This utilizes web parsing.. And it is slower for process
_KLEI_UPDATES_URL_ = 'forums.kleientertainment.com'
_KLEI_UPDATES_PATH_ = '/game-updates/dst/'
_KLEI_UPDATES_PORT_ = 443

# negative - errors 
# positive - new stuff
EXIT_CODE = {
    'PARSE_ERROR' : -4,
    'FILE_NOT_UPDATED' : -3,
    'DISCORD_UNAVAILABLE' : -2,
    'UNKNOWN_ERROR' : -1,
    'ALL_OK' : 0,
    'TEXT_FILE_NOT_FOUND' : 1,
    'NEW_TEST_VERSION' : 2,
    'NEW_RELEASE_VERSION' : 3,
}

def sendToDiscord(message):
    # your webhook URL
    global _DISCORD_WEBHOOK_URL_

    # compile the form data (BOUNDARY can be anything)
    formdata = "------:::BOUNDARY:::\r\nContent-Disposition: form-data; name=\"content\"\r\n\r\n" + message + "\r\n------:::BOUNDARY:::--"
  
    # get the connection and make the request
    connection = http.client.HTTPSConnection("discordapp.com")
    connection.request("POST", _DISCORD_WEBHOOK_URL_, formdata, {
        'content-type': "multipart/form-data; boundary=----:::BOUNDARY:::",
        'cache-control': "no-cache",
        })

# returns versions from file   release and dev (test)
def getSavedVersion(): 
    with open(_PATH_LATEST_VERSION_FILENAME_, 'r') as f:
        versionRelease = int(f.readline())
        versionDev = int(f.readline())
    #print(versionRelease, versionDev)
    return int(versionRelease), int(versionDev)

def saveVersion(versionRelease, versionDev):
    with open(_PATH_LATEST_VERSION_FILENAME_, 'w') as f:
        f.write(str(versionRelease))
        f.write('\n')
        f.write(str(versionDev))

def downloadFile():
    # Creates the connection
    conn = http.client.HTTPSConnection(_KLEI_UPDATES_URL_, _KLEI_UPDATES_PORT_)
    conn.request("GET", _KLEI_UPDATES_PATH_)

    # Get response
    res =  conn.getresponse()

    # If everything is all right, then parse data, else returns the stuff 
    if res.status == 200: 
        data = res.read()
        conn.close()
        return data
    else:
        conn.close()
        raise Exception(str(datetime.datetime.now()) +" " + res.status +" "+ res.reason)

# returns latest version
# raises an exception if not found
def parseVersion(webpage):
    regex = r'\z<td><a href="/changelist/(\d+)/">';
    webpage = webpage.decode("utf-8")
    #print(webpage)
    # (?<=\\").*?(?=\\")
    matches = re.findall(r"\<h3 class='ipsType_sectionHead ipsType_break'\>([\s\d]+)(?=\<span)[^\>]*\>([^\<]*)", webpage)
    highest_dev = 0 # resulting 
    highest_release = 0
    for match in matches:
        current = int(re.sub(r"\s+", "", match[0]))
        if current > highest_dev and match[1] == "Test":
            highest_dev = current
        elif current > highest_release and match[1] == "Release":
            highest_release = current


    #print(highest_dev)
    return int(highest_release), int(highest_dev)



def fromFile():
    return getSavedVersion()
    
versionRelease = None
versionDev = None

""" Checks the version of the game """    
def checkVersion():
    global versionRelease, versionDev, EXIT_CODE
    data = downloadFile()
    versionRelease, versionDev = parseVersion(data)

    # Get version saved in path: `_PATH_LATEST_VERSION_FILENAME_`
    try:
        savedVersionRelease, savedVersionDev = getSavedVersion()
    except (FileNotFoundError, ValueError):
        return EXIT_CODE['TEXT_FILE_NOT_FOUND']

    # Compare versions, save changes
    if versionRelease != savedVersionRelease:
        return EXIT_CODE['NEW_RELEASE_VERSION']
    elif versionDev != savedVersionDev:
        return EXIT_CODE['NEW_TEST_VERSION']
    else:
        return EXIT_CODE['ALL_OK']

# returns date time without miliseconds
def datetimeWithoutMS(): 
    date = str(datetime.datetime.now())
    date, _ = date.split('.');
    return date

if __name__ == '__main__':    
    # Get result from the version
    try:
        result = checkVersion()
    except:
        traceback.print_exc() # Needs to log stdout and stderr
        result = EXIT_CODE['PARSE_ERROR']

    MSG = {
        EXIT_CODE['PARSE_ERROR'] : "Parse error",
        EXIT_CODE['FILE_NOT_UPDATED'] : f"Couldn't save into `{_PATH_LATEST_VERSION_FILENAME_}`! (Sorry for spam)",
        EXIT_CODE['DISCORD_UNAVAILABLE'] : "Couldn't send message through discord",
        EXIT_CODE['UNKNOWN_ERROR'] : "Unknown error",
        EXIT_CODE['ALL_OK'] : "No change",  
        EXIT_CODE['NEW_RELEASE_VERSION'] :  f"**Release update available**: {versionRelease}",
        EXIT_CODE['NEW_TEST_VERSION'] : f"Test version available: {versionDev}",
        EXIT_CODE['TEXT_FILE_NOT_FOUND'] : f"Creating textfile `{_PATH_LATEST_VERSION_FILENAME_}`.\nRelease version: {versionRelease}\nDev version: {versionDev}",
    }

    # Print it on discord if result is NEW_TEST_VERSION, NEW_RELEASE_VERSION, or TEXT_FILE_NOT_FOUND
    if result > EXIT_CODE['ALL_OK']: 
        # Print it on discord and save it inot file
        try:
            sendToDiscord(MSG[result])
            saveVersion(versionRelease, versionDev)
        except (FileNotFoundError, FileExistsError, IOError):
            # couldnt save into file
            result = EXIT_CODE['FILE_NOT_UPDATED']
            sendToDiscord(MSG[result])
        except:
            # couldnt connect on discord 
            result = EXIT_CODE['DISCORD_UNAVAILABLE']


    # Log everything into the stdout
    if result != EXIT_CODE['ALL_OK']:
        timestamp = datetimeWithoutMS();
        print(timestamp, MSG[result])
    exit(result)
