import json
import os
from typing import List, Dict
import requests
from .keywords_extract import keywords_extract  # 远程关键字提取函数
from baidusearch.baidusearch import search  # 百度搜索功能库
import logging

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

class Search:
    """
    Search 类：实现 Google、Serper 和百度搜索引擎的支持。
    包括关键字提取、搜索和搜索结果格式化功能。
    """

    def __init__(self):
        """
        初始化 Search 类，加载配置文件，并设置搜索引擎相关参数。
        """
        print(os.getcwd())  # 打印当前工作目录，便于调试
        with open(r'./config/config.json', encoding='utf-8') as f:
            config = json.load(f)

        # 从配置文件中加载 API 密钥、CSE 标识符和搜索引擎名称
        self.api = config['search_engine']['api_key']
        self.cse = config['search_engine']['cse']  # 仅用于 Google 搜索引擎
        self.search_engine = config['search_engine']['name']  # 搜索引擎名称
        print(f'-----{self.search_engine}-------')  # 打印当前搜索引擎名称

    def google_search(self, question: str) ->tuple:
        """
        使用 Google 自定义搜索 API 进行搜索。

        Args:
            question (str): 用户输入的问题。

        Returns:
            tuple: 包含格式化的搜索结果、提取的关键字权重以及查询关键字。
        """
        # 提取关键字
        queries = keywords_extract(question)  # 使用云端大模型关键字提取

        # 如果需要搜索
        if queries:
            if len(queries) == 2:
                query = queries[0]  # 提取的查询关键字
                grade = queries[1]  # 问题难度等级
                print(f'key_words:{query}, degree:{grade}')

                # 设置 Google 搜索 API 的请求参数
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    "q": query,
                    "key": self.api,
                    "cx": self.cse
                }
                response = requests.get(url, params=params)  # 发送 GET 请求
                data = self.format_data_google(response.json())  # 格式化搜索结果
                return data, int(grade), query
            else:
                logger.error('keywords extract error')  # 打印关键字提取错误信息
        return (0,) * 3  # 不需要搜索

    def serper_search(self, question: str) -> tuple:
        """
        使用 Serper.dev 搜索 API 进行搜索。

        Args:
            question (str): 用户输入的问题。

        Returns:
            tuple: 包含格式化的搜索结果、提取的关键字权重以及查询关键字。
        """
        # 提取关键字
        queries = keywords_extract(question)

        if queries:
            if len(queries) == 2:
                query = queries[0]  # 查询关键字
                grade = int(queries[1])  # 问题难度等级
                print(f'key_words:{query}, degree:{grade}')

                # 设置 Serper 搜索 API 的请求参数
                url = "https://google.serper.dev/search"
                payload = json.dumps({"q": query})
                headers = {
                    'X-API-KEY': self.api,
                    'Content-Type': 'application/json'
                }

                response = requests.request("POST", url, headers=headers, data=payload).json()
                data = self.format_data_serper(response)  # 格式化搜索结果
                return data, int(grade), query
            else:
                logger.error('keywords extract error')  # 打印关键字提取错误信息
        return (0,) * 3

    def baidu_search(self, question: str) -> tuple:
        """
        使用百度搜索引擎进行搜索。

        Args:
            question (str): 用户输入的问题。

        Returns:
            tuple: 包含格式化的搜索结果、提取的关键字权重以及查询关键字。
        """
        # 提取关键字
        queries = keywords_extract(question)

        if queries:
            if len(queries) == 2:
                query = queries[0]  # 查询关键字
                grade = queries[1]  # 问题难度等级
                print(f'key_words:{query}, degree:{grade}')

                # 使用百度搜索库进行搜索
                results = search(query)
                data = self.format_data_baidu(results)  # 格式化搜索结果
                return data, int(grade), query
            else:
                logger.error('keywords extract error')  # 打印关键字提取错误信息
        return (0,) * 3

    def user_defined(self,question :str):
        """
        用户自定义搜索引擎进行搜索。

            Args:
                question (str): 用户输入的问题。

            Returns:
                tuple: 包含格式化的搜索结果、提取的关键字权重以及查询关键字。
        """
        pass

    def format_data_google(self, result: Dict) -> List[Dict]:
        """
        格式化 Google 搜索 API 返回的结果。

        Args:
            result (dict): Google 搜索 API 的响应数据。

        Returns:
            list: 包含格式化的搜索结果，每个结果包含 ID、标题和链接。
        """
        data = []
        for i, item in enumerate(result['items']):
            data.append({
                'id': i,  # 唯一标识符
                "title": item['title'],  # 搜索结果标题
                "link": item['link']  # 搜索结果链接
            })
        return data

    def format_data_serper(self, result: Dict) -> List[Dict]:
        """
        格式化 Serper.dev 搜索 API 返回的结果。

        Args:
            result (dict): Serper 搜索 API 的响应数据。

        Returns:
            list: 包含格式化的搜索结果，每个结果包含 ID、标题和链接。
        """
        data = []
        i, j, k = 0, 0, 0

        # 处理 organic 搜索结果
        for i, item in enumerate(result.get('organic', [])):
            data.append({
                'id': i,
                "title": item['title'],
                "link": item['link']
            })

        # 处理 "people also ask" 结果
        for j, item in enumerate(result.get('peopleAlsoAsk', [])):
            data.append({
                'id': i + j + 1,
                "title": item['title'],
                "link": item['link']
            })

        # 处理相关搜索结果
        for k, item in enumerate(result.get('relatedSearches', [])):
            data.append({
                'id': i + j + k + 1,
                "title": item['title'],
                "link": item['link']
            })
        return data

    def format_data_baidu(self, result: List[Dict]) -> List[Dict]:
        """
        格式化百度搜索返回的结果。

        Args:
            result (list): 百度搜索的原始返回数据，列表形式。

        Returns:
            list: 包含格式化的搜索结果，每个结果包含 ID、标题和链接。
        """
        data = []
        for i, item in enumerate(result):
            data.append({
                'id': i,
                "title": item['title'],  # 搜索结果标题
                "link": item['url']  # 搜索结果链接
            })
        return data

    def format_data_user_defined(self):
        pass

    def search(self, query: str) -> tuple:
        """
        根据配置文件中选择的搜索引擎执行搜索。

        Args:
            query (str): 用户输入的问题。

        Returns:
            tuple: 包含格式化的搜索结果、提取的关键字权重以及查询关键字。
        """
        try:
            # 根据配置选择搜索引擎
            if self.search_engine == 'google':
                return self.google_search(query)
            elif self.search_engine == 'serper':
                return self.serper_search(query)
            elif self.search_engine == 'baidu':
                return self.baidu_search(query)
            else:
                # 自定义搜索引擎
                return self.user_defined(query)
        except Exception as e:
            print('Please modify your config to choose a supported search engine.')
            print(f'Error: {e}')
