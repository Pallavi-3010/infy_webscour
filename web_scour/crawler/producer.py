# ============================================
# Task 6 & Task 9
# Sends seed URLs to RabbitMQ queue
# ============================================

import pika    #communicate with RabbitMQ

# -----------------------------
# CONNECT TO RABBITMQ
# -----------------------------
#Creates a synchronous (blocking) connection to RabbitMQ
#localhost means: RabbitMQ server is running on the same machine and The program waits until connection is established

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)
channel = connection.channel()  #Opens a channel inside the RabbitMQ connection

# Create queue (shared by all workers)
channel.queue_declare(queue='url_queue', durable=True)


seed_url = input("Enter seed URL: ").strip()

# Send seed URL to queue
#Publishes a message into RabbitMQ
#Enables communication between Producer and Workers
channel.basic_publish(   
    exchange='',
    routing_key='url_queue', #Message is delivered to: url_queue
    body=seed_url
)

print(f"[Producer] Seed URL sent: {seed_url}")

connection.close()

print("[Producer] Finished")
