import asyncio
from api.index import chat, ChatRequest

async def main():
    payload = ChatRequest(message="Classify this text: I love the new camera quality, but the battery drains quickly.")
    resp = await chat(payload)
    print(f"event_count={resp.event_count}, app_name={resp.app_name}")
    print((resp.response or "")[:300])

asyncio.run(main())
