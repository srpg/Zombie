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
Infitebullets = 1 # Activates infinite bullets, if player have clan_tag in config have
WEAPON_REMOVE = 1 # Removes weapons which doesn't have bullets, 1 = On| 0 = Off
Weapon_restore = 1 # Will clan member gain weapons back after getting removed
Boost = 10 # How much extra hp gain when have clan tag for killing
Speed = 1.10 # Current: 10% increase speed. How many percent increase speed for killing(only once increases)
KILL_HP = 0 # 1 Activates give full hp after killing zombie
WEAPON = 1 # 1 Activates give deagle and m4a1 for weapon give after first infect
FIRE = 1 # 1 Activates hegrenade hurt ignites enemies
HINT = 1 # 1 Tells hudhint hp
Clan = ['[Best RPG]'] # Change it to your clan_tag you use for the extra features, currently it check Test clan_tag
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
		target = Player.from_userid(player.player_target)
		if not target.dead and target.health > 0:
			hudhint(attacker ,__msg__ = '%s: %s' % (target.name, target.health))
		else:
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
	player = ZombiePlayer.from_userid(userid)
	if not player.have_credits >= 15:
		player.have_credits += 1
		cre = player.have_credits
		Kill.send(player.index, green='\x04', default=default, cred=cre)
		
		
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
				victim = Player.from_userid(userid)
				hurter = Player.from_userid(attacker)
				if not victim.team == hurter.team:
					if not victim.team == 2:
						infect(userid)
						
@Event('player_hurt')
def player_hurt(args):
	userid = args.get_int('userid')
	attacker = args.get_int('attacker')
	if attacker > 0:
		victim = Player.from_userid(userid)
		hurter = Player.from_userid(attacker)
		if not victim.team == hurter.team:
			if args.get_string('weapon') == 'hegrenade' and FIRE:
				burn(userid, 10)
			else:
				if not hurter.is_bot() and HINT:
					player = ZombiePlayer.from_userid(args['attacker'])
					player.player_target = userid
					player.delay(0.1, infopanel, (attacker,)) # Not sure will this work properly

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
			if attacker_player.clan_tag in Clan:
				attacker_player.max_health += Boost
				attacker_player.health = attacker_player.max_health
				attacker_player.speed = Speed
            
@Event('player_death')
def player_death(args):
	userid = args.get_int('userid')
	Player.from_userid(userid).delay(0.1, respawn, (userid,))
	
@Event('weapon_fire_on_empty')
def weapon_fire_on_empty(args):
	if WEAPON_REMOVE:
		userid = args.get_int('userid')
		weapon = args.get_string('weapon')
		player = Player(index_from_userid(userid))
		if player.primary:
			player.primary.remove()
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
		primary = player.primary
		secondary = player.secondary
		we = player.get_active_weapon()
		if GAME_NAME == 'csgo':
			weapon = (we.item_definition_index)
		else:
			weapon = we
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
			if GAME_NAME == 'cstrike' or GAME_NAME == 'csgo':
				player.set_property_bool('m_bHasHelmet', 1)
			queue_command_string('mp_humanteam ct')
		else:
			if GAME_NAME == 'csgo':
				player.emit_sound(sample='sound/zombie/ze-infected3.mp3',volume=1.0,attenuation=0.5)
			else:
				player.emit_sound(sample='ambient/creatures/town_child_scream1.wav',volume=1.0,attenuation=0.5)
			player.switch_team(2)
			player.set_noblock(True)
			player.health = 10
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
	if GAME_NAME == 'csgo':
		player.emit_sound(sample='sound/zombie/ze-infected3.mp3',volume=1.0,attenuation=0.5)
	else:
		player.emit_sound(sample='ambient/creatures/town_child_scream1.wav',volume=1.0,attenuation=0.5)
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
