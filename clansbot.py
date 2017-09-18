import urllib, requests, json
import tokens

# the telegram request should be passed to https://api.telegram.org/bot<token>/METHOD_NAME

startReplyText = "Hello! I am ClansBot. I know everything about clans of Clash of Clans. Ask me for /help to see the list of everything I can do."
tagReplyText = "Give me a tag of a clan and I will tell you everything there is to know about it."
nameReplyText = "Give me a name of a clan so I can tell you about it."
membersReplyText = "Give me a clan tag and I will print you it's members"
warLogReplyText = "I will fetch clan's war log if you give me it's tag"
currentWarReplyText = "I will search for the clan's current war information. Give me the tag now."

commandList = {'tag': 'search clan by clan tag', 
				'name': 'search clan by clan name',
				'members': 'serach by tag print members',
				'clanwarlog': 'search by tag print war log',
				'clancurrentwar': 'search by tag print current war'
				}

answers = {
	#'chat_id': 'answer_type',
	#'201222234': 'tag',
	#'201222234': 'member',
	#etc...
}

def getChatId(message):
	return message['from']['id']

def askFor(message, answerType):
	chatId = getChatId(message)
	answers[chatId] = answerType

def isAnswer(message):
	chatId = getChatId(message)
	return answers.has_key(chatId)

def answerType(message):
	chatId = getChatId(message)
	return answers[chatId]

def removeQuestion(message):
	chatId = getChatId(message)
	del answers[chatId]

def sendMessage(message, replyText, keyboard = None):
	chatId = str(getChatId(message))
	replyText = urllib.quote(replyText.encode('utf-8'))

	url = 'https://api.telegram.org/bot' + tokens.clansBotToken + '/sendMessage?chat_id=' + chatId + '&parse_mode=HTML&text=' + replyText

	if keyboard:
		keyboard = json.dumps(keyboard)
		url = url + '&reply_markup=' + keyboard

	m = requests.get(url) # response [200]
	# print m.text

def getAllUpdates(offset):
	req_url = 'https://api.telegram.org/bot' + tokens.clansBotToken + '/getUpdates'
	if offset:
		req_url = req_url + '?offset=' + str(offset)
	print req_url

	r = requests.get(req_url) #r response [200]
	data = json.loads(r.text)

	if data['result']:
		# data items list iterate
		for item in data['result']:
			if item.has_key('message'):
				message = item['message']
			elif item.has_key('edited_message'):
				message = item['edited_message']

			print u'{0} - {1}: {2}'.format(message['from']['id'], message['from']['username'], message['text'])
			replyToMessage(message)
			updateId = item['update_id']

	print updateId

	return updateId

def replyToMessage(message):

	if not isAnswer(message):
		username = u'{0} {1}'.format(message['from']['first_name'], message['from']['last_name'])
		messageText = message['text']
		if message.has_key('entities') and message['entities'][0]['type']=='bot_command':
			if messageText.lower() == '/help':
				reply_text = helpCommand()
				action = 'help'
			elif messageText.lower() == '/start':
				reply_text = startCommand()
			elif messageText.lower() == '/tag':
				reply_text = tagReplyText
				action = 'tag'
			elif messageText.lower() == '/name':
				reply_text = nameReplyText
				action = 'name'
			elif messageText.lower() == '/members':
				reply_text = membersReplyText
				action = 'members'
			elif messageText.lower() == '/clanwarlog':
				reply_text = warLogReplyText
				action = 'warlog'
			elif messageText.lower() == '/clancurrentwar':
				reply_text = currentWarReplyText
				action = 'currentWar'
			else:
				print username + '----THIS IS NOT A COMMAND----------->' + ' : ' + messageText

			if reply_text:
				sendMessage(message, reply_text)
				
			if action:
				askFor(message, action)
		else:
			print 'ignored'
	else: #process anwer to latest askFor by answerType
		answerReceivedFor = answerType(message)
		if answerReceivedFor == 'tag': 
			tagCommand(message)
		elif answerReceivedFor == 'name':
			nameCommand(message)
		elif answerReceivedFor == 'help':
			helpCommand()
		elif answerReceivedFor == 'members':
			membersCommand(message)
		elif answerReceivedFor == 'warlog':
			clanWarLogCommand(message)
		elif answerReceivedFor == 'currentWar':
			currentWarCommand(message)

		removeQuestion(message)

def startCommand():
	return startReplyText

def helpCommand():
	helpReplyText = "I can do the following for you: \n"
	#generating help message:
	for key in commandList:
		helpReplyText += "/" + key + ": "
		helpReplyText += commandList[key] + "\n"
	return helpReplyText	

# command function communicates messages with data to user
def tagCommand(message):
	if message['text'].startswith('#'):
		tag = message['text'][0:]

		# data from fetch function
		data = fetchByTag(tag)
		# print data
		tag = data['tag']
		name = data['name']
		clanType = data['type']
		description = data['description']
		reply = u'<em>Tag:</em> <b>{0}</b>\n<em>Name:</em> <b>{1}</b>\n<em>Type:</em> <b>{2}</b>\n<em>Description:</em> <b>{3}</b>'.format(tag, 
			name, clanType, description)
	
	else:
		askFor(message, 'tag')
		reply = "Tags start with #"

	sendMessage(message, reply)

# fetch function returns data json
def fetchByTag(tag):
	url = 'https://api.clashofclans.com/v1/clans/' + urllib.quote(tag)
	r = requests.get(url, headers=tokens.keyHeader) #200!
	data = json.loads(r.text)
	return data

# command function communicates messages with data to user
def nameCommand(message):
	name = message['text']
	data = fetchByName(name)
	clans = data['items']
	clanList = []

	for i in range(len(clans)):
		clanInfoText = u'<b>{0}</b> <em>Tag:</em> <b>{1}</b>\n<em>Name:</em> <b>{2}</b>\n<em>Type:</em> <b>{3}</b>\n<em>Level:</em> <b>{4}</b>'.format(i + 1, 
			clans[i]['tag'], clans[i]['name'], clans[i]['type'], clans[i]['clanLevel'])
		clanList.append(clanInfoText)

	reply =  "Here are some clans with the name " + name + ": \n\n" + "\n\n".join(clanList)
	sendMessage(message, reply)

# fetch function returns data json
def fetchByName(name):
	url = 'https://api.clashofclans.com/v1/clans?name=' + urllib.quote(name.encode('utf-8')) + '&limit=10'
	r = requests.get(url, headers=tokens.keyHeader) #200!
	data = json.loads(r.text)
	return data

# command function communicates messages with data to user
def membersCommand(message):
	if message['text'].startswith('#'):
		tag = message['text'][0:]
		# data from fetch function
		memberList = []
		data = fetchClanMembers(tag)
		members = data['items']

		for i in range(len(members)):
			# print members[i]['name']
			memberInfoText = u'<em>{0} Name:</em> <b>{1}</b>\n<em>Expert Level:</em> <b>{2}</b>\n<em>Clan rank:</em> <b>{3}</b>\n<em>Trophies:</em> *<b>{4}</b>\n'.format(i+1, 
				members[i]['name'], members[i]['expLevel'], 
				members[i]['clanRank'], members[i]['trophies'])
			memberList.append(memberInfoText)

		reply =  "Here are the members of this clan: \n\n" + "\n\n".join(memberList)

	else:
		askFor(message, 'members')
		reply = "Clan tags start with #"

	sendMessage(message, reply)

# fetch function returns data json
def fetchClanMembers(tag):
	url = 'https://api.clashofclans.com/v1/clans/' + urllib.quote(tag) + '/members'
	r = requests.get(url, headers=tokens.keyHeader) #200!
	data = json.loads(r.text)
	return data

# command function communicates messages with data to user
def clanWarLogCommand(message):
	if message['text'].startswith('#'):
		tag = message['text'][0:]
		# data from fetch function
		data = fetchClanWarLog(tag)
		warLogList = []

		if data == "no":
			print "no data"
			reply =  "Sry, no data available"
		else:
			for item in data['items']:
				warInfoText = u"<em>Team size:</em> <b>{0}</b>\n<em>Opponent:</em> <b>{1}</b>\n<em>Attacks:</em> <b>{2}</b>\n<em>Result:</em> <b>{3}</b>\n\n".format(item['teamSize'],
					item['opponent']['name'], item['clan']['attacks'], item['result'])
				warLogList.append(warInfoText)
				print warInfoText
			reply = "\n".join(warLogList)

	else:
		askFor(message, 'members')
		reply = "Clan tags start with #"

	sendMessage(message, reply)

# fetch function returns data json
def fetchClanWarLog(tag):
	url = 'https://api.clashofclans.com/v1/clans/' + urllib.quote(tag) + '/warlog?limit=5'
	r = requests.get(url, headers=tokens.keyHeader)
	# the clan might not share warlog data
	if r.status_code == 200:
		data = r.json()
		return data
	else:
		return "no"

def currentWarCommand(message):
	if message['text'].startswith('#'):
		tag = message['text'][0:]
		# data from fetch function
		data = fetchCurrentWar(tag)

		if data == "no":
			print "no data available"
			reply =  "Sry, no data available"
		else:
			clan = data['clan']
			opponent = data['opponent']
			if data['state'] == 'notInWar':
				reply = 'This clan is not in any wars at the moment'
			else:
				warInfoText = u"<em>Attacks:</em> <b>{0}</b>\n<em>Destruction persentage:</em> <b>{1}</b>\n<em>Stars:</em> <b>{2}</b>\n<em>Clan level:</em> *<b>{3}</b>\n<em>State:</em> <b>{4}</b>\n<em>Opponent:</em> <b>{5}</b>\n<em>Destruction persentage:<em/> <b>{6}</b>\n<em>Stars:</em> <b>{7}</b>\n<em>Level:</em> <b>{8}</b>\n".format(clan['attacks'], 
					clan['destructionPercentage'], clan['stars'], clan['clanLevel'], data['state'],
					opponent['attacks'], opponent['destructionPercentage'], opponent['stars'], opponent['clanLevel'])
				reply = warInfoText

	else:
		askFor(message, 'members')
		reply = "Clan tags start with #"

	sendMessage(message, reply)

def fetchCurrentWar(tag):
	url = 'https://api.clashofclans.com/v1/clans/' + urllib.quote(tag) + '/currentwar'
	r = requests.get(url, headers=tokens.keyHeader)
	# the clan might not share current war data
	if r.status_code == 200:
		data = r.json()
		return data
	else:
		return "no"

#save last update id to file
def offsetSaveToFile(lastUpdateId):
	foffset = open('botoffset.txt', 'w')
	foffset.write(str(lastUpdateId))
	# print "Offset saved: {0}".format(lastUpdateId)
	foffset.close()

#read last update id from file
def offsetReadFromFile():
	foffset = open('botoffset.txt', 'r')
	offset = foffset.read()
	# print "Offset read: {0}".format(offset)
	return offset

offset = int(offsetReadFromFile())

lastUpdateId = getAllUpdates(offset)

offsetSaveToFile(lastUpdateId)


