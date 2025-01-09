import json
from typing import List
from langchain_core.documents import Document
from openai import OpenAI
import logging

# 配置logger
logging.basicConfig(
    level=logging.ERROR,  # 记录错误日志
    format="%(asctime)s - %(levelname)s - %(message)s",  # 日志格式
    handlers=[
        logging.StreamHandler()  # 输出到控制台
    ]
)

# 获取logger对象
logger = logging.getLogger()

def generate(query):
    """
    用户的问题不需要搜索，直接调用模型回答

    param query: 用户问题
    """
    # 加载配置文件
    logger.info("开始加载配置文件")
    with open(r'./config/config.json',encoding='utf-8') as f:
        config = json.load(f)

    base_url = config["LLM"]['base_url']
    model_name = config["LLM"]["model_name"]
    api_key = config["LLM"]["api_key"]
    debug = config['debug']['value']

    messages = [
        {"role": "system", "content": '你是AI搜索助手，名字叫做TinyAISearch，由乐乐开发，请根据用户的问题进行回答。'},
        {"role": "user","content": query}
    ]

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    # !!! debug用于在本地IDE调试代码时使用，你可以在运行后看到输出，如果代码调试完成想在前端页面查看效果，请在配置文件中将debug设置为false
    if debug:
        print('debug mode on!')
        try:
            responses = client.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=True,
                stream_options={"include_usage": True}
            )
            for response in responses:
                response = json.loads(response.model_dump_json())
                try:
                    output = response['choices'][0]['delta']['content']
                    if '\n' in output:
                        print(output, end='')
                        continue
                    print(output, end='')
                except Exception as e:
                    logger.error(f"Error processing response: {e}")
            # yield "Error:please modify the debug value"
        except Exception as e:
            logger.error(f"Error: {str(e)}")
    else:
        print('debug mode off')
        def stream_generate():
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    stream=True,
                    stream_options={"include_usage": True}
                )
                for chunk in response:
                    response = json.loads(chunk.model_dump_json())
                    try:
                        content = response['choices'][0]['delta']['content']
                        if content:  # 确保内容不为空
                            yield f"{content}".encode('utf-8')  # 将内容逐块发送给客户端
                    except Exception as e:
                        logger.error(f"Error extracting content from chunk: {e}")
            except Exception as e:
                logger.error(f"Error: {str(e)}")

        return stream_generate()



def search_generate(query: str, search_results: List[Document]):
    """
    参考搜索结果回答用户问题

    param query: 用户问题
    param search_results: 召回的搜索结果
    """

    # 加载配置文件
    with open(r'./config/config.json', encoding='utf-8') as f:
        config = json.load(f)

    base_url = config["LLM"]['base_url']
    model_name = config["LLM"]["model_name"]
    api_key = config["LLM"]["api_key"]
    debug = config['debug']['value']

    # 将搜索结果中的文本内容和标题提取出来，作为外部知识输入大模型
    search_content = [{"搜索结果": doc.page_content, "标题": doc.metadata['title']} for doc in search_results]
    # 将搜索结果的标题和链接提取出来，作为参考信息
    content_info = [{doc.metadata['title']:doc.metadata['url'] for doc in search_results}]
    # print(f'content_info:{content_info}')
    # print(f'search results:{search_content}')

    # 系统提示词
    prompt = """你是一个专业的AI助手，专注于根据搜索结果提供高质量、精准的信息回复。
        1、信息处理原则
            • 仔细理解用户问题及上下文需求。
            • 阅读并分析搜索结果，确保回答准确、相关且深入。
            • 保持中立、客观，避免主观判断或误导性陈述。
            
        2、搜索结果处理策略
            • 优先级判断：排名靠前的搜索结果通常更具参考价值，但仍需综合多方信息验证其可靠性。
            • 信息整合：结合多个搜索结果，形成全面、结构化的回答。
            • 矛盾分析：当搜索结果互相矛盾时，指出分歧并尝试提供可能的原因或背景解释。
            • 局限性提示：若信息不完整或含糊，明确告知用户并提出可能的改进建议。
            
        3、回答质量要求
            • 使用清晰、简洁的语言表达复杂信息。
            • 根据需要使用段落、列表或小标题，提升可读性。
            • 补充相关背景信息，帮助用户更好地理解上下文。
            
        你的核心目标是通过有效利用搜索结果，为用户提供高价值、经过深思熟虑的回答。优先确保内容的全面性、清晰性和可靠性，同时注重用户体验和实际问题的解决。"""

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user",
         "content": f"问题：{query}\n\n搜索结果：{json.dumps(search_content, ensure_ascii=False, indent=2)}"}
    ]

    client = OpenAI(api_key=api_key, base_url=base_url)

    # debug用于在本地IDE调试代码时使用，你可以在运行后看到输出，如果代码调试完成想在前端页面查看效果，请在配置文件中将debug设置为false
    if debug:
        try:
            responses = client.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=True,
                stream_options={"include_usage": True}
            )
            for response in responses:
                response = json.loads(response.model_dump_json())
                try:
                    output = response['choices'][0]['delta']['content']
                    if '\n' in output:
                        print(output, end='')
                        continue
                    print(output, end='')
                except Exception as e:
                    logger.warning(f"Error processing response: {e}")
        except Exception as e:
            logger.error(f"Error: {str(e)}")
    else:
        # 流式响应，实现打字机显示效果
        def stream_generate():
            try:
                yield f"参考信息：{json.dumps(content_info)}"
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    stream=True,
                    stream_options={"include_usage": True}
                )
                for chunk in response:
                    response = json.loads(chunk.model_dump_json())
                    try:
                        content = response['choices'][0]['delta']['content']

                        if content:  # 确保内容不为空
                            yield f"{content}".encode('utf-8')  # 将内容逐块发送给客户端
                    except Exception as e:
                        logger.warning(f"Error extracting content from chunk: {e}")
            except Exception as e:
                 logger.error(f"Error: {str(e)}")

        return stream_generate()




