import asyncio
from typing import List, Dict, Any, Optional
import requests
import random
from baidusearch.baidusearch import search as baidu_search
from duckduckgo_search import DDGS
from .keywords_extract import keywords_extract
import json
import time
import logging
from .config_manager import config

logger = logging.getLogger(__name__)

class Search:
    def __init__(self):
        """
        初始化Search类,从ConfigManager加载Google搜索所需的配置。
        """
        self.google_api_key = config.get('google_api_key')
        self.google_cse_id = config.get('google_cse_id')
        self.google_enabled = str(config.get('google_search_enabled', 'false')).lower() == 'true'

        if not self.google_api_key or not self.google_cse_id or not self.google_enabled:
            logger.warning("Google Search is not configured or enabled. Google fallback/search will not work.")
            self.google_enabled = False # Ensure it's false if keys are missing

    async def search_baidu(self, query: str) -> List[Dict[str, str]]:
        """使用 asyncio.to_thread 异步执行同步的百度搜索"""
        def _search():
            try:
                search_results = baidu_search(query) or []
                return [
                    {'id': i, "title": item.get('title'), "link": item.get('url')}
                    for i, item in enumerate(search_results)
                ]
            except Exception as e:
                print(f"Baidu搜索 '{query}' 时出错: {e}")
                if self.google_enabled:
                    logger.error(f"Baidu搜索 '{query}' 时出错: {e}.将回退到Google搜索。")
                else:
                    logger.error(f"Baidu搜索 '{query}' 时出错: {e}. 将返回空结果,如果需要搜索,请配置Google搜索。")
                return []
                
        baidu_results = await asyncio.to_thread(_search)
        if not baidu_results and self.google_enabled:
            logger.info(f"Baidu搜索失败，将回退到Google搜索")
            return await self.google_search(query)
        return baidu_results

    async def search_duckduckgo(self, query: str, proxy: str | None = None) -> List[Dict[str, str]]:
        """
        使用 asyncio.to_thread 异步执行同步的 DuckDuckGo 搜索。
        增加了随机退避和失败后回退到Google搜索的机制。
        """
        await asyncio.sleep(random.uniform(0.1, 1.0))  # 随机延迟，模拟人类行为

        def _search():
            try:
                with DDGS(proxy=proxy, timeout=5) as ddgs:
                    results = list(ddgs.text(query, max_results=10))
                return [
                    {'id': i, 'title': item.get('title'), 'link': item.get('href')}
                    for i, item in enumerate(results)
                ]
            except Exception as e:
                if self.google_enabled:
                    logger.warning(f"DuckDuckGo搜索 '{query}' 时出错: {e}. 将回退到Google搜索。")
                else:
                    logger.warning(f"DuckDuckGo搜索 '{query}' 时出错: {e}. 将返回空结果,如果需要搜索,请配置Google搜索。")
                return None # 返回None以触发回退
        
        ddg_results = await asyncio.to_thread(_search)

        if ddg_results is not None:
            return ddg_results
        elif self.google_enabled:
            return await self.google_search(query)
        else:
            return []

    async def google_search(self, query: str, api_key: Optional[str] = None, cse_id: Optional[str] = None) -> List[Dict[str, str]]:
        """使用Google Custom Search API进行搜索，作为备用方案。"""
        final_api_key = api_key if api_key is not None else self.google_api_key
        final_cse_id = cse_id if cse_id is not None else self.google_cse_id

        if not final_api_key or not final_cse_id:
            logger.error("Google API Key/CSE ID 未配置，无法使用Google搜索。")
            return []
        logger.info(f"Google搜索 '{query}'")
        def _search():
            try:
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    "q": query,
                    "key": final_api_key,
                    "cx": final_cse_id,
                    "num": 10
                }
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                return self.format_data_google(response.json())
            except Exception as e:
                logger.error(f"Google搜索 '{query}' 时出错: {e}")
                return []

        return await asyncio.to_thread(_search)

    def format_data_google(self, result: Dict) -> List[Dict]:
        """格式化Google搜索API返回的结果。"""
        if 'items' not in result:
            return []
        data = []
        for i, item in enumerate(result['items']):
            data.append({
                'id': i,
                "title": item.get('title'),
                "link": item.get('link')
            })
        return data

    async def search(self, query: str, chat_history: List = [], proxy: str | None = None) -> tuple[Dict[str, Any] | None, Dict[str, List[Dict[str, str]]]]:
        """
        并发执行所有搜索任务。
        为DuckDuckGo任务传递代理参数。
        """
        search_plan_data = keywords_extract(query, chat_history)
        logger.info(f"search_plan_data:{json.dumps(search_plan_data,ensure_ascii=False,indent=2)}")
        if not search_plan_data:
            logger.info(f'search_plan_data 为空')
            return None, {"NO_SEARCH_NEEDED": []}

        search_results = {}
        foundational_queries = search_plan_data.get('search_plan', {}).get('foundational_queries', [])
        tasks = []
        queries = []

        for item in foundational_queries:
            search_query = item.get('query')
            engine = item.get('engine', 'baidu').lower()
            if not search_query:
                continue
            
            queries.append(search_query)
            if engine == 'baidu':
                logger.info(f"Baidu搜索 '{search_query}'")
                tasks.append(self.search_baidu(search_query))
            elif engine == 'duckduckgo':
                logger.info(f"DuckDuckGo搜索 '{search_query}'")
                tasks.append(self.search_duckduckgo(search_query, proxy=proxy))
            else:
                logger.info(f"不支持的搜索引擎 '{engine}'，将使用Baidu进行搜索。")
                tasks.append(self.search_baidu(search_query))
        results_list = await asyncio.gather(*tasks)
        for q, r in zip(queries, results_list):
            search_results[q] = r

        return search_plan_data, search_results
if __name__ == '__main__':
    async def main():
        search_instance = Search()
        proxy_to_use = None

        print(f"使用的代理: {proxy_to_use if proxy_to_use else '无'}")

        start_time = time.time()
        test_query = "OpenAI近况"
        search_plan_data, results = await search_instance.search(test_query, proxy=proxy_to_use)
        
        print("\n--- 搜索计划 ---")
        print(json.dumps(search_plan_data, indent=2, ensure_ascii=False))
        print("\n--- 搜索结果 ---")
        print(json.dumps(results, indent=2, ensure_ascii=False))
        
        end_time = time.time()
        print(f'\n搜索时间：{end_time - start_time:.2f}秒')
    asyncio.run(main())