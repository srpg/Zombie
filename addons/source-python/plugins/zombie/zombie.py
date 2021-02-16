import os, random, path
# Core
from core import GAME_NAME, echo_console
# Sglite
from sqlite3 import dbapi2 as sqlite
# Delay
from listeners.tick import Delay
# Player/Userid
from players.entity import Player
from players.helpers import index_from_userid, userid_from_index
from filters.players import PlayerIter
# Entity
from entities.entity import Entity, BaseEntity
# Model
from engines.precache import Model
# Download
from stringtables.downloads import Downloadables
# Server Command
from engines.server import queue_command_string
# Events
from events.hooks import PreEvent, EventAction
from events import Event
# Messages
from messages import SayText2, HintText
from translations.strings import LangStrings
# Weapon
from filters.weapons import WeaponClassIter
from weapons.manager import weapon_manager
# Zombies
from zombie.command import command
from zombie.zprop import zprop

if GAME_NAME == 'csgo':
	default = '\x01'
	cyan = '\x0A'
else:
	default = '\x07FFB300'
	cyan = '\x0700CED1'
	
#======================
# Translated Messages
#======================
chat = LangStrings('zombie_chat')
Kill = SayText2(chat['Zprop_credits'])
Game = SayText2(chat['Game'])
Market = SayText2(chat['Market'])
Tp = SayText2(chat['Teleport'])
infect_message = SayText2(chat['Infect_first'])
weapon_remove = SayText2(chat['Weapon_remove'])
res = SayText2(chat['Respawn'])
restore = SayText2(chat['Weapon_restore'])
buy = SayText2(chat['Zprop_buy'])

#======================
# Config Add proper config?
#======================
Infitebullets = 1 # Activates infinite bullets, if player have clan_tag in config have,
Weapon_restore = 1 # Will clan member gain weapons back after getting removed
Boost = 10 # How much extra hp gain when have clan tag for killing
Speed = 1.10 # Current: 10% increase speed. How many percent increase speed for killing(only once increases)
KILL_HP = 0 # 1 Activates give full hp after killing zombie
WEAPON = 0 # 1 Activates give deagle and m4a1 for weapon give after first infect
FIRE = 0 # 1 Activates hegrenade hurt ignites enemies
HINT = 0 # 1 Tells hudhint hp
Clan = ['Test'] # Change it to your clan_tag you use for the extra features, currently it check Test clan_tag
weapon_secondary = ['deagle'] # Which weapon give for pistols, note requires WEAPON = 1
weapon_primary = ['m4a1'] # Which weapon give for primary, note requires WEAPON = 1

class SQLiteManager(object):
	players = []
    
	def __init__(self, path):
		self.path	= path 
		self.connection = sqlite.connect(path)
		self.connection.text_factory = str
		self.cursor	= self.connection.cursor()

		self.cursor.execute("PRAGMA journal_mode=OFF")
		self.cursor.execute("PRAGMA locking_mode=EXCLUSIVE")
		self.cursor.execute("PRAGMA synchronous=OFF")

		self.cursor.execute("""\
			CREATE TABLE IF NOT EXISTS Player (
			UserID	INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
			steamid VARCHAR(30) NOT NULL,
			credits		INTEGER DEFAULT 0,
			name	VARCHAR(30) DEFAULT 'default'
		)""")

		self.cursor.execute("CREATE INDEX IF NOT EXISTS PlayerIndex ON Player(SteamID);")

	def __del__(self):
		self.save()
		self.close()
        
	def __contains__(self, key):
		key = str(key)
		if key in self.items:
			return True
		self.execute("SELECT level FROM Player WHERE steamid=?", key)
		result = self.cursor.fetchone()
		if bool(result):
			self.players.append(key)
			return True

	def __iter__(self):
		self.execute("SELECT steamid FROM Player")
		for steamid in self.cursor.fetchall():
			yield steamid[0]

	def execute(self, parseString, *args):
		self.cursor.execute(parseString, args)

	def addPlayer(self, steamid, name):
		self.execute("INSERT INTO Player (steamid, name) VALUES (?,?)", steamid, name)
		return self.cursor.lastrowid
        

	def getUserIdFromSteamId(self, steamId):
		self.execute("SELECT UserID FROM Player WHERE steamid=?", steamId)
		value = self.cursor.fetchone()
		if value is None:
			return None
		return value[0]

	def getPlayerStat(self, userid, statType):
		if not isinstance(userid, int):
			userid = self.getUserIdFromSteamId(userid)
		statType = str(statType).replace("'", "''")
		if hasattr(statType, "__len__"):
			query = "SELECT " + ",".join( map( str, statType)) + " FROM Player WHERE UserID=?"
		else:
			query = "SELECT " + str( statType ) + " FROM Player WHERE UserID=?"
		self.execute(query, userid)
		return self.fetchone()
        
	def update(self, table, primaryKeyName, primaryKeyValue, options):
		keys = ""
		if not isinstance(options, dict):
			raise ValueError("Expected 'options' argument to be a dictionary, instead received: %s" % type(options).__name__)
		if options:
			for key, value in options.iteritems():
				if isinstance(key, str):
					key = key.replace("'", "''")
				if isinstance(value, str):
					value = value.replace("'", "''")
				keys += "%s='%s'," % (key, value)
			keys = keys[:-1]
			query = "UPDATE " + str(table) + " SET " + keys + " WHERE " + str(primaryKeyName) + "='" + str(primaryKeyValue) + "'"
			self.execute(query)

	def increment(self, table, primaryKeyName, primaryKeyValue, options):
		keys = ""
		if not isinstance(options, dict):
			raise ValueError("Expected 'options' argument to be a dictionary, instead received: %s" % type(options).__name__)
		for key, value in options.iteritems():
			if isinstance(key, str):
				key = key.replace("'", "''")
			if isinstance(value, str):
				value = value.replace("'", "''")
			keys += "%s=%s+%i," % (key, key, value)
		keys = keys[:-1]
		self.execute("UPDATE ? SET %s WHERE ?=?+?" % keys, table, primaryKeyName, primaryKeyName, primaryKeyValue)

	def fetchall(self):
		trueValues = []
		for value in self.cursor.fetchall():
			if isinstance(value, tuple):
				if len(value) > 1:
					tempValues = []
					for tempValue in value:
						if isinstance(tempValue, int):
							tempValue = int(tempValue)
						tempValues.append(tempValue)
					trueValues.append(tempValues)
				else:
					if isinstance(value[0], int):
						trueValues.append(int(value[0]))
					else:
						trueValues.append(value[0])
			else:
				if isinstance(value, int):
					value = int(value)
				trueValues.append(value)
		return trueValues

	def fetchone(self):
		result = self.cursor.fetchone()
		if hasattr(result, "__iter__"):
			if len(result) == 1:
				trueResults = result[0]
				if isinstance(trueResults, int):
					trueResults = int(trueResults)
				return trueResults
			else:
				trueResults = []
				for trueResult in result:
					if isinstance(trueResult, int):
						trueResult = int(trueResult)
					trueResults.append(trueResult)
				return trueResults
		if isinstance(result, int):
			result = int(result)
		return result    

	def save(self):
		self.connection.commit()

	def clear(self, saveDatabase = True):
		players.clearList()
		self.execute("DROP TABLE Player")
		if saveDatabase:
			self.save()
		self.__init__(self.path)
		for player in es.getUseridList():
			players.addPlayer(player)

	def close(self):
		self.cursor.close()
		self.connection.close()

class PlayerManager(object):
	def __init__(self):
		self.players = {}

	def __getitem__(self, userid):
		userid = int(userid)
		if self.__contains__(userid):
			return self.players[userid]
		return None

	def __delitem__(self, userid):
		self.removePlayer(userid)

	def __iter__(self):
		for player in self.players:
			yield self.players[player]

	def __contains__(self, userid):
		userid = int(userid)
		return bool(userid in self.players)

	def addPlayer(self, userid):
		self.players[int(userid)] = PlayerObject(userid)

	def removePlayer(self, userid):
		userid = int(userid)
		if self.__contains__(userid):
			del self.players[userid] # calls deconstructor on PlayerObject class

	def getPlayer(self, userid):
		return self.__getitem__(userid)

	def clearList(self):
		self.players.clear()

class PlayerObject(object):
	def __init__(self, userid):
		self.userid   = int(userid)
		self.steamid  = Player(index_from_userid(userid)).steamid
		self.name     = Player(index_from_userid(userid)).name
		self.isbot    = Player(index_from_userid(userid)).is_bot()
		self.currentAttributes = {}
		self.oldAttributes     = {}
		self.dbUserid = database.getUserIdFromSteamId(self.steamid)
		if self.dbUserid is None:
			self.dbUserid = database.addPlayer(self.steamid, self.name)
		self.update()
		self.playerAttributes = {}

	def __del__(self):
		self.commit()

	def __int__(self):
		return self.userid

	def __str__(self):
		return str(self.userid)

	def __getitem__(self, item):
		if item in self.currentAttributes:
			return self.currentAttributes[item]
		if item in self.playerAttributes:
			return self.playerAttributes[item]
		return None

	def __setitem__(self, item, value):
		if item in self.currentAttributes:
			self.currentAttributes[item] = value
		else:
			self.playerAttributes[item] = value

	def commit(self):
		for key, value in self.currentAttributes.items():
			if key in self.oldAttributes:
					database.execute("UPDATE Player SET %s=? WHERE UserID=?" % key, value, self.dbUserid)    
		self.oldAttributes = self.currentAttributes.copy()

	def update(self):
		database.execute("SELECT * FROM Player WHERE UserID=?", self.dbUserid)
		result = database.fetchone()
		UserID, steamid, credits, name = result

		for option in ('steamid', 'credits', 'name'):
			self.oldAttributes[option] = self.currentAttributes[option] = locals()[option]

#======================
# Other
#======================

weapons = [weapon.basename for weapon in WeaponClassIter(not_filters='knife')]

if GAME_NAME == 'cstrike':
	close = 0
	zombie_models = ['models/player/zh/zh_charple001.mdl','models/player/zh/zh_corpse002.mdl','models/player/zh/zh_zombie003.mdl','models/player/ics/hellknight_red/t_guerilla.mdl']
else:
	zombie_models = ['models/player/kuristaja/zombies/bman/bman.mdl', 'models/player/kuristaja/zombies/zpz/zpz.mdl', 'models/player/kuristaja/zombies/charple/charple.mdl']
	close = 9
	
def hudhint(userid, text):
	HintText(message=text).send(index_from_userid(userid))

def infopanel(attacker, userid):
	player = Player(index_from_userid(userid))
	return hudhint(attacker, 'Name: %s\nHealth: %s' % (player.name, player.health)) # Make later a code that can use delay every 2seconds, to prevent hudhint spams

#======================
# Download/Load
#======================

__FILEPATH__    = path.Path(__file__).dirname()
DATABASE_STORAGE_METHOD = SQLiteManager
database = None
databasePath = os.path.join(__FILEPATH__ + '/players.sqlite')
players = PlayerManager()
if GAME_NAME == 'cstrike':
	DOWNLOADLIST_PATH  = os.path.join(__FILEPATH__ + '/css.txt')
else:
	DOWNLOADLIST_PATH  = os.path.join(__FILEPATH__ + '/csgo.txt')

def load():
	global database
	database = DATABASE_STORAGE_METHOD(databasePath)
	database.execute('VACUUM')
	echo_console('[Zombie] Loaded')
	queue_command_string('bot_quota 20')
	queue_command_string('bot_quota_mode fill')
	queue_command_string('mp_roundtime 5')
	queue_command_string('bot_join_after_player 0')
	queue_command_string('bot_join_team any')
	queue_command_string('mp_limitteams 0')
	queue_command_string('mp_autoteambalance 0')
	queue_command_string('bot_chatter off') # Mute bots radio
	queue_command_string('mp_humanteam any')
	setDl()

def setDl():
	downloadables = Downloadables()
	with open(DOWNLOADLIST_PATH) as f:
		for line in f:
			line = line.strip()
			if not line:
				continue
			downloadables.add(line)

#========================
# Functions
#========================
def kill_credits(userid):
	if not players[userid]['credits'] >= 15:
		players[userid]['credits'] += 1
		cre = players[userid]['credits']
		Kill.send(index_from_userid(userid), green='\x04', default=default, cred=cre)
		
		
def player_list():
	pl = []
	for player in PlayerIter('alive'):
		pl.append(player.userid)
	return pl

def ct_count():
	return len(PlayerIter(['all', 'ct']))

def round_checker():
	if ct_count() == 0:
		Entity.find_or_create('info_map_parameters').fire_win_condition(3)

def burn(userid, duration):
	try:
		Entity(index_from_userid(userid)).call_input('IgniteLifetime', float(duration))
	except ValueError:
		pass

def teleport(userid):
	global location
	Player(index_from_userid(userid)).teleport(location)
	Tp.send(index_from_userid(userid), green='\x04', default=default)
    
def respawn(userid):
	player = Player(index_from_userid(userid))
	player.spawn(True)
	player.switch_team(3)
	player.unrestrict_weapons(*weapons)
	res.send(index_from_userid(userid), green='\x04', default=default)

#===================
# Events
#===================
@PreEvent('server_cvar', 'player_team', 'player_disconnect', 'player_connect_client')
def pre_events(game_event):
	return EventAction.STOP_BROADCAST

@Event('player_activate')
def player_activate(args):
	userid = args.get_int('userid')
	players.addPlayer(userid)
	
@Event('player_disconnect')
def player_disconnect(args):
	userid = args.get_int('userid')
	if userid in players:
		del players[userid]

@Event('round_end')
def round_end(args):
	queue_command_string('mp_humanteam any')
	for i in player_list():
		Player(index_from_userid(i)).switch_team(3) # Move all ct when round ends
		Player(index_from_userid(i)).unrestrict_weapons(*weapons) # Remove weapon restrict

@Event('round_start')
def round_start(ev):
	pl = []
	pl = player_list()
	if pl:
		userid = random.choice(pl)
		if userid:
			Player(index_from_userid(userid)).delay(15, infect_first, (userid,))
			#infect_first(userid)


@Event('player_spawn')
def player_spawn(event):
	player = Player.from_userid(event['userid'])
	player.gravity = 1
	player.set_noblock(True)
	player.cash = 12000
	player.unrestrict_weapons(*weapons)
	Game.send(player.index, green='\x04', default=default)
	Market.send(player.index, green='\x04', default=default)
	global location
	location = player.origin
	
@Event('player_hurt')
def player_hurt(args):
	if args.get_string('weapon') == 'knife':
		if args.get_int('dmg_health') >= 45:
			userid = args.get_int('userid')
			attacker = args.get_int('attacker')
			if attacker > 0:
				if not Player(index_from_userid(userid)).team == Player(index_from_userid(attacker)).team:
					if not Player(index_from_userid(userid)).team == 2:
						infect(userid)
						
@Event('player_hurt')
def player_hurt(args):
	userid = args.get_int('userid')
	attacker = args.get_int('attacker')
	if attacker > 0:
		if not Player(index_from_userid(userid)).team == Player(index_from_userid(attacker)).team:
			if args.get_string('weapon') == 'hegrenade' and FIRE:
				burn(userid, 10)
			else:
				if not Player(index_from_userid(attacker)).is_bot() and HINT:
					Delay(0.1, infopanel, (attacker, userid)) # Not sure will this work properly

@Event('player_death')
def player_death(args):
	userid = args.get_int('userid')
	attacker = args.get_int('attacker')
	user_player = Player(index_from_userid(userid))
	attacker_player = Player(index_from_userid(attacker))
	if attacker > 0:
		if not user_player.team == attacker_player.team:
			kill_credits(attacker)
			if KILL_HP:
				attacker_player.health = 100
			if attacker_player.clan_tag in Clan and KILL_HP:
				attacker_player.max_health += Boost
				attacker_player.health = attacker_player.max_health
				attacker_player.speed = Speed
            
@Event('player_death')
def player_death(args):
	userid = args.get_int('userid')
	Delay(0.1, respawn, (userid,))
	
@Event('weapon_fire_on_empty')
def weapon_fire_on_empty(args):
	userid = args.get_int('userid')
	weapon = args.get_string('weapon')
	player = Player(index_from_userid(userid))
	if player.primary:
		player.primary.remove()
	if Player(index_from_userid(userid)).primary:
		Player(index_from_userid(userid)).primary.remove()
	elif player.secondary:
		player.secondary.remove()
	if not player.is_bot():
		weapon_remove.send(player.index, weapons=weapon, default=default, cyan=cyan, green='\x04')
		if player.clan_tag in Clan and Weapon_restore:
 			player.give_named_item('weapon_%s' % (weapon))
 			Clan_Tag = player.clan_tag
 			restore.send(player.index, weapons=weapon, clan=Clan_Tag, default=default, cyan=cyan, green='\x04')

@Event('weapon_fire')
def weapon_fire(args):
	userid = args.get_int('userid')
	player = Player(index_from_userid(userid))
	if player.clan_tag in Clan and Infitebullets:
		weapon = player.active_weapon
		primary = player.primary
		secondary = player.secondary
		max_clip = weapon_manager[weapon.classname].clip
		if weapon == primary:
			weapon.clip = max_clip
		elif weapon == secondary:
			weapon.clip = max_clip
#===================
# Infect
#===================

def infect_first(userid):
	for player in PlayerIter('alive'):
		if player.userid != userid:
			player.switch_team(3)
			player.set_noblock(True)
			if WEAPON:
				player.give_named_item('weapon_%s' % (weapon_primary))
				if player.secondary:
					player.secondary.remove()
				player.give_named_item('weapon_%s' % (weapon_secondary))
			player.armor = 100
			player.set_property_bool('m_bHasHelmet', 1)
			queue_command_string('mp_humanteam ct')
		else:
			if GAME_NAME == 'cstrike':
				player.emit_sound(sample='ambient/creatures/town_child_scream1.wav',volume=1.0,attenuation=0.5)
			else:
				player.emit_sound(sample='sound/zombie/ze-infected3.mp3',volume=1.0,attenuation=0.5)
			player.switch_team(2)
			player.set_noblock(True)
			player.health = 10000
			player.speed = 1.5 # Should make 50% faster walk
			player.gravity = 0.75 # Should make 25% less have gravity
			if player.secondary:
				player.secondary.remove()
			elif player.primary:
				player.primary.remove()
			player.restrict_weapons(*weapons)
			global location
			player.teleport(location)
	infected_player = Player.from_userid(userid)
	random_model = random.choice(zombie_models)        
	infected_player.set_model(Model(random_model))
	infect_message.send(name=infected_player.name, default=default, green='\x04')
	Delay(0.1, round_checker)

def infect(userid):
	player = Player.from_userid(userid)
	player.switch_team(2)
	player.set_noblock(True)
	player.health = 10000
	player.speed = 1.5 # Should make 50% faster walk
	player.gravity = 0.75 # Should make 25% less have gravity
	if GAME_NAME == 'cstrike':
		player.emit_sound(sample='ambient/creatures/town_child_scream1.wav',volume=1.0,attenuation=0.5)
	else:
		player.emit_sound(sample='sound/zombie/ze-infected3.mp3',volume=1.0,attenuation=0.5)
	if player.secondary:
		player.secondary.remove()
	elif player.primary:
		player.primary.remove()
	player.restrict_weapons(*weapons)
	command.remove_idle_weapons()
	infected_player = Player.from_userid(userid)
	random_model = random.choice(zombie_models)        
	infected_player.set_model(Model(random_model))
	infect_message.send(name=infected_player.name, default=default, green='\x04')
	Delay(0.1, round_checker)
