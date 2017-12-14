from server_chatroom import ServerChatroom
import pika


name = 'test'
connection = pika.BlockingConnection(pika.ConnectionParameters(host='127.0.0.1'))
channel = connection.channel()
channel.exchange_declare(exchange=name,
                         exchange_type = 'fanout')
#self.channel.queue_declare(queue=self.name)
print('Chatroom %s running...' % name)
users = []

message = 'TEST MESSAGE'

channel.basic_publish(exchange=name,
                      routing_key='',
                      body=message)

print('sent message...')
connection.close()

