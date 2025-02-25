import asyncio
import grpc
import os
from typing import AsyncIterator
from generated.message_pb2 import Message
from generated.message_pb2_grpc import MessageServiceServicer ,add_MessageServiceServicer_to_server
from kafka import KafkaProducer, KafkaConsumer
from dotenv import load_dotenv

load_dotenv()    
BOOTSTRAP_SERVER=f"{os.getenv('KAFKA_HOST', 'localhost')}:{os.getenv('KAFKA_PORT', 9092)}"

class MessageService(MessageServiceServicer):
    producer = KafkaProducer(bootstrap_servers=BOOTSTRAP_SERVER)
    consumer:KafkaConsumer = None
    async def chatStream(self, request_iterator:AsyncIterator[Message], context):
        user_id: str | None = None  # 用來存這個 Client 的 ID
        
        try:
            async for message in request_iterator:
                user_id = message.author
                topic = f"chat_topic_{message.room_id}"
                self.producer.send(topic, value=message.SerializeToString())
                self.producer.flush()
            
            self.consumer = KafkaConsumer(topic, bootstrap_servers=BOOTSTRAP_SERVER, auto_offset_reset="earliest")
            for msg in self.consumer:
                chat_msg = Message.FromString(msg.value)
                if chat_msg.author != user_id:
                    yield chat_msg
        
        except grpc.RpcError:
            print(f"{user_id} disconnected")
    

async def serve(port):
    server = grpc.aio.server()
    add_MessageServiceServicer_to_server(MessageService(), server)
    server.add_insecure_port(f"[::]:{port}")
    await server.start()
    await server.wait_for_termination()

def main():
    asyncio.run(serve(3000))

if __name__ == "__main__":
    main()