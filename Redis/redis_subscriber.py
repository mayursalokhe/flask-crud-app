import redis

redis_client = redis.Redis(host='localhost',port=6379, db=0, decode_responses=True)

# channel = 'my_channel'
# pubsub.subscribe(channel)
# print(f'Subscribed to {channel}. Waiting for messages...')
# for msg in pubsub.listen():
#     if msg['type'] == 'message':
#         print(f'Received: {msg['data']}')

channels_input = input("Enter the channels to subscribe to (comma separated  ex-> 'a,b,c'): ")
channels_to_subscribe = [channel.strip() for channel in channels_input.split(',')]
# channels_to_subscribe = ['a', 'b', 'c']

def message_handler(message):
    print(f"Received message from {message['channel']} : {message['data']}")

pubsub = redis_client.pubsub()
pubsub.subscribe(**{channel: message_handler for channel in channels_to_subscribe})

print("Subscribed to channels:", channels_to_subscribe)
for message in pubsub.listen():
    if message['type'] == 'message':
        message_handler(message)
