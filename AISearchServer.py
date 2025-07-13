import logging
import os
import json
import asyncio
from typing import List, Optional
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler

from langchain_core.documents import Document

dir_path = './logs'
file_name = 'app.log'
file_path = os.path.join(dir_path, file_name)
if not os.path.exists(dir_path):
    os.makedirs(dir_path)
if not os.path.exists(file_path):
    with open(file_path, 'w') as f:
        f.write('')
logging.basicConfig(
    format='%(levelname)s (%(asctime)s): %(message)s (Line: %(lineno)d [%(filename)s])',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='./logs/app.log',
    encoding='utf-8',
    filemode='a',
    level=logging.WARNING
)

logger = logging.getLogger(__name__)

from fastapi import FastAPI, Request, Body, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from utils.search_web import Search
from utils.crawl_web import Crawl
from utils.pages_retrieve import Retrieval_v2
from utils.response import generate, search_generate
from utils.retrieval import Retrieval_v1
from utils.config_manager import config
import utils.database as db
from openai import OpenAI, AsyncOpenAI
import httpx

@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    db.create_tables()
    logger.info("数据库表已检查/创建完成。")
    yield
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class SearchRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    user_id: str
    use_web: bool = True

class SessionRequest(BaseModel):
    user_id: str
    title: Optional[str] = None

class LoginRequest(BaseModel):
    user_id: str
    password: str

class RegisterRequest(BaseModel):
    user_id: str
    password: str

class TestRequest(BaseModel):
    model_name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    cse_id: Optional[str] = None
async def stream_json(data_type: str, content: any):
    message = {
        "type": data_type,
        "payload": content
    }
    return json.dumps(message, ensure_ascii=False) + '\n'

def get_and_clean_history(session_id: str) -> List[dict]:
    history_messages = db.get_messages(session_id)
    cleaned_history = []
    for msg in history_messages:
        if msg.get('role') == 'assistant':
            try:
                content_data = json.loads(msg['content'])
                cleaned_msg = {'role': 'assistant', 'content': content_data.get('text', '')}
                cleaned_history.append(cleaned_msg)
            except (json.JSONDecodeError, TypeError):
                cleaned_history.append(msg)
        else:
            cleaned_history.append(msg)
    return cleaned_history[:-1] if cleaned_history else []

@app.get("/api/status")
async def get_status():
    is_configured = config.is_configured()
    return {"configured": is_configured}

@app.get("/api/settings")
async def get_settings_api():
    return config.get_all()

@app.post("/api/settings")
async def save_settings_api(payload: dict):
    settings_data = payload.get("settings", {})
    if not settings_data:
        return {"status": "error", "message": "未提供设置数据。"}
    db.save_settings(settings_data)
    config.load_config() # Reload config in the manager
    return {"status": "success", "message": "设置保存成功。"}

@app.post("/api/test/llm")
async def test_llm_connection(req: TestRequest):
    if not req.api_key or not req.base_url or not req.model_name:
        return {"success": False, "message": "LLM配置不完整"}
    client = AsyncOpenAI(api_key=req.api_key, base_url=req.base_url)
    try:
        await client.chat.completions.create(
            model=req.model_name,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=2
        )
        return {"success": True, "message": "LLM连接成功"}
    except Exception as e:
        logger.error(f"LLM连接测试失败: {e}")
        return {"success": False, "message": f"连接失败: {str(e)}"}

@app.post("/api/test/embedding")
async def test_embedding_connection(req: TestRequest):
    if not req.api_key or not req.base_url or not req.model_name:
        return {"success": False, "message": "Embedding模型配置不完整"}
    payload = {
        "model": req.model_name,
        "input": ["test"],
        "encoding_format": "float"
    }
    headers = {
        "Authorization": f"Bearer {req.api_key}",
        "Content-Type": "application/json"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(req.base_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            if "data" in data:
                return {"success": True, "message": "Embedding模型连接成功"}
            else:
                return {"success": False, "message": f"API响应异常: {data}"}
    except Exception as e:
        logger.error(f"Embedding连接测试失败: {e}")
        return {"success": False, "message": f"连接失败: {str(e)}"}

@app.post("/api/test/rerank")
async def test_rerank_connection(req: TestRequest):
    if not req.base_url or not req.api_key or not req.model_name:
        return {"success": False, "message": "Rerank模型配置不完整"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                req.base_url,
                headers={"Authorization": f"Bearer {req.api_key}"},
                json={
                    "model": req.model_name,
                    "query": "test",
                    "documents": ["test1", "test2"]
                }
            )
            response.raise_for_status()
        return {"success": True, "message": "Rerank模型连接成功"}
    except Exception as e:
        logger.error(f"Rerank连接测试失败: {e}")
        return {"success": False, "message": f"连接失败: {str(e)}"}

@app.post("/api/test/google")
async def test_google_connection(req: TestRequest):
    if not req.api_key or not req.cse_id:
        return {"success": False, "message": "API Key和CSE ID不能为空"}
    try:
        search_instance = Search()
        await search_instance.google_search("test", api_key=req.api_key, cse_id=req.cse_id)
        return {"success": True, "message": "Google Search连接成功"}
    except Exception as e:
        logger.error(f"Google Search连接测试失败: {e}")
        return {"success": False, "message": f"连接失败: {str(e)}"}

@app.post("/search")
async def search(req: SearchRequest):
    if not config.is_configured():
        async def not_configured_stream():
             yield await stream_json("error", "系统未配置。请先访问配置页面完成设置。")
        return StreamingResponse(not_configured_stream(), media_type="application/x-json-stream")

    session_id = req.session_id
    if not session_id:
        session_id = db.create_session(user_id=req.user_id, title=req.query[:50])
        if not session_id:
            logger.error("创建新会话失败")
            return await stream_json("error", "创建新会话失败")

    db.add_message(session_id, 'user', req.query)
    logger.info(f"用户消息已添加至会话 {session_id}")
    processed_history = get_and_clean_history(session_id)
    logger.info(f"处理后的历史记录: {processed_history}")

    async def process_request():
        assistant_response_text = ""
        try:
            if not req.use_web:
                response_generator = generate(req.query, chat_history=processed_history)
                if response_generator:
                    for chunk in response_generator:
                        chunk_str = chunk.decode('utf-8', errors='ignore')
                        assistant_response_text += chunk_str
                        yield await stream_json("answer_chunk", chunk_str)
                
                final_db_content = {"text": assistant_response_text, "references": []}
                db.add_message(session_id, 'assistant', json.dumps(final_db_content, ensure_ascii=False))
                return
            logger.info("准备搜索....")
            yield await stream_json("process", "正在分析问题...")
            
            search_instance = Search()
            search_plan_data, search_results = await search_instance.search(req.query, chat_history=processed_history)
            
            print(f"search_plan_data:{search_plan_data}")
            if not search_plan_data:
                yield await stream_json("process", "该问题不需要搜索，直接回答...")
                response_generator = generate(req.query, chat_history=processed_history)
                if response_generator:
                    for chunk in response_generator:
                        chunk_str = chunk.decode('utf-8', errors='ignore')
                        assistant_response_text += chunk_str
                        yield await stream_json("answer_chunk", chunk_str)
                final_db_content = {"text": assistant_response_text, "references": []}
                db.add_message(session_id, 'assistant', json.dumps(final_db_content, ensure_ascii=False))
                return

            plan = search_plan_data.get('search_plan', {})
            foundational_queries = plan.get('foundational_queries', [])
            expansion_queries = plan.get('expansion_deep_dive_queries', [])

            if not (foundational_queries or expansion_queries):
                yield await stream_json("process", "该问题不需要搜索，直接回答...")
                response_generator = generate(req.query, chat_history=processed_history)
                if response_generator:
                    for chunk in response_generator:
                        chunk_str = chunk.decode('utf-8', errors='ignore')
                        assistant_response_text += chunk_str
                        yield await stream_json("answer_chunk", chunk_str)
                final_db_content = {"text": assistant_response_text, "references": []}
                db.add_message(session_id, 'assistant', json.dumps(final_db_content, ensure_ascii=False))
                return

            key_entities = search_plan_data.get('query_analysis', {}).get('key_entities', [])
            yield await stream_json("process", f"搜索关键词: {key_entities}")

            crawler = Crawl()
            web_pages = crawler.crawl(search_results)
            crawler.close()

            yield await stream_json("process", f"搜索完成. 找到 {sum(len(v) for v in web_pages.values())} 个网页.")

            retrieval_vertion = config.get("retrieval_version", "v2") # Read from config
            logger.info(f"检索版本: {retrieval_vertion}")
            if retrieval_vertion == "v2":
                retrieval_v2 = Retrieval_v2()
                context = retrieval_v2.retrieve(search_plan_data, web_pages)
            else:
                retrieval_v1 = Retrieval_v1()
                all_web_pages = [page for pages in web_pages.values() for page in pages]
                context = retrieval_v1.retrieve(queries=[req.query],search_plan_data=search_plan_data, web_pages=all_web_pages)
            

            response_generator = search_generate(req.query, context, search_plan_data, chat_history=processed_history)
            if response_generator:
                for chunk in response_generator:
                    if isinstance(chunk, bytes):
                        chunk_str = chunk.decode('utf-8', errors='ignore')
                    else:
                        chunk_str = str(chunk) # Handle non-byte chunks
                    assistant_response_text += chunk_str
                    yield await stream_json("answer_chunk", chunk_str)
            all_pages = []
            if isinstance(context, dict):
                for results in context.values():
                    all_pages.extend(results)
            else:
                for item in context:
                    if isinstance(item, Document):
                        all_pages.append({
                            'title': item.metadata.get('title', ''),
                            'link': item.metadata.get('url', '')
                        })
                    elif isinstance(item, dict):
                        all_pages.append(item)
            unique_refs = {
                (page.get('title'), page.get('link')): {page.get('title'): page.get('link')}
                for page in all_pages if page.get('title') and page.get('link')
            }
            references = list(unique_refs.values())
            logger.info(f"参考来源: {references}")
            if references:
                yield await stream_json("reference", references)
            
            final_db_content = {"text": assistant_response_text, "references": references}
            db.add_message(session_id, 'assistant', json.dumps(final_db_content, ensure_ascii=False))
            logger.info(f"助手回复及参考来源已添加至会话 {session_id}")

        except Exception as e:
            logger.error(f"搜索处理过程中出错: {e}", exc_info=True)
            yield await stream_json("error", f"发生错误: {e}")

    return StreamingResponse(process_request(), media_type="application/x-json-stream")


@app.get("/sessions")
async def get_all_sessions(user_id: str):
    sessions = db.get_sessions(user_id)
    return sessions


@app.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    messages = db.get_messages(session_id)
    return messages


@app.post("/session", status_code=201)
async def create_new_session_endpoint(req: SessionRequest):
    import time
    title = req.title if req.title else f"Chat {time.strftime('%Y-%m-%d %H:%M')}"
    session_id = db.create_session(user_id=req.user_id, title=title)
    if session_id:
        return {'session_id': session_id, 'title': title}
    return {"error": "创建会话失败"}


@app.post("/login")
async def login(req: LoginRequest):
    if not req.user_id or not req.password:
        logger.error(f"登录尝试失败: 缺少用户ID或密码")
        raise HTTPException(status_code=400, detail="用户ID和密码为必填项")
    
    logger.info(f"用户登录尝试: {req.user_id}")
    
    # 验证用户是否存在并密码是否匹配
    is_valid = db.verify_user(req.user_id, req.password)
    
    if not is_valid:
        logger.warning(f"用户登录失败: {req.user_id}")
        raise HTTPException(status_code=401, detail="无效的凭据或用户不存在")
    
    logger.info(f"用户登录成功: {req.user_id}")
    return {"message": "登录成功", "user_id": req.user_id}

@app.post("/register")
async def register(req: RegisterRequest):
    if not req.user_id or not req.password:
        logger.error("注册尝试失败: 缺少用户ID或密码")
        raise HTTPException(status_code=400, detail="用户ID和密码为必填项")
    
    logger.info(f"用户注册尝试: {req.user_id}")
    
    # 检查用户是否已存在
    user_exists = db.user_exists(req.user_id)
    if user_exists:
        logger.warning(f"注册失败: 用户已存在: {req.user_id}")
        raise HTTPException(status_code=409, detail="用户已存在")
    
    # 注册新用户
    success = db.register_user(req.user_id, req.password)
    if not success:
        logger.error(f"注册用户失败: {req.user_id}")
        raise HTTPException(status_code=500, detail="注册用户失败")
    
    logger.info(f"用户注册成功: {req.user_id}")
    return {"message": "注册成功", "user_id": req.user_id}


if __name__ == '__main__':
    uvicorn.run("AISearchServer:app", host='localhost', port=5000, reload=True) 