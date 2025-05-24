import asyncio
import websockets
import json

async def chat():
    uri = "ws://localhost:5000/api/chats/ws/1"
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNzQ3ODE2MjY3fQ.i72wXcv7sY6kSqFdv4llI7koFwauq6bShS_3qIUhMcg"
    }
    async with websockets.connect(uri, extra_headers=headers) as websocket:
        # ارسال پیام
        message = {
            "message": "سلام، لطفاً درباره خدمات مهاجرت به کانادا توضیح دهید."
        }
        await websocket.send(json.dumps(message))
        
        # دریافت پاسخ
        response = await websocket.recv()
        print("پاسخ:", json.loads(response))

asyncio.run(chat()) 