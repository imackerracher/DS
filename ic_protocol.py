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
    elif message.startswith(_MESSAGE + _MESSAGE_SEP):
        return _MESSAGE
    elif message.startswith(_GET_CHATROOMS):
        return _GET_CHATROOMS
    elif message.startswith(_JOIN_ROOM + _MESSAGE_SEP):
        return _JOIN_ROOM

    else:
        return 'NADA, NIET, NICHTS, NOTHING, RIEN'