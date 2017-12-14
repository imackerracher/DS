import pika
import string
import random
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
        if private:
            self.key = self.generate_key()
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
        if len(self.users) == 0:
            self.delete_chatroom()
        return

    def generate_key(self):
        """
        Secret key, needed if the chatroom is private.
        94^10 possibilities
        """
        alphabet = string.letters + string.digits + string.punctuation
        key = ''.join([random.choice(alphabet) for i in range(10)])
        return key


    def delete_chatroom(self):
        self.channel.close()
        self.connection.close()
        return