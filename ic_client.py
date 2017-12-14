import logging
import os
import pika
from argparse import ArgumentParser
import ic_protocol
import time
import uuid
import threading
from client_chatroom import ClientChatroom


class Client(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=args.saddr))
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue
        self.channel.basic_consume(self.on_response, no_ack=True, queue=self.callback_queue)
        self.chatrooms = []
        self.main()


    def main(self):
        while True:
            time.sleep(1)
            try:
                message = raw_input('enter a command followed by optional message: ')
                self.message_process(message)
            except KeyboardInterrupt:
                self.channel.close()
                self.connection.close()
                break


    def message_process(self, message):
        split_message = message.split()
        print 'in message process'
        if split_message[0] == 'r':
            body = ic_protocol._REGISTER + ic_protocol._MESSAGE_SEP + split_message[1]
        elif split_message[0] == 'c':
            body = ic_protocol._CREATE_CHATROOM + ic_protocol._MESSAGE_SEP + split_message[1]
        elif split_message[0] == 'm':
            # m:CHATROOM:MESSAGE
            body = ic_protocol._MESSAGE + ic_protocol._MESSAGE_SEP + \
                   split_message[1] + ic_protocol._MESSAGE_SEP + \
                   split_message[2]
        elif split_message[0] == 'g':
            body = ic_protocol._GET_CHATROOMS
        elif split_message[0] == 'j':
            body = ic_protocol._JOIN_ROOM + ic_protocol._MESSAGE_SEP + split_message[1]
        else:
            body = ''
        print 'body %s' % body
        self.response = None
        self.corr_id = str(uuid.uuid4())
        rsp = self.call(body)
        self.responce_process(rsp)

    def responce_process(self, rsp):
        if ic_protocol.server_process(rsp) == ic_protocol._CREATE_CHATROOM:
            split_rsp = rsp.split(ic_protocol._MESSAGE_SEP)
            c_thread = threading.Thread(target=self.chatroom_thread, args=(split_rsp[2],))
            c_thread.daemon = True
            c_thread.start()
            self.chatrooms.append(c_thread)
            print('Opened chatroom %s' % split_rsp[2])
        elif ic_protocol.server_process(rsp) == ic_protocol._GET_CHATROOMS:
            chatrooms = rsp.split(ic_protocol._MESSAGE_SEP)[1].split(',')
            print('Available Chatrooms:')
            for n in chatrooms:
                print(n)
        elif ic_protocol.server_process(rsp) == ic_protocol._UNAME_TAKEN:
            print('Username already taken, choose another')
        elif ic_protocol.server_process(rsp) == ic_protocol._JOIN_ROOM:
            chat_thread = threading.Thread(target=self.chatroom_thread, args=(rsp.split(ic_protocol._MESSAGE_SEP)[2],))
            chat_thread.daemon = True
            chat_thread.start()
            print('Joined room')
        elif ic_protocol.server_process(rsp) == ic_protocol._CHATROOM_NON_EXISTANT:
            print('Chatroom nonexistant')
        elif ic_protocol.server_process(rsp) == ic_protocol._MESSAGE:
            print('Message sent!')
        else:
            print('NO ADEQUATE ACTION FOUND. THE RESPONSE WAS %s' % rsp)
            print('SERVER PROCESS: %s' % ic_protocol.server_process(rsp))

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
    Client()
