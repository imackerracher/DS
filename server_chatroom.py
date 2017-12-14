import pika
import logging

#FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
#logging.basicConfig(level=logging.DEBUG, format=FORMAT)
#LOG = logging.getLogger()

class ServerChatroom:
    """
    Publish subscribe pattern
    """

    def __init__(self, name, private=False):
        self.name = name
        self.private = private
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='127.0.0.1'))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=self.name,
                                      exchange_type = 'fanout')
        #self.channel.queue_declare(queue=self.name)
        print('Chatroom %s running...' % self.name)
        self.users = []

    def add_user(self, username):
        self.users.append(username)
        return

    def publish_message(self, message):
        print('published message %s' % message)
        self.channel.basic_publish(exchange=self.name,
                                   routing_key='',
                                   body=message)
        return

    def delete_chatroom(self):
        self.channel.close()
        self.connection.close()
        return