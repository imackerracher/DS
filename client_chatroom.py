import pika
import logging

#FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
#logging.basicConfig(level=logging.DEBUG, format=FORMAT)
#LOG = logging.getLogger()

class ClientChatroom:
    """
    Publish subscribe pattern
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
        print('received message %s' % body)
        return