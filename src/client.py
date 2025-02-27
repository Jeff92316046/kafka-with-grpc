import asyncio
import threading
import grpc
from generated.message_pb2 import Message
from generated.message_pb2_grpc import MessageServiceStub
from google.protobuf.timestamp_pb2 import Timestamp

def receive_messages(stub:MessageServiceStub,user_id:int):
    """ 持續接收 server 訊息 """
    request_messages = []
    for response in stub.ChatStream(iter(request_messages)):
        if response.author != user_id:
            print(f"\n[{response.author}]: {response.text}\n> ", end="")

async def chat_client(user_id: int, room_id: int):
    # Correct the port here:
    channel = grpc.insecure_channel("localhost:3000")
    stub = MessageServiceStub(channel)
    threading.Thread(target=receive_messages, args=(stub,user_id), daemon=True).start()

    while True:
        message = input("> ")
        if message.lower() == "exit":
            break
        try:
            stub.ChatStream(iter([Message(room_id=room_id,author=user_id, text=message)]))
        except Exception as e:
            print(e)

if __name__ == "__main__":
    user_id = int(input("輸入你的 User ID: "))
    room_id = int(input("輸入房間 ID: "))
    asyncio.run(chat_client(user_id, room_id))
