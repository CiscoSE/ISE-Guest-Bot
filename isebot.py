"""

Copyright (c) 2019 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
               
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.

"""

import requests
from datetime import datetime, date, timedelta
import base64
import json
from webexteamsbot import TeamsBot

##############
### Required Fields (Update with the appropriate info)
##############

BOT_APP_NAME = ""
BOT_EMAIL = ""
ACCESS_TOKEN = ""
BOT_ID = ""
BOT_URL = ""

ISE_USER = ""
ISE_PW = ""

ISE_URL = "https://IP-ADDR:PORT/ers"

portalID = ""

##############
### Bot setup
##############

auth = str.encode(':'.join((ISE_USER, ISE_PW)))
authkey = bytes.decode(base64.b64encode(auth))
headers = {'AUTHORIZATION': 'Basic ' + authkey, 'Content-Type': 'application/json', 'Accept': 'application/json'}

bot = TeamsBot(
    BOT_APP_NAME,
    teams_bot_token=ACCESS_TOKEN,
    teams_bot_url=BOT_URL,
    teams_bot_email=BOT_EMAIL,
)

def runbot():
    # Add bot commands
    bot.add_command("/listusers", "List all non-expired guest users", list_users)
    bot.add_command("/adduser", "Add a new guest user", add_user)
    bot.add_command("/deluser", "Delete a guest user", del_user)
    bot.add_command("/finduser", "Return information for a guest user", find_user)
    # Remove echo command
    bot.remove_command("/echo")
    # Set bot greeting (returned if no command is recognized)
    bot.set_greeting(botgreeting)
    # Run bot on local server
    bot.run(host="0.0.0.0", port=5000)

def botgreeting(incoming_arg):
    # If no message is found, provide default response 
    return "Hi there! If you need help, just type /help"

##############
### Bot Actions
##############

def add_user(incoming_arg):
    # Assemble URL
    USR_ADD = "/config/guestuser"
    url = ISE_URL + USR_ADD

    # Collect arguments passed to us
    userargs = []
    userargs = str(bot.extract_message("/adduser", incoming_arg.text)).split(",")
    # Check to make sure we have 3 arguments
    if len(userargs) < 3:
        return "Hmm. That doesn't look right. Please use the format: /adduser name, email, validDays"
    
    # Pull user's first/last name from command
    names = userargs[0].strip()
    if len(names.split(" ")) > 1:
        firstname = names.split(" ")[0]
        lastname = names.split(" ")[1]
        username = firstname[:1] + lastname
    else:
        firstname = names
        lastname = ""
        username = firstname + "01"

    # Get current time & generate expriration date 
    curtime = datetime.now()
    exptime = date.today() + timedelta(days=int(userargs[2].strip()))

    # Bundle data into JSON to send up to ISE
    userdata = {}
    userdata['GuestUser'] = {}
    userdata['GuestUser']['portalId'] = portalID
    userdata['GuestUser']['customFields'] = {}
    userdata['GuestUser']['guestType'] = 'Contractor (default)'
    userdata['GuestUser']['guestInfo'] = {}
    userdata['GuestUser']['guestInfo']['userName'] = username
    userdata['GuestUser']['guestInfo']['firstName'] = firstname
    userdata['GuestUser']['guestInfo']['lastName'] = lastname
    userdata['GuestUser']['guestInfo']['emailAddress'] = userargs[1].strip()
    userdata['GuestUser']['guestAccessInfo'] = {}
    userdata['GuestUser']['guestAccessInfo']['location'] = 'San Jose' 
    userdata['GuestUser']['guestAccessInfo']['validDays'] = (int(userargs[2].strip()) + 1)
    userdata['GuestUser']['guestAccessInfo']['toDate'] = exptime.strftime("%m/%d/%Y %H:%M")
    userdata['GuestUser']['guestAccessInfo']['fromDate'] = curtime.strftime("%m/%d/%Y %H:%M")
    json_data = json.dumps(userdata)

    # Send POST to ISE to create user
    response = requests.post(url, data = json_data, headers=headers, verify=False)

    # Check Response. If success, ISE will respond 201. If fail, ISE will provide JSON message with error
    print("Response code:" + str(response.status_code))
    print(response.text)
    if response.status_code == 201:
        userinfo = get_user_by_name(username)
        return "Created User! Please provide the following login credentials to your guest:" + userinfo
    else:
        actionresponse = json.loads(response.text)
        if actionresponse['ERSResponse']['messages'][0]['type'] == "ERROR":
            return "Uh oh. Something went wrong! Please use the format: /adduser name, email, validDays"


def del_user(incoming_arg):
    # Get email address from command
    emailaddr = bot.extract_message("/finduser", incoming_arg.text)

    if len(emailaddr) < 1:
        return "Hmm. That doesn't look right. Please use the format: /deluser emailAddress "

    # Parse JSON / Get total user count
    userList = get_all_users()
    userList = userList['SearchResult']['resources']

    # Run through user list to get attributes
    for user in userList:
        getbyid = "/config/guestuser/%s" % (user['id'])
        url = ISE_URL + getbyid

        response = requests.get(url, headers=headers, verify=False)
        # Check each user vs email addr provided
        guestuser = json.loads(response.text)
        if guestuser['GuestUser']['guestInfo']['emailAddress'] == emailaddr.strip():
            return delete_by_id(user['id'])

def find_user(incoming_arg):
    # Get email address from command
    emailaddr = bot.extract_message("/finduser", incoming_arg.text)

    if len(emailaddr) < 1:
        return "Hmm. That doesn't look right. Please use the format: /finduser emailAddress "

    # Parse JSON / Get total user count
    userList = get_all_users()
    userList = userList['SearchResult']['resources']

    # Run through user list to get attributes
    for user in userList:
        getbyid = "/config/guestuser/%s" % (user['id'])
        url = ISE_URL + getbyid

        response = requests.get(url, headers=headers, verify=False)
        # Check each user vs email addr provided
        guestuser = json.loads(response.text)
        if guestuser['GuestUser']['guestInfo']['emailAddress'] == emailaddr.strip():
            #Get user info
            guestuser = get_user_by_id(user['id'])
            # Grab what we need...
            guestPasswd = guestuser['GuestUser']['guestInfo']['password']
            guestusername = guestuser['GuestUser']['name']
            guestExpiration = guestuser['GuestUser']['guestAccessInfo']['toDate']
            userinfo = """
    """
            userinfo += "Username: %s, Password: %s, Expires on: %s" % (guestusername, guestPasswd, guestExpiration)
            return "Found user: " + userinfo
    return "No user found"

def list_users(incoming_arg):
    # Parse JSON / Get total user count
    userList = get_all_users()
    total = userList['SearchResult']['total']

    userList = userList['SearchResult']['resources']
    responseList = []
    botResponse = """ Found %s users.
    """ % total

    # Run through user list to get attributes
    for user in userList:
        guestuser = get_user_by_id(user['id'])
        # Pull guest info
        try: guestFirst = guestuser['GuestUser']['guestInfo']['firstName']
        except KeyError: guestFirst = ""
        try: guestLast = guestuser['GuestUser']['guestInfo']['lastName']
        except KeyError: guestLast = ""
        guestEmail = guestuser['GuestUser']['guestInfo']['emailAddress']
        guestPasswd = guestuser['GuestUser']['guestInfo']['password']
        guestusername = guestuser['GuestUser']['name']
        guestExpiration = guestuser['GuestUser']['guestAccessInfo']['toDate']
        # add to response
        botResponse = botResponse + "%s %s, Email: %s, Username: %s, Password: %s, Expires on: %s" % (guestFirst, guestLast, guestEmail, guestusername, guestPasswd, guestExpiration)
        botResponse += """
    """
    return(botResponse)

##############
### Supporting Functions
##############

def get_user_by_name(username):
    # Assemble URL
    GET_BY_NAME = "/config/guestuser/name/"
    url = ISE_URL + GET_BY_NAME + username
    response = requests.get(url, headers=headers, verify=False)

    guestuser = json.loads(response.text)
    userinfo = ""
    # Pull guest info
    try: guestFirst = guestuser['GuestUser']['guestInfo']['firstName']
    except KeyError: guestFirst = ""
    try: guestLast = guestuser['GuestUser']['guestInfo']['lastName']
    except KeyError: guestLast = ""
    guestEmail = guestuser['GuestUser']['guestInfo']['emailAddress']
    guestPasswd = guestuser['GuestUser']['guestInfo']['password']
    guestusername = guestuser['GuestUser']['name']
    guestExpiration = guestuser['GuestUser']['guestAccessInfo']['toDate']
    # add to response
    userinfo += """
    """
    userinfo = userinfo + "Username: %s, Password: %s, Expires on: %s" % (guestusername, guestPasswd, guestExpiration)
    return(userinfo)

def get_user_by_id(userid):
    getbyid = "/config/guestuser/%s" % (userid)
    url = ISE_URL + getbyid
    response = requests.get(url, headers=headers, verify=False)
    return json.loads(response.text)

def get_all_users():
    findurl = "/config/guestuser"
    url = ISE_URL + findurl
    response = requests.get(url, headers=headers, verify=False)
    return json.loads(response.text)

def delete_by_id(userid):
    url = ISE_URL + "/config/guestuser/%s" % (userid)
    response = requests.delete(url, headers=headers, verify=False)
    if response.status_code == 204:
        return "Guest user has been deleted."
    else:
        return "Unable to delete user."
    
def parse_user_info(guestuser):
    guest = {}
    # Pull guest info
    try: guest['FirstName'] = guestuser['GuestUser']['guestInfo']['firstName']
    except KeyError: guestFirst = ""
    try: guestLast = guestuser['GuestUser']['guestInfo']['lastName']
    except KeyError: guestLast = ""
    guestEmail = guestuser['GuestUser']['guestInfo']['emailAddress']
    guestPasswd = guestuser['GuestUser']['guestInfo']['password']
    guestusername = guestuser['GuestUser']['name']
    guestExpiration = guestuser['GuestUser']['guestAccessInfo']['toDate']
    # add to response



if __name__ == "__main__":
    runbot()