from commands.say import SayFilter
from core import GAME_NAME
from filters.weapons import WeaponIter, WeaponClassIter
from weapons.manager import weapon_manager

from players.entity import Player
from players.helpers import index_from_userid, userid_from_index

from menus import SimpleMenu, Text, SimpleOption
from menus import PagedOption, PagedMenu

from translations.strings import LangStrings
from messages import SayText2

from zombie import zombie

if GAME_NAME == 'csgo':
	close = 9
else:
	close = 0

chat = LangStrings('market_chat')

market_ct = SayText2(chat['Market_ct'])
market_alive =  SayText2(chat['Market_alive'])
ztele =  SayText2(chat['Ztele'])
weapon_tell = SayText2(message=chat['Weapon'])

def tell(userid, text):
	SayText2(message='' + text).send(index_from_userid(userid))

def is_queued(_menu, _index):
	q = _menu._get_queue_holder()
	for i in q:
		if i == _index:
			for x in q[i]:
				return True
	return False

def useridFromIndex(index):
	return userid_from_index(index)

def indexFromUserid(userid):
	return index_from_userid(userid)

def remove_idle_weapons():
	for w in WeaponIter.iterator():
		if w.get_property_int('m_hOwnerEntity') in [-1, 0]:
			w.call_input('Kill')

@SayFilter
def sayfilter(command, index, teamonly):
	userid = None
	if index:
		userid = useridFromIndex(index)
	
		if userid and command:
			text = command[0].replace('!', '', 1).replace('/', '', 1).lower()
			args = command.arg_string
			player = Player.from_userid(userid)
			if text == 'market':
				if not player.get_property_bool('pl.deadflag'):
					if not player.team == 2:
						market_main(userid)
					else:
						market_ct.send(player.index, green='\x04')
				else:
					market_alive.send(player.index, green='\x04')
				return False
			elif text == 'ztele':
				if notplayer player.get_property_bool('pl.deadflag'):
					zombie.teleport(userid)
				else:
					ztele.send(player.index, green='\x04')
				return False

def market_main(userid):
	menu = SimpleMenu()
	if is_queued(menu, index_from_userid(userid)):
		return
	menu.append(Text('Market\nSection: Main Menu\n'))
	menu.append(Text('-' * 25))
	menu.append(SimpleOption(1, 'Primaries', 'Rifle'))
	menu.append(SimpleOption(2, 'Secondaries', 'Secondary'))
	menu.append(Text('-' * 25))
	menu.append(SimpleOption(close, 'Close', None))
	menu.select_callback = main_menu_callback
	menu.send(indexFromUserid(userid))

def market_rifle(userid):
	menu = PagedMenu(title = 'Market\nSection: Primaries\n')
	if is_queued(menu, index_from_userid(userid)):
		return
	for weapon in WeaponClassIter(is_filters='primary'):
		afford = Player(index_from_userid(userid)).cash >= weapon.cost
		menu.append(PagedOption('%s [%s$]' % (weapon.basename.upper(), weapon.cost), weapon, afford, afford))
	menu.select_callback = menu_callback
	menu.send(indexFromUserid(userid))
    
def market(userid):
	menu = PagedMenu(title = 'Market\nSection: Pistols\n')
	if is_queued(menu, index_from_userid(userid)):
		return
	for weapon in WeaponClassIter(is_filters='pistol'):
		afford = Player(index_from_userid(userid)).cash >= weapon.cost
		menu.append(PagedOption('%s [%s$]' % (weapon.basename.upper(), weapon.cost), weapon, afford, afford))
	menu.select_callback = menu_callback
	menu.send(indexFromUserid(userid))

#==================================
# Menu Call Backs
#==================================
def main_menu_callback(_menu, _index, _option):
	choice = _option.value
	if choice:
		userid = userid_from_index(_index)
		if choice == 'Rifle':
			market_rifle(userid)
			zombie.ZombiePlayer.from_userid(userid).primary_primary = 'rifle'
		elif choice == 'Secondary':
			market(userid)
			zombie.ZombiePlayer.from_userid(userid).secondary_pistol = 'secondary'
            
def menu_callback(_menu, _index, _option):
	choice = _option.value
	if choice:
		userid = userid_from_index(_index)
		player = ZombiePlayer(index_from_userid(userid))
		player.cash -= choice.cost
		if player.secondary_pistol == 'secondary':
			if player.secondary:
				player.secondary.remove()
		elif player.primary_primary == 'rifle':
			if player.primary:
				player.primary.remove()
		player.give_named_item('%s' % (choice.name))
		weapon_tell.send(index_from_userid(userid), weapon=choice.basename.upper(), price=choice.cost, green='\x04', cyan=zombie.cyan, default=zombie.default)
