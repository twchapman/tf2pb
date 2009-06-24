#!/usr/bin/python2.6

import irclib
import random
import re
import sqlite3
import string
import threading
import time

#irclib.DEBUG = 1

def add(userName, userCommand):
    global state
    global userList
    print "State : " + state
    if state != 'idle':
        if state == 'captain' or state == 'normal':
            # Debug.
            if len(userList) < 4:
                print "User add : " + userName + "  Command : " + userCommand
                userList[userName] = createUser(userName, userCommand)
            # Debug.
            if len(userList) == 4:
                initGame()
            printUserList()
            return 0
    else:
        server.privmsg(channel, "You can't \"!add\" until an admin has started a game.")
        return 0

def addFriend(userName, userCommand):
    global userList
    # 2 friends limit.
    commandList = string.split(userCommand, ' ')
    if len(commandList) > 1 and userName in userList:
        for i in range(1, len(commandList)):
            userList[userName]['friends'] = commandList[i]

def addGame(userName, userCommand):
    resetVariables()
    global allowFriends, gameServer, state

    # Game options.
    if re.search('nofriends', userCommand):
        print "Disable friends."
        allowFriends = 0

    # Game server.
    if re.search("[0-9a-z]*\.[0-9a-z]*:[0-9][0-9][0-9][0-9][0-9]*", userCommand):
        gameServer = re.findall("[0-9a-z]*\..*:[0-9][0-9][0-9][0-9][0-9]*", userCommand)[0]
    else:
        server.privmsg(userName, "You must set a server IP. Here is an example : \"!add 127.0.0.1:27015\".")
        return 0

    # Game type.
    if re.search('captain', userCommand):
        state = 'captain'
    else:
        state = 'normal'

    server.privmsg(channel, 'PUG started. Game type : ' + state + '. Type "!add" to join a game.')

def analyseCommand(connection, event):
    global lastCommand
    userName = extractUserName(event.source())
    if re.match('^!', event.arguments()[0]):
    # Check if the user is trying to pass a command to the bot.
        userCommand = event.arguments()[0]
        if isAdminCommand(userName, userCommand):
            if checkIfUserIsAdmin(event):
            #Execute the admin command.
                lastCommand = userCommand
                executeCommand(userName, userCommand)
                return 1
            else :
            # Exit and report an error.
                server.privmsg(channel, "Warning " + userName + ", you are trying an admin command as a normal user.")
                return 1
        else :
        #Execute the user command.
            if isUserCommand(userName, userCommand):
                lastCommand = userCommand
                executeCommand(userName, userCommand)
                return 1
    return 0

def assignCaptains():
        global teamA, teamB
        assignUserToTeam('medic', 0, 'a', userList[getAPlayer('medic')])
        assignUserToTeam('medic', 0, 'b', userList[getAPlayer('medic')])
        teamA[0]['status'] = 'captain'
        teamB[0]['status'] = 'captain'
        print teamA
        print teamB
        printCaptainChoices()

def assignUserToTeam(gameClass, recursiveFriend, team, user):
    global allowFriends, state, teamA, teamB, userList
    if gameClass:
        user['class'] = [gameClass]
    else:
        user['class'] = []
    if not team:
        if random.randint(0,1):
            team = 'a'
        else:
            team = 'b'
    # Assign the user to the team if the team's not full.
    if len(getTeam(team)) < 2: # Debug.
        getTeam(team).append(user)
    else:
        getTeam(getOppositeTeam(team)).append(user)
    if allowFriends and recursiveFriend:
    # Add friends if allowed to.
        counter = 0
        for friend in userList[user['nick']]['friends']:
            if isUser(friend) and not firstChoiceMedic(friend):
                assignUserToTeam('', 0, team, friend)
                counter += 1
            if counter >= getNumberOfFriendsPerClass(userList[user['nick']]['class']):
                break
    del userList[user['nick']]
    return 0

def buildTeams():
    global allowFriends, state, userList
    if state == 'normal':
        assignUserToTeam('medic', 1, 'a', userList[getAPlayer('medic')])
        assignUserToTeam('medic', 1, 'b', userList[getAPlayer('medic')])
        for i in range(2): #Debug.
            assignUserToTeam('', 1, 0, userList[getAPlayer('')])
        printTeams()
        print teamA
    state = 'idle'
    return 0

def checkIfUserIsAdmin(event):
    global userChannel
    user = extractUserName(event.source())
    whoisData = whois(user)
    if userChannel != '':
        if re.search('@' + channel + ' *', whoisData['channel']):
        # User is an admin.
            return 1
        else :
        # User is not an admin.
            return 0 #Debug.

def classCount(gameClass):
    global userList
    counter = 0
    for i, j in userList.iteritems():
        for userClass in userList[i]['class']:
            if userClass == gameClass:
                counter += 1
    return counter            

def createUser(userName, userCommand):
    global classList
    commandList = string.split(userCommand, ' ')
    user = {'command':'', 'class':[], 'friends':{}, 'nick':'', 'status':'', 'team':''}
    user['command'] = userCommand
    user['class'] = extractClasses(userCommand)
    user['nick'] = userName
    return user

def endGame():
    global initTimer, state
    initTimer.cancel()
    state = 'idle'
    print 'PUG stopped.'

def endofwhois(connection, event):
    whoisEnded = 1

def executeCommand(userName, userCommand):
    if re.search('!add$', userCommand) or re.search('!add ', userCommand):
        add(userName, userCommand)
        return 0
    if re.search('^!addfriends.*$', userCommand):
        addFriend(userName, userCommand)
        return 0
    if re.search('^!addgame.*$', userCommand):
        addGame(userName, userCommand)
        return 0
    if re.search('^!endgame.*$', userCommand):
        endGame()
        return 0
    if re.search('^!ip.*$', userCommand):
        ip()
        return 0
    if re.search('^!pick.*$', userCommand):
        pick(userName, userCommand)
        return 0
    if re.search('^!remove.*$', userCommand):
        remove(userName)
        return 0
    if re.search('^!vent.*$', userCommand):
        vent()
        return 0
    if re.search('^!vote.*$', userCommand):
        vote(userName, userCommand)
        return 0

def extractClasses(userCommand):
    global classList
    classes = []
    commandList = string.split(userCommand, ' ')
    for i in commandList:
        for j in classList:
            if i == j:
                classes.append(j)
    return classes

def extractUserName(user):
    return string.split(user, '!')[0]

def firstChoiceMedic(user):
    counter = 0
    for gameClass in userList[user]['class']:
        if gameClass == 'medic':
            break
        counter += 1
    if counter == 0:
        print "return 1"
        return 1
    print "return 0"
    return 0

def getAPlayer(gameClass):
    global userList
    for i in range(5):
        candidateList = []
        forcedList = []
        for user in userList:
            if len(userList[user]['class']) > i and gameClass == userList[user]['class'][i]:
                candidateList.append(user)
            else:
                forcedList.append(user)
        if len(candidateList) != 0:
            if len(candidateList) > 1:
                return candidateList[random.randint(0,len(candidateList) - 1)]
            else:
                return candidateList[0]
    if len(forcedList) > 1:
        return forcedList[random.randint(0,len(forcedList) - 1)]
    else:
        return forcedList[0]

def getNumberOfFriendsPerClass(gameClass):
    if gameClass == 'medic':
        return 2
    else:
        return 1

def getOppositeTeam(team):
    if team == 'a':
        return 'b'
    else:
        return 'a'

def getPlayerNumber(userName):
    global userList
    counter = 1
    for i in userList:
        if i == userName:
            return counter
        counter += 1

def getPlayerTeam(userName):
    for teamID in ['a', 'b']:
        team = getTeam(teamID)
        for user in team:
            if user['nick'] == userName:
                return teamID

def getRemainingClasses():
    global captainStage, captainStageList, formalTeam
    remainingClasses = formalTeam
    team = getTeam(captainStageList[captainStage])
    for user in team:
        if user['class'][0] in remainingClasses:
            remainingClasses.remove(user['class'][0])
    return remainingClasses

def getTeam(team):
    global teamA, teamB
    if team == 'a':
        return teamA
    else:
        return teamB

def ip():
    global gameServer
    if gameServer != '':
        message = "Match will be played on : " + gameServer
        server.privmsg(channel, message)

def isAuthorizedCaptain(userName):
    global captainStage, captainStageList, teamA, teamB
    team = getTeam(captainStageList[captainStage])
    for user in team:
        if user['status'] == 'captain' and user['nick'] == userName:
            return 1
    return 0

def isUser(userName):
    if userName in userList:
        return 1
    else:
        return 0
def initGame():
    global teamA, teamB
    global state, initTimer
    print "Init game."
    if state == "normal":
        # Debug.
        initTimer = threading.Timer(5, buildTeams)
        initTimer.start()
    elif state == "captain":
        # Debug.
        initTimer = threading.Timer(5, assignCaptains)
        initTimer.start()

def isAdminCommand(userName, userCommand):
    global adminCommands
    userCommand = string.split(userCommand, ' ')[0]
    for i in adminCommands:
        if re.search('^' + userCommand + '$', i):
            return 1
    return 0

def isUserCommand(userName, userCommand):
    global userCommands
    userCommand = string.split(userCommand, ' ')[0]
    for i in userCommands:
        if re.search('^' + userCommand + '$', i):
            return 1
    server.privmsg(userName, "Invalid command : " + userCommand)
    return 0

def nickChange(connection, event):
    global userList
    oldUserName = extractUserName(event.source())
    newUserName = event.target()
    if oldUserName in userList:
        userList[newUserName] = userList[oldUserName]
        del userList[oldUserName]

def pick(userName, userCommand):
    global captainStage, classList, state, teamA, teamB, userList
    if not len(teamA) or not len(teamB):
        print 'not yet started : picl'
        return 0
    commandList = string.split(userCommand, ' ')
    if len(commandList) == 1:
        print 'not enough args:pick'
        return 0
    del commandList[0]
    gameClass = ''
    counter = 0
    for command in commandList:
        if command in classList:
            gameClass = command
            del commandList[counter]
        counter += 1
    # Check if this nickname exists in the player list.
    userFound = 0
    for user in userList:
        if userList[user]['nick'] == commandList[0]:
            userFound = 1
            break
    if not userFound:
        print 'error, this user doesn\'t exists :picl'
        return 0
    # Check if the captain specified a class.
    if gameClass == '':
        print 'error, you must specify a class'
        return 0
    if isAuthorizedCaptain(userName):
        assignUserToTeam(gameClass, 0, getPlayerTeam(userName), userList[commandList[0]])
        # Debug.
        if captainStage < 1:
            captainStage += 1
            printCaptainChoices()
        else:
            state = 'idle'
            printTeams()
            print 'send message to all users'
    else:
        print 'you are not authorized to pick a player'

def privmsg(connection, event):
    if not analyseCommand(connection, event):
        server.privmsg(extractUserName(event.source()), "Type \"!help\" for usage commands. Otherwise, don't ask me anything that I can't answer, I'm just a PUG bot.")

def pubmsg(connection, event):
    analyseCommand(connection, event)

def printCaptainChoices():
    print getRemainingClasses()
    global classList, captainStage, captainStageList, userList
    captainName = getTeam(captainStageList[captainStage])[0]['nick']
    for gameClass in classList:
        choiceList = []
        for userName in userList:
            if gameClass in userList[userName]['class']:
                choiceList.append("(" + str(getPlayerNumber(userName)) + ")" + userName)
        if len(choiceList):
            server.send_raw("NOTICE " + captainName + " : " + gameClass.capitalize() + "s: " + ', '.join(choiceList)) 
    choiceList = []
    for userName in userList:
        choiceList.append("(" + str(getPlayerNumber(userName)) + ")" + userName)
    server.send_raw("NOTICE " + captainName + " : All: " + ', '.join(choiceList)) 

def printTeams():
    global teamA, teamB
    teamNames = ['Team A', 'Team B']
    teams = [teamA, teamB]
    counter = 0
    for i in teams:
        message = teamNames[counter] + " : "
        for user in teams[counter]:
            gameClass = ''
            if user['class']:
                gameClass = " as \x0314" + user['class'][0] + "\x03"
            message += '"' + user['nick'] + gameClass + '" '
        server.privmsg(channel, message)
        counter += 1

def printUserList():
    global lastUserPrint, printTimer, userList
    if (time.time() - lastUserPrint) > 5:
        lastUserPrint = time.time()
        # Debug.
        message = str(len(userList)) + "/4 users subscribed : "
        for i, user in userList.iteritems():
            message += '"' + user['nick']
            if 'medic' in user['class']:
                message += " as \x0314medic\x03"
            message += '"  '
        server.privmsg(channel, message)
    else:
        if type(printTimer) is not int:
            printTimer.cancel()
        printTimer = threading.Timer(5, printUserList)
        printTimer.start()

def remove(userName):
    global userList
    if(isUser(userName)):
        del userList[userName]
        initTimer.cancel()
    printUserList()

def resetUserVariables():
    global userAuth, userInfo, userName
    userAuth = []
    userChannel = []
    userInfo = []

def resetVariables():
    global allowFriends, captainStage, gameServer, teamA, teamB, userList
    allowFriends = 1
    captainStage = 0
    gameServer = ''
    teamA = []
    teamB = []
    userList = {}
    print 'Reset variables.'

def saveVote(votedWhoisData, voterWhoisData, vote):
    global connection, cursor
    votedAuth = ''
    votedIP = votedWhoisData['info'][2]
    voterIP = voterWhoisData['info'][2]
    if len(votedWhoisData['auth']):
        votedAuth = votedWhoisData['auth'][1]
        queryData = votedAuth, voterIP
        cursor.execute('SELECT * FROM votes WHERE votedAuth = ? AND voterIP = ?', queryData)
        if cursor.fetchone():
            queryData = vote, votedAuth, voterIP
            cursor.execute('UPDATE votes SET vote = ? WHERE votedAuth = ? AND voterIP = ?', queryData)
        else:
            queryData = votedIP, votedAuth, voterIP, vote
            cursor.execute('INSERT INTO votes VALUES (?, ?, ?, ?)', queryData)
    else:
        queryData = votedIP, voterIP
        cursor.execute('SELECT * FROM votes WHERE votedIP = ? AND voterIP = ?', queryData)
        if cursor.fetchone():
            queryData = vote, votedIP, voterIP
            cursor.execute('UPDATE votes SET vote = ? WHERE votedIP = ? AND voterIP = ?', queryData)
        else:
            queryData = votedIP, '', voterIP, vote
            cursor.execute('INSERT INTO votes VALUES (?, ?, ?, ?)', queryData)
    connection.commit()

def vent():
    global voiceServer
    message = "Ventrilo IP : " + voiceServer['ip'] + ":" + voiceServer['port'] + "  Password : " + password
    server.privmsg(channel, message)

def vote(userName, userCommand):
    global userInfo, whoisEnded
    #Validation of the user vote.
    commandList = string.split(userCommand, ' ')
    if len(commandList) == 3:
        if(re.search('[0-9][0-9]*', commandList[2]) and (int(commandList[2]) >= 0 and int(commandList[2]) <= 10)):
            vote = commandList[2]
            votedWhoisData = whois(commandList[1])
        else:
            server.privmsg(userName, "Error, the second argument of your \"!vote\" command must be a number of 0 to 10.")
            return 0
    else:
        server.privmsg(userName, "Your vote can't be registered, you don't have the right number of arguments in yout command. Here is an example of a correct vote command: \"!vote nickname 10\".")
        return 0
    if len(votedWhoisData['info']) > 0:
        voterWhoisData = whois(userName)
        saveVote(votedWhoisData, voterWhoisData, vote)
        server.privmsg(channel, userName + " rated " + commandList[1] + " " + vote + "/10" + ".")
    else:
        server.privmsg(channel, userName + ", the user you voted for does not exist.")
        return 0

def welcome(connection, event):
    server.join ( channel )

def whois(userName):
    resetUserVariables()
    global userAuth, userChannel, userInfo, whoisEnded
    counter = 0
    whoisEnded = 0
    server.whois([userName])
    while not whoisEnded and counter < 10:
        irc.process_once(0.2)
        counter += 1
    return {'auth':userAuth, 'channel':userChannel, 'info':userInfo}

def whoisauth(connection, event):
    for i in event.arguments():
        userAuth.append(i)

def whoischannels(connection, event):
    global userChannel
    if re.search('#', event.arguments()[1]):
        userChannel = event.arguments()[1]
        return 0

def whoisuser(connection, event):
    global userInfo
    for i in event.arguments():
        userInfo.append(i)

# Connection information
#network = 'irc.gamesurge.net'
network = '127.0.0.1'
port = 6667
channel = '#tf2.pug.na'
nick = 'PUG-BOT'
name = 'BOT'

adminCommands = ["!addgame", "!endgame"]
allowFriends = 1
captainStage = 0
captainStageList = ['a', 'b', 'a', 'b', 'a', 'b', 'a', 'b', 'a', 'b'] 
classList = ['demo', 'medic', 'scout', 'soldier']
formalTeam = ['demo', 'medic', 'scout', 'scout', 'soldier', 'soldier']
gameServer = ''
lastCommand = ""
lastUserPrint = time.time()
password = 'tf2gather'
state = 'idle'
teamA = []
teamB = []
printTimer = 0
initTimer = 0
userCommands = ["!add", "!addfriend", "!addfriends", "!ip", "!pick", "!remove", "!vent", "!vote"]
userAuth = []
userChannel = []
userInfo = []
userList = {}
voiceServer = {'ip':'vent20.gameservers.com', 'port':'4273'}
whoisEnded = 0

#CREATE TABLE votes (votedIP varchar(255), votedAuth varchar(255), voterIP varchar(255), vote int)
connection = sqlite3.connect('./tf2pb.sqlite')
cursor = connection.cursor()

# Create an IRC object
irc = irclib.IRC()

# Create a server object, connect and join the channel
server = irc.server()
server.connect ( network, port, nick, ircname = name )

#irc.add_global_handler("all_events", all, -10)
irc.add_global_handler('endofwhois', endofwhois)
irc.add_global_handler('nick', nickChange)
irc.add_global_handler('privmsg', privmsg)
irc.add_global_handler('pubmsg', pubmsg)
irc.add_global_handler('welcome', welcome)
irc.add_global_handler('whoisauth', whoisauth)
irc.add_global_handler('whoischannels',whoischannels)
irc.add_global_handler('whoisuser',whoisuser)

# Jump into an infinite loop
irc.process_forever()
