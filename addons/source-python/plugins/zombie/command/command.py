from commands.say import SayFilter

from filters.weapons import WeaponIter, WeaponClassIter
from weapons.manager import weapon_manager

from players.entity import Player
from players.helpers import index_from_userid, userid_from_index

from menus import SimpleMenu, Text, SimpleOption
from menus import PagedOption, PagedMenu

from translations.strings import LangStrings
from messages import SayText2

from zombie import zombie

weapon_list = weapon_manager.ini['weapons']

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
			if text == 'market':
				if not Player(index_from_userid(userid)).get_property_bool('pl.deadflag'):
					if not Player(index_from_userid(userid)).team == 2:
						market(userid)
					else:
						market_ct.send(index_from_userid(userid), green='\x04')
				else:
					market_alive.send(index_from_userid(userid), green='\x04')
				return False
			elif text == 'ztele':
				if not Player(index_from_userid(userid)).get_property_bool('pl.deadflag'):
					zombie.teleport(userid)
				else:
					ztele.send(index_from_userid(userid), green='\x04')
				return False

def market(userid):
	menu = PagedMenu(
	title = 'Market\n')
	if is_queued(menu, indexFromUserid(userid)):
		return
	for weapon in weapon_list:
		if 'cost' in weapon_list[weapon]:
			afford = Player(index_from_userid(userid)).cash >= weapon_list[weapon]['cost']
			menu.append(PagedOption('%s [%s$]' % (weapon, weapon_list[weapon]['cost']), weapon, afford, afford))
	menu.select_callback = menu_callback
	menu.send(indexFromUserid(userid))

#==================================
# Menu Call Backs
#==================================
def menu_callback(_menu, _index, _option):
	choice = _option.value
	if choice:
		userid = useridFromIndex(_index)
		player = Player(index_from_userid(userid))
		player.cash -= weapon_list[choice]['cost']
		player.client_command('drop', True)
		player.give_named_item('weapon_%s' % (choice))
		weapon_tell.send(index_from_userid(userid), weapon=choice, price=weapon_list[choice]['cost'], green='\x04', cyan=zombie.cyan, default=zombie.default)
