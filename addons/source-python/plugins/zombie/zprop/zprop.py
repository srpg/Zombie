from engines.server import engine_server
from players.helpers import index_from_userid, userid_from_index
from players.entity import Player
from entities.entity import Entity
from zombie import zombie
from menus import SimpleMenu, Text, SimpleOption
from commands.say import SayFilter
from messages import SayText2
from core import GAME_NAME

def tell(userid, text):
	SayText2(message='' + text).send(index_from_userid(userid))

def is_queued(_menu, _index):
	q = _menu._get_queue_holder()
	for i in q:
		if i == _index:
			for x in q[i]:
				return True
	return False

@SayFilter
def sayfilter(command, index, teamonly):
	userid = None
	if index:
		userid = userid_from_index(index)
	
		if userid and command:
			text = command[0].replace('!', '', 1).replace('/', '', 1).lower()
			args = command.arg_string
			if text == 'zprop':
				if GAME_NAME == 'cstrike':
					if not Player(index_from_userid(userid)).team == 1:
						if not Player(index_from_userid(userid)).dead:
							zprop_menu(userid)
							return False
				else:
					tell(userid, '\x04Zrops not implented to csgo!')
					return False
				
def zprop_menu(userid):
	menu = SimpleMenu()
	if is_queued(menu, index_from_userid(userid)):
		return
	menu.append(Text('Zprops\nCurrent Credits: %s' % (zombie.players[userid]['credits'])))
	menu.append(Text('-' * 25))
	cab = zombie.players[userid]['credits'] >= 2
	bar = zombie.players[userid]['credits'] >= 3
	dr = zombie.players[userid]['credits'] >= 4
	woo = zombie.players[userid]['credits'] >= 5
	ga = zombie.players[userid]['credits'] >= 7
	dump = zombie.players[userid]['credits'] >= 15
	menu.append(SimpleOption(1, 'Filing Cabinet[Credits: 2]', '1', cab, cab))
	menu.append(SimpleOption(2, 'Barrel[Credits: 3]', '2', bar, bar))
	menu.append(SimpleOption(3, 'Dryer[Credits: 4]', '3', dr, dr))
	menu.append(SimpleOption(4, 'Wooden Crate[Credits: 5]', '4', woo, woo))
	menu.append(SimpleOption(5, 'Gas Pump[Credits: 7]', '5', ga, ga))
	menu.append(SimpleOption(6, 'Dumpster[Credits: 15]', '6', dump, dump))
	menu.append(Text('-' * 25))
	menu.append(SimpleOption(0, 'Close', None))
	menu.select_callback = menu_callback
	menu.send(index_from_userid(userid))
	
def menu_callback(_menu, _index, _option):
	choice = _option.value
	if choice:
		userid = userid_from_index(_index)
		if choice == '1':
			cabinet(userid)
			current = zombie.players[userid]['credits']
			zombie.players[userid]['credits'] -= 2
			zombie.buy.send(index_from_userid(userid), green='\x04',  default='\x07FFB300', price='2', cur=current, type='Filing Cabinet')
		elif choice == '2':
			barrel(userid)
			current = zombie.players[userid]['credits']
			zombie.players[userid]['credits'] -= 3
			zombie.buy.send(index_from_userid(userid), green='\x04',  default='\x07FFB300', price='3', cur=current, type='Barrek')
		elif choice == '3':
			dryer(userid)
			current = zombie.players[userid]['credits']
			zombie.players[userid]['credits'] -= 4
			zombie.buy.send(index_from_userid(userid), green='\x04',  default='\x07FFB300', price='4', cur=current, type='Dryer')
		elif choice == '4':
			crate(userid)
			current = zombie.players[userid]['credits']
			zombie.players[userid]['credits'] -= 5
			zombie.buy.send(index_from_userid(userid), green='\x04',  default='\x07FFB300', price='5', cur=current, type='Wooden Crate')
		elif choice == '5':
			pump(userid)
			current = zombie.players[userid]['credits']
			zombie.players[userid]['credits'] -= 7
			zombie.buy.send(index_from_userid(userid), green='\x04',  default='\x07FFB300', price='7', cur=current, type='Gas Pump')
		elif choice == '6':
			dumpster(userid)
			current = zombie.players[userid]['credits']
			zombie.players[userid]['credits'] -= 15
			zombie.buy.send(index_from_userid(userid), green='\x04',  default='\x07FFB300', price='15', cur=current, type='Dumpster')
			
def cabinet(userid):
	player = Player(index_from_userid(userid))
	model = 'models/props/cs_office/file_cabinet1.mdl'
	entity = Entity.create('prop_physics')
	engine_server.precache_model(model)
	entity.set_key_value_vector('origin', player.eye_location + player.view_vector * 150)
	entity.set_key_value_string('model', model)
	entity.spawn()
	return entity.index

def barrel(userid):
	player = Player(index_from_userid(userid))
	model = 'models/props/de_train/Barrel.mdl'
	entity = Entity.create('prop_physics')
	engine_server.precache_model(model)
	entity.set_key_value_vector('origin', player.eye_location + player.view_vector * 150)
	entity.set_key_value_string('model', model)
	entity.spawn()
	return entity.index
    
def dryer(userid):
	player = Player(index_from_userid(userid))
	model = 'models/props/cs_militia/dryer.mdl'
	entity = Entity.create('prop_physics')
	engine_server.precache_model(model)
	entity.set_key_value_vector('origin', player.eye_location + player.view_vector * 150)
	entity.set_key_value_string('model', model)
	entity.spawn()
	return entity.index
    
def crate(userid):
	player = Player(index_from_userid(userid))
	model = 'models/props_junk/wood_crate001a.mdl'
	entity = Entity.create('prop_physics')
	engine_server.precache_model(model)
	entity.set_key_value_vector('origin', player.eye_location + player.view_vector * 150)
	entity.set_key_value_string('model', model)
	entity.spawn()
	return entity.index
    
def pump(userid):
	player = Player(index_from_userid(userid))
	model = 'models/props_wasteland/gaspump001a.mdl'
	entity = Entity.create('prop_physics_override')
	engine_server.precache_model(model)
	entity.set_key_value_vector('origin', player.eye_location + player.view_vector * 150)
	entity.set_key_value_string('model', model)
	entity.spawn()
	return entity.index
    
def dumpster(userid):
	player = Player(index_from_userid(userid))
	model = 'models/props_junk/TrashDumpster01a.mdl'
	entity = Entity.create('prop_physics_override')
	engine_server.precache_model(model)
	entity.set_key_value_vector('origin', player.eye_location + player.view_vector * 150)
	entity.set_key_value_string('model', model)
	entity.spawn()
	return entity.index
