import asyncio
from concurrent import futures
import grpc
import os
from typing import AsyncIterator, Dict
from generated.message_pb2 import Message
from generated.message_pb2_grpc import MessageServiceServicer, add_MessageServiceServicer_to_server
from kafka import KafkaProducer, KafkaConsumer
from dotenv import load_dotenv

load_dotenv()
BOOTSTRAP_SERVER = f"{os.getenv('KAFKA_HOST', 'localhost')}:{os.getenv('KAFKA_PORT', 9092)}"


class MessageService(MessageServiceServicer):
    producer = KafkaProducer(bootstrap_servers=BOOTSTRAP_SERVER)
    consumers: Dict[str, KafkaConsumer] = {}

    def create_consumer(self, topic: str) -> KafkaConsumer:
        """Create a new consumer for a specific topic."""
        return KafkaConsumer(
            topic,
            bootstrap_servers=BOOTSTRAP_SERVER,
            auto_offset_reset="latest",
            enable_auto_commit=True,
        )

    def ChatStream(self, request_iterator: AsyncIterator[Message], context):
        user_id: int | None = None
        topic :str | None = None
        try:
            for message in request_iterator:
                user_id = message.author
                topic = f"chat_topic_{message.room_id}"

                if topic not in self.consumers:
                  self.consumers[topic] = self.create_consumer(topic)

                self.producer.send(topic, value=message.SerializeToString())
                # self.producer.flush() # You may remove this line, if it is not necessary.

                if topic:
                    for msg in self.consumers[topic]:
                        print(f"Received message from {msg.topic}")
                        chat_msg = Message.FromString(msg.value)
                        if chat_msg.author != user_id:
                            yield chat_msg

        except grpc.RpcError:
            if user_id:
              print(f"{user_id} disconnected")
            # Clean up the consumer on disconnect
            if topic and topic in self.consumers:
                self.consumers[topic].close()
                del self.consumers[topic]

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
