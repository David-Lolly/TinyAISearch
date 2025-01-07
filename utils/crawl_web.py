import nest_asyncio
import aiohttp
import re
import fitz  # PyMuPDF
from readability import Document
from bs4 import BeautifulSoup
import asyncio
from crawl4ai import AsyncWebCrawler
from typing import List, Dict
import logging



class Crawl:
    """
    具有异步功能的网络爬取和文本清洗类
    """
    def __init__(
        self,
        max_concurrent_tasks: int = 10,
        global_timeout: float = 6.0,
        max_retry: int = 2,
        log_level: int = logging.INFO
    ):
        """
        初始化Crawl对象，并配置可自定义的参数

        :param max_concurrent_tasks: 最大并发任务数
        :param global_timeout: 全局网络请求超时时间
        :param max_retry: 失败请求的最大重试次数
        :param log_level: 日志级别
        """
        nest_asyncio.apply()

        # 配置参数
        self.MAX_CONCURRENT_TASKS = max_concurrent_tasks
        self.GLOBAL_TIMEOUT = global_timeout
        self.MAX_RETRY = max_retry
        logging.basicConfig(
            level=logging.ERROR,  # 记录错误日志
            format="%(asctime)s - %(levelname)s - %(message)s",  # 日志格式
            handlers=[
                logging.StreamHandler()  # 输出到控制台
            ]
        )
        self.logger = logging.getLogger()


    async def _clean_html(self, content):
        """清理HTML内容，去除不需要的标签和格式化文本"""
        try:
            doc = Document(content.html)
            content = doc.summary(html_partial=True)

            soup = BeautifulSoup(content, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'comments', 'a', 'img']):
                tag.decompose()  # 删除不需要的标签
            main_text = soup.get_text(separator='\n')  # 提取主要文本

            # 格式化文本，去除特殊字符和不必要的空格
            clean_text = re.sub(r'\n', '', main_text)
            clean_text = re.sub(r'\$\$.*?\$\$', '', clean_text)
            clean_text = re.sub(r'\$.*?\$', '', clean_text)
            clean_text = re.sub(r'\\\((.*?)\\\)', '', clean_text)
            clean_text = re.sub(r'[^\w\s\u4e00-\u9fa5，。！？；：、.]+', '', clean_text)
            clean_text = re.sub(r'[，。！？；：、.]{2,}', lambda x: x.group()[0], clean_text)
            text = re.sub(r'\s+', ' ', clean_text).strip()
            # 清除或替换掉不可编码的字符
            text = text.encode('utf-8', 'ignore').decode('utf-8')

            return text
        except Exception as e:
            self.logger.error(f"HTML清理错误: {e}")
            return ""

    async def _extract_pdf_content(self, url: str, timeout: float = None) -> str:
        """
        下载并解析PDF内容，带超时机制
        """
        timeout = timeout or self.GLOBAL_TIMEOUT
        try:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                        if response.status != 200:
                            self.logger.warning(f"PDF下载失败，状态码: {response.status}")
                            return ""
                        pdf_data = await response.read()
                except asyncio.TimeoutError:
                    self.logger.warning(f"PDF下载超时: {url}")
                    return ""

            pdf_text = ""
            with fitz.open(stream=pdf_data, filetype="pdf") as doc:
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    pdf_text += page.get_text()

            # 清理PDF文本内容
            clean_text = re.sub(r'\n', '', pdf_text)
            clean_text = re.sub(r'\$\$.*?\$\$', '', clean_text)
            clean_text = re.sub(r'\$.*?\$', '', clean_text)
            clean_text = re.sub(r'\\\((.*?)\\\)', '', clean_text)
            clean_text = re.sub(r'[^\w\s\u4e00-\u9fa5，。！？；：、.]+', '', clean_text)
            clean_text = re.sub(r'[，。！？；：、.]{2,}', lambda x: x.group()[0], clean_text)
            # 清除或替换掉不可编码的字符
            clean_text = clean_text.encode('utf-8', 'ignore').decode('utf-8')
            text = re.sub(r'\s+', ' ', clean_text).strip()

            return text
        except Exception as e:
            self.logger.error(f"PDF提取错误 {url}: {e}")
            return ""

    async def _fetch_url(self, crawler, web: Dict, web_text: List[Dict], semaphore: asyncio.Semaphore) -> None:
        """
        抓取URL内容并处理，带信号量控制并发，带超时和重试机制
        """
        for attempt in range(self.MAX_RETRY):
            try:
                # URL和链接有效性检查
                if not web.get('link') or not isinstance(web.get('link'), str):
                    self.logger.warning(f"无效的URL: {web}")
                    return

                # 使用信号量控制并发
                async with semaphore:
                    # 设置超时处理
                    try:
                        if web['link'].endswith('.pdf'):
                            clean_text = await asyncio.wait_for(
                                self._extract_pdf_content(web['link']),
                                timeout=self.GLOBAL_TIMEOUT
                            )
                        else:
                            result = await asyncio.wait_for(
                                crawler.arun(url=web['link']),
                                timeout=self.GLOBAL_TIMEOUT
                            )
                            clean_text = await self._clean_html(result)

                    except asyncio.TimeoutError:
                        self.logger.warning(f"抓取 {web['link']} 超时，第 {attempt + 1} 次尝试")
                        if attempt == self.MAX_RETRY:
                            return
                        continue

                    # 检查内容是否为空
                    if not clean_text or len(clean_text.strip()) < 10:
                        self.logger.warning(f"URL {web['link']} 的内容过少或为空")
                        return

                    # 成功获取并存储内容
                    web_text.append({
                        'id': web['id'],
                        'title': web.get('title', ''),
                        'link': web['link'],
                        'text': clean_text,
                    })
                    return  # 成功后退出重试循环

            except Exception as e:
                self.logger.error(f"处理 URL {web['link']} 时发生错误（第 {attempt + 1} 次尝试）: {e}")
                if attempt == self.MAX_RETRY:
                    return

    async def _get_web_pages(self, search_results: List[Dict]) -> List[Dict]:
        """
        并发处理网页爬取任务，控制并发数
        """
        # 创建一个信号量来限制并发数
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_TASKS)

        # 准备全局存储结果的列表
        web_text = []

        # 使用上下文管理器创建爬虫
        async with AsyncWebCrawler(verbose=True) as crawler:
            # 创建任务列表
            tasks = [
                self._fetch_url(crawler, web, web_text, semaphore)
                for web in search_results
            ]

            # 并发执行所有任务
            await asyncio.gather(*tasks)

        # 按ID排序
        web_text = sorted(web_text, key=lambda x: x['id'])

        return web_text

    def crawl(self, search_results: List[Dict]) -> List[Dict]:
        """
        对外暴露的爬取接口，执行异步操作并返回结果

        :param search_results: 要爬取的URL列表
        :return: 包含爬取内容的字典列表
        """
        try:
            return asyncio.run(self._get_web_pages(search_results))
        except Exception as e:
            # self.logger.error(f"爬取过程中发生错误: {e}")
            print(f"爬取过程中发生错误: {e}")
            return []