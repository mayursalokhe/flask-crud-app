import redis
import random
import time
import threading

redis_client = redis.Redis(host='localhost',port=6379, db=0)

# channel = 'my_channel'
channels = ['a', 'b', 'c', 'd', 'e']


def publish_random_data(channel):
    while True:
        number_data = random.randint(10,99)
        redis_client.publish(channel,number_data)
        print(f'Published {number_data} to channel {channel}')
        time.sleep(5)

    # while True:
    #     # msg = input('Enter a message:')
    #     # redis_client.publish(channel, msg)
    #     for channel in channels:
    #         number_data = random.randint(10,99)
    #         redis_client.publish(channel,number_data)
    #         print(f'Published {number_data} to channel {channel}')

    #     time.sleep(1)

threds = []
for channel in channels:
    thread = threading.Thread(target=publish_random_data, args=(channel,))
    threds.append(thread)
    thread.start()




    