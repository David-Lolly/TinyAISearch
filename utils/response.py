import json
from typing import List, Optional, Union, Dict, Any
from langchain_core.documents import Document
from openai import OpenAI
import logging
from datetime import date
from openai.types.chat import ChatCompletionMessageParam
from .config_manager import config

logger = logging.getLogger(__name__)

def generate(query, chat_history: Optional[List[dict]] = None):
    """
    用户的问题不需要搜索，直接调用模型回答

    param query: 用户问题
    """
    base_url = config.get("llm_base_url")
    model_name = config.get("llm_model_name")
    api_key = config.get("llm_api_key")

    if not all([base_url, model_name, api_key]):
        logger.error("LLM configuration is missing.")
        def error_stream():
            yield b"Error: LLM configuration is missing. Please configure the application."
        return error_stream()
    current_date ='当前日期：'+ date.today().strftime("%Y-%m-%d")
    prompt = """你是AI搜索助手，名字叫做TinyAISearch，由乐乐开发，{current_date}。请根据你和用户的聊天记录，以及当前用户的问题，充分理解用户意图，进行回答。"""
    system_message = {"role": "system", "content": prompt.format(current_date=current_date)}
    messages = [system_message]
    if chat_history:
        for msg in chat_history:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                messages.append({'role': msg['role'], 'content': msg['content']})
            elif isinstance(msg, str): # 兼容旧的字符串格式历史（如果存在）
                pass #  简单忽略无法处理的格式
                
    
    messages.append({"role": "user", "content": query})
    logger.info(f'response_stage_messages:{json.dumps(messages, ensure_ascii=False, indent=2)}')
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=30  
    )

    
    def stream_generate():
        try:
            logger.info("开始调用LLM API...")
            import time
            start_time = time.time()
            
            assert model_name is not None
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=True,
                temperature=0.8,
                stream_options={"include_usage": True}
            )
            
            logger.info(f"LLM API调用完成，耗时: {time.time() - start_time:.2f}秒")
            
            chunk_count = 0
            for chunk in response:
                if chunk_count == 0:
                    logger.info(f"收到第一个chunk，总耗时: {time.time() - start_time:.2f}秒")
                chunk_count += 1
                
                response_data = json.loads(chunk.model_dump_json())
                try:
                    content = response_data['choices'][0]['delta']['content']
                    if content:  # 确保内容不为空
                        yield f"{content}".encode('utf-8')  # 将内容逐块发送给客户端
                except Exception as e:
                    logger.error(f"Error extracting content from chunk: {e}")
            
            logger.info(f"流式响应完成，总共处理了{chunk_count}个chunks")
        except Exception as e:
            logger.error(f"Error: {str(e)}")

    return stream_generate()



def search_generate(query: str, search_results: Union[Dict[str, List[Dict[str, Any]]], List[Document]],search_plan_data: dict, chat_history: Optional[List[dict]] = None,debug: bool = False):
    """
    参考搜索结果回答用户问题

    param query: 用户问题
    param search_results: 召回的搜索结果
    """
    base_url = config.get("llm_base_url")
    model_name = config.get("llm_model_name")
    api_key = config.get("llm_api_key")

    if not all([base_url, model_name, api_key]):
        logger.error("LLM configuration is missing.")
        def error_stream():
            yield b"Error: LLM configuration is missing. Please configure the application."
        return error_stream()

    implicit_questions = search_plan_data.get('query_analysis', {}).get('implicit_questions', [])
    
    all_search_results = []
    if isinstance(search_results, dict):
        for results in search_results.values():
            all_search_results.extend(results)
    else:
        for item in search_results:
            if isinstance(item, Document):
                all_search_results.append({
                    'title': item.metadata.get('title', ''),
                    'content': item.page_content,
                    'link': item.metadata.get('url', '')
                })
            elif isinstance(item, dict):
                all_search_results.append(item)

    logger.info(f'retreival_context:{json.dumps(all_search_results, ensure_ascii=False, indent=2)}')
    retrieval_context = [{"Title":page.get('title', ''), "Content":page.get('content', '')[:2048]} for page in all_search_results]
    prompt = """# Role and Goal
        You are a top-tier AI Search Analyst. Your primary mission is to provide the user with a comprehensive, accurate, and critically-evaluated answer. You must synthesize and deeply analyze the provided search results, not just summarize them.
        You will be provided with the following information:
        1.  **CURRENT_DATE**: The current date,if user's question is  related to current date,you should use it.
        2.  **IMPLICIT_QUESTIONS**: The underlying, deeper questions inferred from the user's query, which reveal their true intent.
        3.  **SEARCH_RESULTS**: A list of web pages containing a `Title`, `Content`. Treat this as raw, unverified data that requires rigorous scrutiny.

        **Step 1: Deconstruct the User's Need**
        -   Thoroughly analyze the `USER_QUERY` and all `IMPLICIT_QUESTIONS`. This is the key to understanding the full scope of what the user wants to know. Your final answer must address all of these points.

        **Step 2: Critically Evaluate the Search Results**
        -   **NEVER blindly trust the search results.** Your core value lies in your ability to analyze and vet information.
        -   **Cross-Validate Information**: Compare all search sources to identify points of consensus and disagreement.
        -   **Identify Contradictions**: If different sources provide conflicting information, you MUST explicitly point out these discrepancies in your answer. If possible, offer a plausible explanation for the conflict (e.g., different timeframes, differing perspectives, or reporting errors).
        -   **Assess Information Quality**: A well-reasoned article with specific data is more credible than a simple, unsubstantiated claim. Note when a source appears to be of low quality.
        -   **Identify Information Gaps**: If the search results are incomplete or cannot fully answer the user's question, state this clearly and specify what information is missing.

        **Step 3: Synthesize a High-Value Answer**
        -   **Structure Your Answer Logically**: Begin with a direct answer, then provide a detailed explanation using headings, lists, and bold text for clarity.
        -   **Synthesize, Don't List**: Weave the validated information from multiple sources into a single, coherent, and easy-to-understand narrative. Your output should be a new piece of value-added content.
        -   **Maintain an Objective, Analytical Tone**: Clearly present facts and distinguish them from speculation or conflicting reports.
        -   Your answer must use the same language as the user's question.
        -   The final output must be a well-written, thoughtful, and comprehensive response that directly answers the user's explicit and implicit questions.
        -   The answer must be grounded in the provided search results but elevated by your critical analysis.
        -   If there is not enough information to provide a definitive answer, explain why and what information is missing.
        
        CURRENT_DATE:
        {current_date}

        IMPLICIT_QUESTIONS:
        {implicit_questions}

        SEARCH_RESULTS:
        {retrieval_context}
        
        
        
        """

    implicit_questions = json.dumps(implicit_questions, ensure_ascii=False, indent=2)
    retrieval_context = json.dumps(retrieval_context, ensure_ascii=False, indent=2)
    current_date = date.today().strftime("%Y-%m-%d")

    system_message = {"role": "system", "content": prompt.format(current_date=current_date, implicit_questions=implicit_questions, retrieval_context=retrieval_context)}
    
    
    
    messages = [system_message]
    if chat_history:
        for msg in chat_history:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                messages.append({'role': msg['role'], 'content': msg['content']})
            elif isinstance(msg, str):
                pass # 简单忽略无法处理的格式
                
    messages.append({"role": "user", "content": query})
    logger.info(f'response_stage_messages:{json.dumps(messages, ensure_ascii=False, indent=2)}')
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=60.0)
    def stream_generate():
        try:
            logger.info("开始调用LLM API (search_generate)...")
            import time
            start_time = time.time()
            
            assert model_name is not None
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=True,
                temperature=0.5,
            )
            
            logger.info(f"LLM API调用完成 (search_generate)，耗时: {time.time() - start_time:.2f}秒")
            
            chunk_count = 0
            for chunk in response:
                if chunk_count == 0:
                    logger.info(f"收到第一个chunk (search_generate)，总耗时: {time.time() - start_time:.2f}秒")
                chunk_count += 1
                
                response_data = json.loads(chunk.model_dump_json())
                try:
                    content = response_data['choices'][0]['delta']['content']

                    if content:  # 确保内容不为空
                        yield f"{content}".encode('utf-8')  # 将内容逐块发送给客户端
                except (KeyError, IndexError):
                    pass # Ignore empty delta content
                except Exception as e:
                    logger.warning(f"Error extracting content from chunk: {e}")
            
            logger.info(f"流式响应完成 (search_generate)，总共处理了{chunk_count}个chunks")
        except Exception as e:
                logger.error(f"Error: {str(e)}")

    return stream_generate()


if __name__ == "__main__":
    query = "claude 3.5 sonnet 和 3.7 sonnet 有什么区别"
    with open(r'cache\context.json', 'r', encoding='utf-8') as f:
        search_results = json.load(f)
    with open('./cache/search_plan_data.json', 'r', encoding='utf-8') as f:
        search_plan_data = json.load(f)
    result = search_generate(query, search_results=search_results, search_plan_data=search_plan_data, chat_history=[], debug=True)
    for r in result:
        print(r.decode('utf-8'))


