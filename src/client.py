import asyncio
import grpc
from generated.message_pb2 import Message
from generated.message_pb2_grpc import MessageServiceStub
from google.protobuf.timestamp_pb2 import Timestamp

async def send_messages(user_id: str, room_id: str):
    while True:
        text = await asyncio.to_thread(input, "輸入訊息: ")  # 讓 `input()` 在非同步環境執行
        if text.lower() == "exit":
            return
        message = Message(
            room_id=room_id,
            author=user_id,
            text=text,
            created_at=Timestamp()
        )
        yield message

async def chat_client(user_id: str, room_id: str):
    async with grpc.aio.insecure_channel("localhost:3000") as channel:
        stub = MessageServiceStub(channel)
        try:
            async for response in stub.chatStream(send_messages(user_id, room_id)):
                print(f"from {response.author}: {response.text}")
        except grpc.RpcError as e:
            print(f"gRPC 連線中斷: {e}")

if __name__ == "__main__":
    user_id = input("輸入你的 User ID: ")
    room_id = input("輸入房間 ID: ")
    asyncio.run(chat_client(user_id, room_id))
