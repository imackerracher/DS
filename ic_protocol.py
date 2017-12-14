import random

_ACK = 'ACK'
_DISCONNECT = 'DIS'
_LISTEN = 'LISTEN'
_REGISTER = '0'
_UNAME_TAKEN = '1'
_CREATE_CHATROOM = '2'
_MESSAGE = '3'
_CHATROOM_NON_EXISTANT = '4'
_GET_CHATROOMS = '5'
_JOIN_ROOM = '6'
_USERS = '7'
_CREATE_PRIVATE_CHATROOM = '8'


_MESSAGE_SEP = ':'
_INSTANCE_SEP = '$'

def server_process(message):

    if message.startswith(_ACK):
        if message.startswith(_ACK + _MESSAGE_SEP + _CREATE_CHATROOM):
            return _CREATE_CHATROOM
        elif message.startswith(_ACK + _MESSAGE_SEP + _JOIN_ROOM):
            return _JOIN_ROOM
        elif message.startswith(_ACK + _MESSAGE_SEP + _MESSAGE):
            return
    elif message.startswith(_REGISTER + _MESSAGE_SEP):
        return _REGISTER
    elif message.startswith(_UNAME_TAKEN):
        return _UNAME_TAKEN
    elif message.startswith(_CREATE_CHATROOM + _MESSAGE_SEP):
        return _CREATE_CHATROOM
    elif message.startswith(_CREATE_PRIVATE_CHATROOM + _MESSAGE_SEP):
        return _CREATE_PRIVATE_CHATROOM
    elif message.startswith(_MESSAGE + _MESSAGE_SEP):
        return _MESSAGE
    elif message.startswith(_GET_CHATROOMS):
        return _GET_CHATROOMS
    elif message.startswith(_JOIN_ROOM + _MESSAGE_SEP):
        return _JOIN_ROOM
    elif message.startswith(_USERS):
        return _USERS
    elif message.startswith(_DISCONNECT):
        return _DISCONNECT

    else:
        return random.choice('NADA', 'NIET', 'NICHTS', 'NOTHING', 'RIEN')