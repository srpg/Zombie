import random, path
#   Commands
from commands.say import SayCommand
#   Engine
from engines.precache import Model
from engines.server import queue_command_string
#   Entity
from entities.entity import Entity
#   Events
from events.hooks import PreEvent, EventAction
from events import Event
#   Filters
from filters.weapons import WeaponClassIter
from filters.players import PlayerIter
#   Player
from players.entity import Player
from players.helpers import index_from_userid
# Download
from stringtables.downloads import Downloadables
# Messages
from messages import SayText2, HintText
from translations.strings import LangStrings
# Menus
from menus import SimpleMenu, SimpleOption
from menus import Text, PagedMenu, PagedOption

weapons = [weapon.basename for weapon in WeaponClassIter(not_filters='knife')]
primaries = [weapon.name for weapon in WeaponClassIter(is_filters='primary')]
secondaries = [weapon.name for weapon in WeaponClassIter(is_filters='pistol')]

HAS_INFECTED = False

zprops = {1: '2-Filing Cabinet-models/props/cs_office/file_cabinet1.mdl', 2: '3-Barrel-models/props/de_train/Barrel.mdl', 3: '4-Dryer-models/props/cs_militia/dryer.mdl', 4: '5-Wooden Crate-models/props_junk/wood_crate001a.mdl', 5: '7-Gas Pump-models/props_wasteland/gaspump001a.mdl', 6: '15-Dumpster-models/props_junk/TrashDumpster01a.mdl'}
close = 0
zombie_models = ['models/player/zh/zh_charple001.mdl','models/player/zh/zh_corpse002.mdl','models/player/zh/zh_zombie003.mdl','models/player/ics/hellknight_red/t_guerilla.mdl']

default = '\x01'
cyan = '\x0700CED1'
green='\x04'
#======================
# Translated Messages
#======================
chat = LangStrings('zombie_chat')
market_chat = LangStrings('market_chat')

Kill = SayText2(chat['Zprop_credits'])
Game = SayText2(chat['Game'])
Market = SayText2(chat['Market'])
Tp = SayText2(chat['Teleport'])
infect_message = SayText2(chat['Infect_first'])
weapon_remove = SayText2(chat['Weapon_remove'])
respawn = SayText2(chat['Respawn'])
restore = SayText2(chat['Weapon_restore'])
buy = SayText2(chat['Zprop_buy'])
zprop_alive = SayText2(chat['Zprop Alive'])
zprop_ct = SayText2(chat['Zprop CT'])
#======================
# Market Messages
#======================
weapon_afford = SayText2(market_chat['Weapon Afford'])
weapon_purchase_alive = SayText2(market_chat['Weapon Puirchase Alive'])
market_ct = SayText2(market_chat['Market_ct'])
market_alive =  SayText2(market_chat['Market_alive'])
ztele =  SayText2(market_chat['Ztele'])
ztele_alive = SayText2(market_chat['Ztele Alive'])
weapon_tell = SayText2(market_chat['Weapon'])
#======================
# Config
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

#======================
# Custom Player Class
#======================
class ZombiePlayer(Player):
	caching = True 

	def __init__(self, index):
		super().__init__(index)
		self.have_credits  	= 0
		self.player_target 	= False
		self.infect_type = None
		self.spawn_origin = None

	def ztele(self):
		index = self.index
		if self.dead:
			return ztele_alive.send(index, green=green, default=default)

		if self.team < 3:
			return ztele.send(index, green=green, default=default)

		self.origin = self.spawn_origin
		Tp.send(index, green=green, default=default)

	def infect(self):
		global HAS_INFECTED
		HAS_INFECTED = True
		self.switch_team(2)
		self.set_noblock(True)
		self.health = INFECT_HEALTH
		self.speed = 1.5
		self.gravity = 0.75
		self.godmode = False
		self.emit_sound(sample='ambient/creatures/town_child_scream1.wav',volume=1.0,attenuation=0.5)

		for weapon in self.weapons():
			if weapon.classname != 'weapon_knife':
				weapon.remove()

		self.restrict_weapons(*weapons)    
		self.set_model(Model(random.choice(zombie_models)))
        
		infect_message.send(name=self.name, default=default, green='\x04')
		if self.infect_type == 'First':
			self.origin = self.spawn_origin
			for player in PlayerIter('all'):
				if player.index != self.index:
					player.switch_team(3)
					player.godmode = False

		round_checker()

	def uninfect(self):
		self.unrestrict_weapons(*weapons)
		self.switch_team(3)
		self.spawn()
		respawn.send(self.index, green=green, default=default)

	def give_weapons_back(self, weapon):
		index = self.index
		if self.is_bot():
			return

		if self.is_wearing_clan_tag() == False:
			return

		if WEAPON_REMOVE == 0:
			return

		for weapons in self.weapons():
			if weapons.classname.replace('weapon_', '', 1) == weapon:
				weapons.remove()
				weapon_remove.send(index, weapons=weapon, default=default, cyan=cyan, green=green)

		if Weapon_restore == 0:
			return

		self.give_named_item(f'weapon_{weapon}')
		restore.send(index, weapons=weapon, clan=self.clan_tag, default=default, cyan=cyan, green=green)

	def give_weapons_ct(self):
		if self.team < 3:
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
		current_credits = self.have_credits
		current_credits += 1
		if current_credits >= 15:
			current_credits = 15
		self.have_credits += current_credits
		Kill.send(self.index, green=green, default=default, cred=current_credits)

		if KILL_HP == 1:
			self.health = 100

		if self.is_wearing_clan_tag() == True:
			self.max_health += Boost
			self.health = self.max_health
			self.speed = Speed

	def infinite_clip(self):
		if self.is_bot():
			return

		if self.is_wearing_clan_tag() == False:
			return

		if Infitebullets == 0:
			return

		weapon = self.get_active_weapon()
		if weapon is None:
			return

		classname = weapon.classname
		if classname in primaries + secondaries:
			weapon.clip += 1

	def is_wearing_clan_tag(self):
		if Clan == self.clan_tag:
			return True
		else:
			return False
#======================
# Other
#======================
def infopanel(attacker):
	player = ZombiePlayer.from_userid(attacker)
	target_userid = player.player_target
	if target_userid == False:
		return

	try:
		target = Player.from_userid(target_userid)
	except ValueError:
		player.player_target = False

	if not target.dead and target.health > 0:
		__msg__ = f'{target.name}: {target.health}'
		HintText(__msg__).send(player.index)
	else:
		player.player_target = False

#======================
# Download/Load
#======================
DOWNLOADLIST_PATH    = path.Path(__file__).dirname().joinpath('css.txt')

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

def build_entity(userid, entity_model):
	player = Player.from_userid(userid)
	if entity_model == 'models/props_junk/TrashDumpster01a.mdl' or entity_model == 'models/props_wasteland/gaspump001a.mdl':
		entity = Entity.create('prop_physics_override')
	else:
		entity = Entity.create('prop_physics')
	entity.model = Model(entity_model)
	entity.origin = player.view_cordinates()
	entity.spawn()

#===================
# Events
#===================
@PreEvent('server_cvar', 'player_team', 'player_disconnect', 'player_connect_client')
def pre_events(game_event):
	return EventAction.STOP_BROADCAST

@Event('round_end')
def round_end(args):
	global HAS_INFECTED
	HAS_INFECTED = False
	queue_command_string('mp_humanteam any')
	for alive_players in player_list():
		ZombiePlayer.from_userid(alive_players).uninfect()

@Event('round_start')
def round_start(ev):
	userid = random.choice(player_list())
	if userid:
		player = ZombiePlayer(index_from_userid(userid))
		player.infect_type = 'First'
		player.delay(15, player.infect)
		for others in player_list():
			ct = ZombiePlayer.from_userid(others)
			ct.delay(16, ct.give_weapons_ct)

@Event('player_spawn')
def player_spawn(event):
	player = ZombiePlayer.from_userid(event['userid'])

	if HAS_INFECTED == False:
		player.godmode = True

	player.gravity = 1
	player.set_noblock(True)
	player.cash = 12000
	player.unrestrict_weapons(*weapons)
	player.spawn_origin = player.origin
	player.infect_type = None

	index = player.index

	Game.send(index, green=green, default=default)
	Market.send(index, green=green, default=default)
							
@Event('player_hurt')
def player_hurt(args):
	userid = args.get_int('userid')
	attacker = args.get_int('attacker')
	if attacker > 0:
		victim = ZombiePlayer.from_userid(userid)
		hurter = ZombiePlayer.from_userid(attacker)
		if not victim.team == hurter.team:
			if args.get_string('weapon') == 'hegrenade' and FIRE:
				victim.ignite_lifetime(10)
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
	victim = ZombiePlayer.from_userid(userid)
	if attacker > 0:
		player = ZombiePlayer.from_userid(attacker)
		if not victim.team == player.team:
			player.give_kill_bonus()
	victim.uninfect()

@PreEvent('weapon_fire_on_empty')
def pre_weapon_fire_on_empty(args):
	ZombiePlayer.from_userid(args['userid']).give_weapons_back(args.get_string('weapon'))

@Event('weapon_fire')
def weapon_fire(args):
	ZombiePlayer.from_userid(args['userid']).infinite_clip()

#==========================
# Chat Commands
#==========================
@SayCommand(['market', '!market', '/market'])
def market_command(command, index, teamonly):
	player = Player(index)
	if not player.dead:
		if player.team > 2:
			main_menu.send(index)
		else:
			market_ct.send(index, green=green)
	else:
		market_alive.send(index, green=green)
	return False

@SayCommand(['ztele', '!ztele', '/ztele'])
def ztele_command(command, index, teamonly):
	ZombiePlayer(index).ztele()
	return False

@SayCommand(['zprop', '/zprop', '!zprop'])
def zrop_command(command, index, teamonly):
	player = Player(index)
	if player.team < 3:
		return zprop_ct.send(index, green=green, default=default)
	if player.dead:
		return zprop_alive.send(index, green=green, default=default)
	zprop_menu.send(index)
	return False
#==========================
# Menu callbacks
#==========================
def main_menu_callback(_menu, _index, _option):
	choice = _option.value
	if choice:
		if choice == 'primary':
			primaries_menu.send(_index)
		else:
			secondaries_menu.send(_index)

def market_secondary_select(_menu, _index, _option):
	choice = _option.value
	if choice:
		player = Player(_index)
		price = choice.cost
		weapon = choice.basename.title()

		if player.dead:
			return weapon_purchase_alive.send(_index, weapon=weapon, green=green, cyan=cyan, default=default)

		if player.cash >= price:
			player.cash -= price

			secondary = player.secondary
			if secondary is not None:
				secondary.remove()

			player.give_named_item(choice.name)
			weapon_tell.send(_index, weapon=weapon, price=price, green=green, cyan=cyan, default=default)

		else:
			weapon_afford.send(_index, weapon=weapon, missing=int(price - player.cash), green=green, cyan=cyan, default=default)

def market_primary_select(_menu, _index, _option):
	choice = _option.value
	if choice:
		player = Player(_index)
		price = choice.cost
		weapon = choice.basename.title()

		if player.dead:
			return weapon_purchase_alive.send(_index, weapon=weapon, green=green, cyan=cyan, default=default)

		if player.cash >= price:
			player.cash -= price

			primary = player.primary
			if primary is not None:
				primary.remove()

			player.give_named_item(choice.name)
			weapon_tell.send(_index, weapon=weapon, price=price, green=green, cyan=cyan, default=default)

		else:
			weapon_afford.send(_index, weapon=weapon, missing=int(price - player.cash), green=green, cyan=cyan, default=default)

def zprop_menus_select(_menu, _index, _option):
	choice = _option.value
	if choice:
		player = ZombiePlayer(_index)
		if player.dead:
			return zprop_alive.send(_index, green=green, default=default)

		if player.team <= 3:
			return zprop_ct.send(_index, green=green, default=default)

		price = int(zprops[choice].split('-')[0])
		entity_name = zprops[choice].split('-')[1]
		entity_model= zprops[choice].split('-')[2]
		if player.have_credits >= price:
			player.have_credits -= price
			build_entity(player.userid, entity_model)
			buy.send(_index, green=green,  default=default, price=price, cur=player.have_credits, type=entity_name)
#==========================
# Menu build callbacks
#==========================
def market_secondaries(menu, index):
	menu.clear()
	player = Player(index)
	for secondary in WeaponClassIter(is_filters='pistol'):
		afford = player.cash >= secondary.cost and not player.dead
		menu.append(PagedOption(f'{secondary.basename.title()} [{secondary.cost}$]', secondary, afford, afford))

def market_primaries(menu, index):
	menu.clear()
	player = Player(index)
	for primaries in WeaponClassIter(is_filters='primary'):
		afford = player.cash >= primaries.cost and not player.dead
		menu.append(PagedOption(f'{primaries.basename.title()} [{primaries.cost}$]', primaries, afford, afford))

def zprop_menus(menu, index):
	menu.clear()
	player = ZombiePlayer(index)
	for i in sorted(zprops):
		price = int(zprops[i].split('-')[0])
		name = zprops[i].split('-')[1]
		afford = player.have_credits >= price and not player.dead
		menu.append(PagedOption(f'{name} [Credits: {price}]', i, afford, afford))
#==========================
# Menus
#==========================
main_menu = SimpleMenu()
main_menu.append(Text('Market'))
main_menu.append(Text('Main Menu'))
main_menu.append(Text(' '))
main_menu.append(SimpleOption(1, 'Primaries', 'primary'))
main_menu.append(SimpleOption(2, 'Secondaries', 'secondary'))
main_menu.append(Text(' '))
main_menu.append(SimpleOption(close, 'Close', None))
main_menu.select_callback = main_menu_callback

secondaries_menu = PagedMenu(title='Market\nPurchase secondary\n')
secondaries_menu.build_callback = market_secondaries
secondaries_menu.select_callback = market_secondary_select

primaries_menu = PagedMenu(title='Market\nPurchase primary\n')
primaries_menu.build_callback = market_primaries
primaries_menu.select_callback = market_primary_select

zprop_menu = PagedMenu(title='Zprops\n')
zprop_menu.build_callback = zprop_menus
zprop_menu.select_callback = zprop_menus_select