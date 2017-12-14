import os
import logging
import pika
import ic_protocol
from argparse import ArgumentParser
from server_chatroom import ServerChatroom
import threading



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
        self.start_main()

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
            if username not in self.usernames:
                self.usernames.append(username)
                print('Successfully registered user %s' % username)
                respond(ic_protocol._ACK)
            else:
                print('Username %s taken' % username)
                respond(ic_protocol._UNAME_TAKEN)
        elif ic_protocol.server_process(body) == ic_protocol._CREATE_CHATROOM:
            name = body.split(ic_protocol._MESSAGE_SEP)[1]
            chatroom = ServerChatroom(name)
            self.chatrooms.append(chatroom)
            response = ic_protocol._ACK + ic_protocol._MESSAGE_SEP + \
                       ic_protocol._CREATE_CHATROOM + ic_protocol._MESSAGE_SEP + \
                       chatroom.name
            respond(response)
            print('Started chatroom %s' % chatroom.name)

        elif ic_protocol.server_process(body) == ic_protocol._MESSAGE:
            # m:CHATROOM:MESSAGE
            split_body = body.split(ic_protocol._MESSAGE_SEP)
            chatroom_name = split_body[1]
            message = split_body[2]
            try:
                index = self.get_chatroom(chatroom_name)
                self.chatrooms[index].publish_message(message)
                respond(ic_protocol._ACK + ic_protocol._MESSAGE_SEP + ic_protocol._MESSAGE)
            except:
                respond(ic_protocol._CHATROOM_NON_EXISTANT)

        elif ic_protocol.server_process(body) == ic_protocol._GET_CHATROOMS:
            response = ','.join([chatroom.name for chatroom in self.chatrooms])
            respond(ic_protocol._GET_CHATROOMS + ic_protocol._MESSAGE_SEP + response)

        elif ic_protocol.server_process(body) == ic_protocol._JOIN_ROOM:
            chatroom_name = body.split(ic_protocol._MESSAGE_SEP)[1]
            try:
                index = self.get_chatroom(chatroom_name)
                self.chatrooms[index].publish_message('User INSERT USER joined this chat')
                respond(ic_protocol._ACK + ic_protocol._MESSAGE_SEP + \
                        ic_protocol._JOIN_ROOM + ic_protocol._MESSAGE_SEP + \
                        chatroom_name)
            except:
                respond(ic_protocol._CHATROOM_NON_EXISTANT)


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