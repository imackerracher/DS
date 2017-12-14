import pika
import logging
import ic_protocol
import threading

"""
Contains usefull classes that the client uses
"""


# FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
# logging.basicConfig(level=logging.DEBUG, format=FORMAT)
# LOG = logging.getLogger()

class ClientChatroom:
    """
    Publish subscribe pattern. The chatroom on the client side. Runs as a deamon thread in the background.
    """

    def __init__(self, name, private=True):
        self.name = name
        self.private = private
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='127.0.0.1'))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=self.name,
                                      exchange_type='fanout')
        result = self.channel.queue_declare(exclusive=True)
        queue_name = result.method.queue
        self.channel.queue_bind(exchange=self.name,
                                queue=queue_name)
        self.channel.basic_consume(self.callback,
                                   queue=queue_name,
                                   no_ack=True)
        self.main()

    def main(self):
        print('Chatroom %s running...' % self.name)
        self.channel.start_consuming()

    def callback(self, ch, method, properties, body):
        print('\n          %s\n' % body)
        return


####### User Action Protocol #########
_REGISTER = 'r'
_CREATE = 'c'
_MESSAGE = 'm'
_GET_ROOMS = 'g'
_JOIN = 'j'

class ClientHandler:
    """
    Handles requests made by client and the responses from the server.
    """
    def __init__(self):
        self.chatrooms = []

    def handle(self, message):
        """
        :param message: Input message by the client
        :return: Corresponding action
        """
        print 'in client handle'
        split_message = message.split()
        print split_message
        action = split_message[0]
        if len(split_message) > 1:
            user_input_1 = split_message[1]
            if len(split_message) > 2:
                user_input_2 = split_message[2]
        if action == _REGISTER:
            body = ic_protocol._REGISTER + ic_protocol._MESSAGE_SEP + user_input_1
        elif split_message[0] == _CREATE:
            body = ic_protocol._CREATE_CHATROOM + ic_protocol._MESSAGE_SEP + user_input_1
        elif split_message[0] == _MESSAGE:
            # m:CHATROOM:MESSAGE
            body = ic_protocol._MESSAGE + ic_protocol._MESSAGE_SEP + \
                   user_input_1 + ic_protocol._MESSAGE_SEP + user_input_2
        elif split_message[0] == _GET_ROOMS:
            body = ic_protocol._GET_CHATROOMS
        elif split_message[0] == _JOIN:
            body = ic_protocol._JOIN_ROOM + ic_protocol._MESSAGE_SEP + user_input_1
        else:
            body = ''
        return body

    def response_process(self, rsp):
        if ic_protocol.server_process(rsp) == ic_protocol._CREATE_CHATROOM:
            self.create_thread(rsp)
        elif ic_protocol.server_process(rsp) == ic_protocol._GET_CHATROOMS:
            self.list_rooms(rsp)
        elif ic_protocol.server_process(rsp) == ic_protocol._UNAME_TAKEN:
            print('Username already taken, choose another')
        elif ic_protocol.server_process(rsp) == ic_protocol._JOIN_ROOM:
            self.create_thread(rsp.split(ic_protocol._MESSAGE_SEP)[2])
        elif ic_protocol.server_process(rsp) == ic_protocol._CHATROOM_NON_EXISTANT:
            print('Chatroom nonexistant')
        elif ic_protocol.server_process(rsp) == ic_protocol._MESSAGE:
            print('Message sent!')
        else:
            print('NO ADEQUATE ACTION FOUND. THE RESPONSE WAS %s' % rsp)
            print('SERVER PROCESS: %s' % ic_protocol.server_process(rsp))

    def create_thread(self, rsp):
        thread_name = rsp.split(ic_protocol._MESSAGE_SEP)[2]
        new_thread = threading.Thread(target=self.chatroom_thread, args=(thread_name,))
        new_thread.daemon = True
        new_thread.start()
        print('In chat %s' %thread_name)
        self.chatrooms.append(new_thread)

    def chatroom_thread(self, name):
        chatroom = ClientChatroom(name)
        return

    def list_rooms(self, rsp):
        chatrooms = rsp.split(ic_protocol._MESSAGE_SEP)[1].split(',')
        print('Available Chatrooms:')
        for n in chatrooms:
            print(n)
