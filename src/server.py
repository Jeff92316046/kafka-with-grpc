import asyncio
from concurrent import futures
import grpc
import os
from typing import AsyncIterator, Dict
from generated.message_pb2 import Message,ChatRequest,Empty
from generated.message_pb2_grpc import MessageServiceServicer, add_MessageServiceServicer_to_server
from kafka import KafkaProducer, KafkaConsumer
from dotenv import load_dotenv

load_dotenv()
BOOTSTRAP_SERVER = f"{os.getenv('KAFKA_HOST', 'localhost')}:{os.getenv('KAFKA_PORT', 9092)}"


class MessageService(MessageServiceServicer):
    def __init__(self):
        self.producer = KafkaProducer(bootstrap_servers=BOOTSTRAP_SERVER)

    def ChatStream(self, request:ChatRequest, context):
        room_id = request.room_id
        topic = f"chat_room_{room_id}"

        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=BOOTSTRAP_SERVER,
            auto_offset_reset="earliest"
        )
        try:
            for msg in consumer:
                data = msg.value.decode("utf-8").split("|")
                if int(data[2]) != request.author and int(data[2]) != 0:  
                    message = Message(
                        room_id=int(data[0]),
                        message_id=int(data[1]),
                        author=int(data[2]),
                        text=data[3]
                    )
                    yield message
        finally:
            print("Closing Kafka Consumer") 
            consumer.close()

    def SendMessage(self, request:Message, context):
        topic = f"chat_room_{request.room_id}"
        message = f"{request.room_id}|{request.message_id}|{request.author}|{request.text}".encode("utf-8")
        print(message)
        self.producer.send(topic, message)
        self.producer.flush()
        
        return Empty()

def serve(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_MessageServiceServicer_to_server(MessageService(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    server.wait_for_termination()

def main():
    asyncio.run(serve(3000))

if __name__ == "__main__":
    main()
