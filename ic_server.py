import os
import logging
import pika
import ic_protocol
from argparse import ArgumentParser
from server_chatroom import ServerChatroom



class Server:
    def __init__(self, args):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=args.laddr))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='rpc_queue')
        self.channel.basic_qos(prefetch_count=1)
        self.usernames = []
        self.online_users = []
        self.chatrooms = []
        self.messages = []
        # Start the main thread now
        try:
            self.start_main()
        except:
            #Delete queue upon error, mainly usefull when client crashes
            self.channel.queue_delete(queue='rpc_queue')

    def start_main(self):
        self.channel.basic_consume(self.callback, queue='rpc_queue')
        print(' [*] Waiting for messages. To exit press CTRL+C')
        self.channel.start_consuming()

    def callback(self, ch, method, properties, body):
        def respond(rsp):
            print 'respond'
            ch.basic_publish(exchange='',
                             routing_key=properties.reply_to,
                             properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                             body=rsp)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        print body

        if ic_protocol.server_process(body) == ic_protocol._REGISTER:
            username = body.split(ic_protocol._MESSAGE_SEP)[1]
            password = body.split(ic_protocol._MESSAGE_SEP)[2]
            if username not in [user[0] for user in self.usernames]:
                self.usernames.append((username, password))
                self.online_users.append(username)
                print('Successfully registered user %s' % username)
                respond(ic_protocol._ACK)
            else:
                print('Username %s taken\n' % username)
                respond(ic_protocol._UNAME_TAKEN)
        elif (ic_protocol.server_process(body) == ic_protocol._CREATE_CHATROOM or
                      ic_protocol.server_process(body) == ic_protocol._CREATE_PRIVATE_CHATROOM):
            private = False
            if ic_protocol.server_process(body) == ic_protocol._CREATE_PRIVATE_CHATROOM:
                private = True
            inf = body.split(ic_protocol._MESSAGE_SEP)
            chatroom = ServerChatroom(inf[2], private)
            chatroom.add_user(inf[1])
            self.chatrooms.append(chatroom)
            response = ic_protocol._ACK + ic_protocol._MESSAGE_SEP + \
                       ic_protocol._CREATE_CHATROOM + ic_protocol._MESSAGE_SEP + \
                       chatroom.name
            respond(response)
            print('Started chatroom %s' % chatroom.name)

        elif ic_protocol.server_process(body) == ic_protocol._MESSAGE:
            # m:CHATROOM:MESSAGE
            inf = body.split(ic_protocol._MESSAGE_SEP)
            chatroom_name = inf[2]
            message = inf[3]
            try:
                index = self.get_chatroom(chatroom_name)
                self.chatrooms[index].publish_message('{0}: {1}'.format(inf[1],message))
                respond(ic_protocol._ACK + ic_protocol._MESSAGE_SEP + ic_protocol._MESSAGE)
            except:
                respond(ic_protocol._CHATROOM_NON_EXISTANT)

        elif ic_protocol.server_process(body) == ic_protocol._GET_CHATROOMS:
            response = ','.join([chatroom.name for chatroom in self.chatrooms if not chatroom.private])
            respond(ic_protocol._GET_CHATROOMS + ic_protocol._MESSAGE_SEP + response)

        elif ic_protocol.server_process(body) == ic_protocol._JOIN_ROOM:
            inf = body.split(ic_protocol._MESSAGE_SEP)
            chatroom_name = inf[2]
            try:
                index = self.get_chatroom(chatroom_name)
                self.chatrooms[index].add_user(inf[1])
                self.chatrooms[index].publish_message('User %s joined this chat\n' % inf[1])
                respond(ic_protocol._ACK + ic_protocol._MESSAGE_SEP + \
                        ic_protocol._JOIN_ROOM + ic_protocol._MESSAGE_SEP + \
                        chatroom_name)
            except:
                respond(ic_protocol._CHATROOM_NON_EXISTANT)

        elif ic_protocol.server_process(body) == ic_protocol._INVITE:
            inf = body.split(ic_protocol._MESSAGE_SEP)
            try:
                # i:USER:CURRENTCHAT:INVITECHAT
                index_invited_chat = self.get_chatroom(inf[3])
                name = self.chatrooms[index_invited_chat].name
                key = self.chatrooms[index_invited_chat].key
                index_current_room = self.get_chatroom(inf[2])
                self.chatrooms[index_current_room].publish_message(
                    'You have received an invitation to the private chatroom {0}.'
                    ' To join this chatroom enter \"j {1} {2}\".\n If you are already '
                    'in this chatroom then ignore this message\n'.format(name, name, key))
                respond(ic_protocol._ACK)
            except Exception as e:
                respond(ic_protocol._INV)

        elif ic_protocol.server_process(body) == ic_protocol._USERS:
            respond(ic_protocol._USERS + ic_protocol._MESSAGE_SEP + ','.join([user[0] for user in self.usernames]))

        elif ic_protocol.server_process(body) == ic_protocol._JOIN_ON_INVITE:
            inf = body.split(ic_protocol._MESSAGE_SEP)
            chatroom_name = inf[1]
            key = inf[2]
            try:
                index = self.get_chatroom(chatroom_name)
                if self.chatrooms[index].key == key:
                    self.chatrooms[index].add_user(inf[1])
                    self.chatrooms[index].publish_message('User %s joined this chat\n' % inf[1])
                    respond(ic_protocol._ACK + ic_protocol._MESSAGE_SEP + \
                            ic_protocol._JOIN_ROOM + ic_protocol._MESSAGE_SEP + \
                            chatroom_name)
            except:
                respond(ic_protocol._CHATROOM_NON_EXISTANT)

        elif ic_protocol.server_process(body) == ic_protocol._LEAVE_ROOM:
            inf = body.split(ic_protocol._MESSAGE_SEP)
            for chatroom in self.chatrooms:
                if inf[1] in chatroom.users:
                    chatroom.users.remove(inf[1])
                    chatroom.publish_message('User {0} has left the chatroom {1}\n'.format(inf[1], chatroom.name))
            respond(ic_protocol._ACK)

        elif ic_protocol.server_process(body) == ic_protocol._USERS_SPECIFIC_CHAT:
            inf = body.split(ic_protocol._MESSAGE_SEP)
            try:
                index = self.get_chatroom(inf[2])
                respond(ic_protocol._USERS_SPECIFIC_CHAT + ic_protocol._MESSAGE_SEP + \
                        ','.join([user for user in self.chatrooms[index]]))
            except:
                respond(ic_protocol._INV)

        elif ic_protocol.server_process(body) == ic_protocol._DISCONNECT:
            inf = body.split(ic_protocol._MESSAGE_SEP)
            self.online_users.remove(inf[1])
            for chatroom in self.chatrooms:
                if inf[1] in chatroom.users:
                    chatroom.users.remove(inf[1])
                    chatroom.publish_message('User {0} has left the chatroom {1}\n'.format(inf[1], chatroom.name))
            respond(ic_protocol._ACK)



    def get_chatroom(self, chatroom_name):
        for i in range(len(self.chatrooms)):
            if self.chatrooms[i].name == chatroom_name:
                return i
        return False




if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-l', '--laddr', help="Listen address. Default localhost.", default='127.0.0.1')
    parser.add_argument('-p', '--port', help="Listen on port.", default=5672, type=int)
    args = parser.parse_args()
    Server(args)
