import asyncio
import threading
import grpc
from generated.message_pb2 import Message,ChatRequest
from generated.message_pb2_grpc import MessageServiceStub
from google.protobuf.timestamp_pb2 import Timestamp
async def send_message(stub:MessageServiceStub, room_id, author):
    message_id = 0
    while True:
        text = await asyncio.to_thread(input, ">")
        if text.lower() == "/exit":
            break
        message_id += 1
        request = Message(
            room_id=room_id,
            message_id=message_id,
            author=author,
            text=text
        )
        await stub.SendMessage(request)

async def chat_stream(stub:MessageServiceStub, room_id,author):
    request = ChatRequest(room_id=room_id,author=author)
    async for message in stub.ChatStream(request):
        if message.author != author:
            print(f"\r{message.author}: {message.text}",end='\n')

async def main():
    async with grpc.aio.insecure_channel("localhost:3000") as channel:
        stub = MessageServiceStub(channel)

        room_id = int(input("Enter room ID: "))
        author = int(input("Enter your user ID: "))

        recv_task = asyncio.create_task(chat_stream(stub, room_id,author))
        send_task = asyncio.create_task(send_message(stub, room_id, author))

        await asyncio.gather(recv_task, send_task)

if __name__ == "__main__":
    asyncio.run(main())
