import os, random, path
# Core
from core import GAME_NAME, echo_console
# Delay
from listeners.tick import Delay
# Player/Userid
from players.entity import Player
from players.helpers import index_from_userid, userid_from_index
from filters.players import PlayerIter
# Entity
from entities.entity import Entity
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
INFECT_HEALTH = 10000 # How much hp get infected players
Infitebullets = 1 # Activates infinite bullets, if player have clan_tag in config have
WEAPON_REMOVE = 1 # Removes weapons which doesn't have bullets, 1 = On| 0 = Off
Weapon_restore = 1 # Will clan member gain weapons back after getting removed
Boost = 10 # How much extra hp gain when have clan tag for killing
Speed = 1.10 # Current: 10% increase speed. How many percent increase speed for killing(only once increases)
KILL_HP = 1 # 1 Activates give full hp after killing zombie
WEAPON = 1 # 1 Activates give deagle and m4a1 for weapon give after first infect
FIRE = 1 # 1 Activates hegrenade hurt ignites enemies
HINT = 1 # 1 Tells hudhint hp
Clan = '[Best RPG]' # Change it to your clan_tag you use for the extra features, currently it check [Best RPG] clan_tag
weapon_secondary = 'deagle' # Which weapon give for pistols, note requires WEAPON = 1
weapon_primary = 'm4a1' # Which weapon give for primary, note requires WEAPON = 1

class ZombiePlayer(Player):
	caching = True 

	def __init__(self, index):
		super().__init__(index)
		self.have_credits  	= 0
		self.player_target 	= False
		self.secondary_pistol 	= False
		self.primary_primary 	= False

	def infect(self, type=None):
		self.switch_team(2)
		self.set_noblock(True)
		self.health = INFECT_HEALTH
		self.speed = 1.5
		self.gravity = 0.75
		if GAME_NAME == 'csgo':
			self.emit_sound(sample='sound/zombie/ze-infected3.mp3',volume=1.0,attenuation=0.5)
		else:
			self.emit_sound(sample='ambient/creatures/town_child_scream1.wav',volume=1.0,attenuation=0.5)
		for weapon in self.weapons():
			if weapon.classname != 'weapon_knife':
				weapon.remove()
		self.restrict_weapons(*weapons)
		random_model = random.choice(zombie_models)        
		self.set_model(Model(random_model))
		infect_message.send(name=self.name, default=default, green='\x04')
		Delay(0.1, round_checker)
		if not type is None:
			global location
			self.origin = location

	def uninfect(self):
		self.unrestrict_weapons(*weapons)
		self.switch_team(3)
		self.spawn()
		res.send(self.index, green='\x04', default=default)

	def give_weapons_back(self, weapon):
		if self.is_bot():
			return
		if not self.have_clan_benefit():
			return
		if WEAPON_REMOVE == 0:
			return
		for weapons in self.weapons():
			if weapons.classname.replace('weapon_', '', 1) == weapon:
				weapons.remove()
				weapon_remove.send(self.index, weapons=weapon, default=default, cyan=cyan, green='\x04')
				if Weapon_restore == 0:
					return
				self.give_named_item(f'weapon_{weapon}')
			restore.send(self.index, weapons=weapon, clan=self.clan_tag, default=default, cyan=cyan, green='\x04')

	def give_weapons_ct(self):
		if not self.team == 3:
			return
		self.armor = 100
		self.has_helmet = True
		self.set_noblock(True)
		queue_command_string('mp_humanteam ct')
		if WEAPON == 0:
			return
		for weapon in self.weapons():
			if weapon.classname != 'weapon_knife':
				weapon.remove()
		self.give_named_item(f'weapon_{weapon_primary}')
		self.give_named_item(f'weapon_{weapon_secondary}')

	def give_kill_bonus(self):
		if not self.have_credits >= 15:
			self.have_credits += 1
			Kill.send(self.index, green='\x04', default=default, cred=self.have_credits)
		if KILL_HP == 1:
			self.health = 100
		if self.have_clan_benefit():
			self.max_health += Boost
			self.health = self.max_health
			self.speed = Speed

	def infinite_clip(self):
		if self.is_bot():
			return
		if self.have_clan_benefit():
			if Infitebullets:
				weapon = self.get_active_weapon()
				if weapon is None:
					return
				try:
					weapon.clip += 1
				except ValueError:
					return

	def have_clan_benefit(self):
		if Clan == self.clan_tag:
			return True
#======================
# Other
#======================
weapons = [weapon.basename for weapon in WeaponClassIter(not_filters='knife')]

if GAME_NAME == 'csgo':
	zombie_models = ['models/player/kuristaja/zombies/bman/bman.mdl', 'models/player/kuristaja/zombies/zpz/zpz.mdl', 'models/player/kuristaja/zombies/charple/charple.mdl']
	close = 9
else:
	close = 0
	zombie_models = ['models/player/zh/zh_charple001.mdl','models/player/zh/zh_corpse002.mdl','models/player/zh/zh_zombie003.mdl','models/player/ics/hellknight_red/t_guerilla.mdl']
	
def hudhint(userid, text):
	HintText(message=text).send(index_from_userid(userid))

def infopanel(attacker):
	player = ZombiePlayer.from_userid(attacker)
	if not player.player_target == False:
		try:
			target = Player.from_userid(player.player_target)
			if not target.dead and target.health > 0:
				__msg__ = '%s: %s' % (target.name, target.health)
				hudhint(attacker, __msg__)
			else:
				player.player_target = False
		except:
			player.player_target = False

#======================
# Download/Load
#======================

__FILEPATH__    = path.Path(__file__).dirname()

if GAME_NAME == 'csgo':
	DOWNLOADLIST_PATH  = os.path.join(__FILEPATH__ + '/csgo.txt')
else:
	DOWNLOADLIST_PATH  = os.path.join(__FILEPATH__ + '/css.txt')

def load():
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

#===================
# Events
#===================
@PreEvent('server_cvar', 'player_team', 'player_disconnect', 'player_connect_client')
def pre_events(game_event):
	return EventAction.STOP_BROADCAST

@Event('round_end')
def round_end(args):
	queue_command_string('mp_humanteam any')
	for i in player_list():
		player = Player.from_userid(i)
		player.switch_team(3) # Move all ct when round ends
		player.unrestrict_weapons(*weapons) # Remove weapon restrict

@Event('round_start')
def round_start(ev):
	pl = []
	pl = player_list()
	if pl:
		userid = random.choice(pl)
		if userid:
			player = ZombiePlayer(index_from_userid(userid))
			player.delay(15, player.infect, ('first',))
			for i in player_list():
				ct = ZombiePlayer.from_userid(i)
				ct.delay(16, self.give_weapons_ct)

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
	userid = args.get_int('userid')
	attacker = args.get_int('attacker')
	if attacker > 0:
		victim = ZombiePlayer.from_userid(userid)
		hurter = ZombiePlayer.from_userid(attacker)
		if not victim.team == hurter.team:
			if args.get_string('weapon') == 'hegrenade' and FIRE:
				burn(userid, 10)
			elif args.get_string('weapon') == 'knife' and args.get_int('dmg_health') >= 45:
				if not victim.team == 2:
					victim.infect()
			else:
				if not hurter.is_bot() and HINT:
					hurter.player_target = userid
					hurter.delay(0.1, infopanel, (attacker,))

@Event('player_death')
def player_death(args):
	userid = args.get_int('userid')
	attacker = args.get_int('attacker')
	if attacker > 0:
		user_player = Player(index_from_userid(userid))
		attacker_player = ZombiePlayer(index_from_userid(attacker))
		if not user_player.team == attacker_player.team:
			attacker_player.give_kill_bonus()
	ZombiePlayer.from_userid(userid).uninfect()

@PreEvent('weapon_fire_on_empty')
def pre_weapon_fire_on_empty(args):
	userid = args.get_int('userid')
	ZombiePlayer.from_userid(userid).give_weapons_back(args.get_string('weapon'))

@Event('weapon_fire')
def weapon_fire(args):
	userid = args.get_int('userid')
	ZombiePlayer.from_userid(userid).infinite_clip()
