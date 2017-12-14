import pika
from argparse import ArgumentParser
import ic_protocol
import time
import uuid
import threading
import re
from client_chatroom import ClientChatroom


class Client(object):

    def __init__(self, args):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=args.saddr))
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue
        self.channel.basic_consume(self.on_response, no_ack=True, queue=self.callback_queue)
        self.chatrooms = []
        self.username = None
        self.main()


    def main(self):
        while True:
            time.sleep(1)
            try:
                if self.username is None:
                    name = raw_input('Enter a username: ')
                    if re.match(r'[a-zA-Z0-9]{3,}', name):
                        self.username = name
                        password = raw_input('Enter a password: ')
                        if re.match(r'[a-zA-Z0-9]{3,}', password):
                            self.message_process('r %s' % name + ic_protocol._MESSAGE_SEP + password)
                    else:
                        print('Invalid . May contain only numbers and letters. '
                              'Must be at least 3 characters long')


                else:
                    message = raw_input('Enter a command followed by optional message: ')
                    self.message_process(message)
            except KeyboardInterrupt:
                self.message_process(ic_protocol._DISCONNECT)
                self.channel.close()
                self.connection.close()
                break


    def message_process(self, message):
        split_message = message.split()
        action = split_message[0]
        if len(split_message) > 1:
            user_input_1 = split_message[1]
            if len(split_message) > 2:
                user_input_2 = split_message[2]
        if action == 'r':
            body = ic_protocol._REGISTER + ic_protocol._MESSAGE_SEP + user_input_1
        elif action == 'c':
            body = ic_protocol._CREATE_CHATROOM + ic_protocol._MESSAGE_SEP + user_input_1
        elif action == 'pc': #private chatroom
            body = ic_protocol._CREATE_PRIVATE_CHATROOM + ic_protocol._MESSAGE_SEP + user_input_1
        elif action == 'm':
            # m:CHATROOM:MESSAGE
            if user_input_1 not in self.chatrooms:
                print('Must join chatroom first before you can send messages')
                body = None
            else:
                body = ic_protocol._MESSAGE + ic_protocol._MESSAGE_SEP + \
                       user_input_1 + ic_protocol._MESSAGE_SEP + ' '.join(split_message[2:])
        elif action == 'g':
            body = ic_protocol._GET_CHATROOMS
        elif action == 'j':
            body = ic_protocol._JOIN_ROOM + ic_protocol._MESSAGE_SEP + user_input_1
        elif action == 'uo':
            body = ic_protocol._USERS
        elif action == 'u':
            body = ic_protocol._USERS_SPECIFIC_CHAT + ic_protocol._MESSAGE_SEP + user_input_1
        elif action == 'i':
            # i:CURRENTCHAT:INVITECHAT
            body = ic_protocol._INVITE + ic_protocol._MESSAGE_SEP + \
                   user_input_1 + ic_protocol._MESSAGE_SEP + \
                   user_input_2
        elif action == 'pj':
            #join private
            # pj:CHATROOM:KEY
            body = ic_protocol._JOIN_ON_INVITE + ic_protocol._MESSAGE_SEP + \
                   user_input_1 + ic_protocol._MESSAGE_SEP + user_input_2
        elif action == 'l':
            body = ic_protocol._LEAVE_ROOM + ic_protocol._MESSAGE_SEP + user_input_1
        elif action == ic_protocol._DISCONNECT:
            body = ic_protocol._DISCONNECT
        else:
            body = None


        if body is not None:
            print("body from client handler: %s" % body)
            self.response = None
            self.corr_id = str(uuid.uuid4())
            body = body.split(ic_protocol._MESSAGE_SEP)
            body = ic_protocol._MESSAGE_SEP.join([body[0], self.username] + body[1:])
            rsp = self.call(body)
            self.responce_process(rsp)
        else:
            print('invalid input')

    def responce_process(self, rsp):
        if ic_protocol.server_process(rsp) == ic_protocol._CREATE_CHATROOM:
            self.create_thread(rsp.split(ic_protocol._MESSAGE_SEP)[2])
        elif ic_protocol.server_process(rsp) == ic_protocol._GET_CHATROOMS:
            self.list_subjects(rsp)
        elif ic_protocol.server_process(rsp) == ic_protocol._UNAME_TAKEN:
            print('Username already taken, choose another')
        elif ic_protocol.server_process(rsp) == ic_protocol._JOIN_ROOM:
            self.create_thread(rsp.split(ic_protocol._MESSAGE_SEP)[2])
        elif ic_protocol.server_process(rsp) == ic_protocol._CHATROOM_NON_EXISTANT:
            print('Chatroom nonexistant')
        elif ic_protocol.server_process(rsp) == ic_protocol._MESSAGE:
            print('Message sent!')
        elif ic_protocol.server_process(rsp) == ic_protocol._USERS:
            self.list_subjects(rsp, u=True)
        elif ic_protocol.server_process(rsp) == ic_protocol._USERS_SPECIFIC_CHAT:
            self.list_subjects(rsp, u=True)
        else:
            print('NO ADEQUATE ACTION FOUND. THE RESPONSE WAS %s' % rsp)
            print('SERVER PROCESS: %s' % ic_protocol.server_process(rsp))

    def create_thread(self, thread_name):
        new_thread = threading.Thread(target=self.chatroom_thread, args=(thread_name,))
        new_thread.daemon = True
        new_thread.start()
        print('In chat %s' %thread_name)
        self.chatrooms.append(thread_name)

    def list_subjects(self, rsp, u=False):
        subjects = rsp.split(ic_protocol._MESSAGE_SEP)[1].split(',')
        print('Available users:' if u else 'Available Chatrooms:')
        for n in subjects:
            print(n)


    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def chatroom_thread(self, name):
        chatroom = ClientChatroom(name)
        return

    def call(self, message):
        print 'in call'
        self.channel.basic_publish(exchange='',
                                   routing_key='rpc_queue',
                                   properties=pika.BasicProperties(
                                       reply_to=self.callback_queue,
                                       correlation_id=self.corr_id,
                                   ),
                                   body=message)
        print('sent...')
        while self.response is None:
            self.connection.process_data_events()
        return self.response




if __name__ == "__main__":
    parser = ArgumentParser(description="Client for uploading/listing files.")
    parser.add_argument('-a', '--saddr', help="Address of the host. Default localhost.", default='127.0.0.1')
    parser.add_argument('-p', '--port', help="Listen on port.", default=5672, type=int)
    args = parser.parse_args()
    Client(args)
