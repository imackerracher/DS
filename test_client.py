import pika



name = 'test'
connection = pika.BlockingConnection(pika.ConnectionParameters(host='127.0.0.1'))
channel = connection.channel()
channel.exchange_declare(exchange=name,
                         exchange_type='fanout')
result = channel.queue_declare(exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange=name,
                   queue=queue_name)



def callback(ch, method, properties, body):
    print('received message %s' % body)

channel.basic_consume(callback,
                      queue=queue_name,
                      no_ack=True)



channel.start_consuming()


