import json
from typing import List

from openai import OpenAI
import logging
from datetime import date

# 配置logger
logging.basicConfig(
    level=logging.ERROR,  # 记录所有级别的日志
    format="%(asctime)s - %(levelname)s - %(message)s",  # 日志格式
    handlers=[
        logging.StreamHandler()  # 输出到控制台
    ]
)

# 获取logger对象
logger = logging.getLogger()



def keywords_extract(query: str) -> List[str]:
    # 根据用户的问题提取出适合搜索的关键词

    # 加载配置文件
    with open(r'./config/config.json',encoding='utf-8') as f:
        config = json.load(f)

    base_url = config["LLM"]['base_url']
    model_name = config["LLM"]["model_name"]
    api_key = config["LLM"]["api_key"]

    print(model_name,api_key,base_url)
    prompt_zh = """你是一个专门生成最佳搜索查询并判断是否需要搜索的AI。请遵循以下指导原则：
            1、分析问题以确定是否需要进行外部搜索。
            2、用户的问题默认是需要搜索的，如果问题涉及直接回答、直接告诉我等强制要求，或该问题可以不依赖外部信息回答,回复“NO_SEARCH_NEEDED”。
            3、对于你无法回答需要搜索的问题： 
                a. 基于问题提取2-5个关键搜索词或短语，请不要在关键词中包含任何问题的答案或解释，仅提供关键词。 
                b. 考虑同义词和相关概念来扩展搜索范围，确保关键词覆盖问题的核心和潜在的相关领域。 
                c. 优先选择具体且独特的词汇，而不是一般性词汇，并对关键词的重要性进行排序，确保核心关键词优先。 
                d. 以JSON数组的格式返回搜索关键词，生成的关键词放在同一个字符串内并使用空格隔开。 
                e. 生成的关键词应该按相关性进行排序，最重要的关键词放在前面，以确保搜索引擎能够优先匹配最相关的结果。
                f. 请你根据用户的问题来判断该问题的难度，难度等级1~2(难度等级说明：1表示简单直接且具体的问题，只需查找简单的事实即可回答;2表示一般需要一定的专业知识来解释，涉及多个步骤和概念，需要复杂的推理和预测)，难度等级放在字符串内，用逗号和前面的搜索关键词隔开。
                g. 用户问题中会包含当前日期信息，请你根据用户的问题判断是否需要再搜索关键词中加入日期信息

            示例：
                例如“你能做什么？当前日期：2024-12-15”，“请直接告诉我某行业的情况”等直接询问你能力的问题，回复“NO_SEARCH_NEEDED”。
                例如“蔡徐坤是谁？当前日期：2024-11-15”，回复 [ "蔡徐坤 个人介绍","1"]。
                例如“最近发生了什么大事？当前日期：2024-12-12”，回复 [ "2024年12月国际形势 重大新闻 政治形势 经济状况","1"]。
                例如“光合作用如何在植物中工作？当前日期：2024-12-11”，回复 [ "植物 光合作用原理","2"]。
                例如“量子计算对网络安全的影响是什么，它将如何改变未来十年的加密格局？当前日期：2024-12-18”，回复 [ "量子计算 网络安全 量子计算对网络安全的影响 量子计算如何改变未来十年的加密格局","2"]。
            记住，你的目标是仔细识别用户的问题是否需要搜索，对于需要搜索的问题按照示例的格式回复，不需要搜索的问题回复“NO_SEARCH_NEEDED”，不要回复任何其他内容。
            """
    # 把当前日期加入到用户问题中，以便模型判断是否需要在搜索关键词中加入日期信息
    current_date ='当前日期：'+ date.today().strftime("%Y-%m-%d")
    message = [{"role": 'system', "content": prompt_zh},
               {"role": "user", "content": query+current_date}]


    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=message,
            temperature=0.2
        )

        # 从响应中提取文本
        response = json.loads(completion.model_dump_json())
        result = response['choices'][0]['message']['content']

        if 'NO_SEARCH_NEEDED' in result:
            return None
        try:
            queries = json.loads(result)
            if isinstance(queries, list) and queries:
                return queries
            else:
                logger.error(f"Unexpected response format: {queries}")
        except json.JSONDecodeError:
            logger.error(f"Error parsing response: {result}")
    except Exception as e:
        logger.error(f"Error: {str(e)}")


