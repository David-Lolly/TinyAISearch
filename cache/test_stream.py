import httpx, json, asyncio
import time

async def main():
    async with httpx.AsyncClient(timeout=None) as client:
        print(f"[{0:.2f}s] 开始发送请求...")
        start_time = time.time()
        
        async with client.stream("POST", "http://localhost:5000/search",
                                 headers={"Accept":"application/x-json-stream"},
                                 json={"query":"python实现菲波那切数列","user_id":"u","use_web":False}) as r:
            print(f"[{time.time() - start_time:.2f}s] 收到响应头，开始接收数据...")
            
            line_count = 0
            async for line in r.aiter_lines():
                current_time = time.time() - start_time
                if line:
                    line_count += 1
                    if line_count <= 5 or line_count % 20 == 0:  # 只打印前5行和每20行
                        print(f"[{current_time:.2f}s] Line {line_count}: {line}")
                    elif line_count == 6:
                        print(f"[{current_time:.2f}s] ... (省略中间行，每20行显示一次)")
                    
        end = time.time()
        print(f"[{end - start_time:.2f}s] 完成，总共接收了{line_count}行数据")

asyncio.run(main())