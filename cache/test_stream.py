import httpx, json, asyncio

async def main():
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", "http://localhost:5000/search",
                                 headers={"Accept":"application/x-json-stream"},
                                 json={"query":"test","user_id":"u","use_web":False}) as r:
            async for line in r.aiter_lines():
                if line:
                    print("LINE:", line)

asyncio.run(main())