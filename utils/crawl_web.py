import httpx
import fitz  # PyMuPDF
from readability import Document
from bs4 import BeautifulSoup
import chardet  # 添加用于检测编码的库
from selectolax.parser import HTMLParser as SelectolaxParser
import re
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class Crawl:

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    ]
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes

    def __init__(
            self,
            max_workers: int = 10,
            max_retries: int = 3,
            timeout_config: Tuple[float, float, float, float] = (10.0, 15.0, 10.0, 10.0),
    ):
        self.MAX_WORKERS = max_workers
        self.MAX_RETRIES = max_retries
        self.TIMEOUT = httpx.Timeout(
            timeout_config[0], read=timeout_config[1], write=timeout_config[2], pool=timeout_config[3]
        )
        self.client = httpx.Client(http2=True, follow_redirects=True, timeout=self.TIMEOUT)

    def _get_random_user_agent(self) -> str:
        return random.choice(self.USER_AGENTS)

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'[\r\t\s]+', ' ', text)
        text = re.sub(r'[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uff60\u2000-\u206f.,!?;:，。！？；：、]+', '', text)
        text = re.sub(r'([.,!?;:，。！？；：、])\1+', r'\1', text)
        return text.strip()
    
    def _is_text_valid(self, text: str) -> bool:
        """
        检查文本是否有明显的乱码问题
        """
        if not text or len(text) < 20:
            return False
        questionable_chars = sum(1 for c in text if ord(c) > 0xFFFF or c == '' or c == '□' or c == '■')
        if len(text) > 0 and questionable_chars / len(text) > 0.15:  # 超过15%为乱码字符则认为无效
            logger.warning(f"Text contains too many questionable characters: {questionable_chars}/{len(text)}")
            return False
        for i in range(len(text) - 5):
            if len(set(text[i:i+6])) == 1 and text[i] not in ('.', '-', '_', ' ', '*'):
                logger.warning(f"Text contains suspicious repetitive characters: {text[i:i+6]}")
                return False
                
        return True
    
    def _fix_encoding_issues(self, text: str) -> str:
        """
        尝试修复常见的编码问题
        """
        if '%' in text and text.count('%') > len(text) * 0.05:
            from urllib.parse import unquote
            try:
                return unquote(text)
            except:
                pass
        replacements = {
            '&nbsp;': ' ', '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"',
            '&apos;': "'", '&#39;': "'", '&#160;': ' ', '&#xa0;': ' ', 
            'â€™': "'", 'â€"': "–", 'â€"': "—", 'â€˜': "'", 'â€™': "'",
            'â€œ': """, 'â€': """, 'Â': '', 'â': '', '': '',
        }
        
        for wrong, correct in replacements.items():
            text = text.replace(wrong, correct)
        
        return text

    def _parse_html_with_selectolax(self, html_content: bytes, url: str) -> str:
        try:
            detected_encoding = None
            try:
                detection_result = chardet.detect(html_content[:10000])
                if detection_result and detection_result['confidence'] > 0.7:
                    detected_encoding = detection_result['encoding']
                    logger.info(f"Detected encoding for {url}: {detected_encoding} (confidence: {detection_result['confidence']})")
            except Exception as e:
                logger.warning(f"Encoding detection failed for {url}: {e}")
            decoded_html = BeautifulSoup(html_content, 'lxml')
            soup_str = str(decoded_html)
            if soup_str.count('') > len(soup_str) * 0.01 and detected_encoding:
                try:
                    html_str = html_content.decode(detected_encoding, errors='replace')
                    decoded_html = BeautifulSoup(html_str, 'lxml')
                    logger.info(f"Re-decoded HTML with detected encoding: {detected_encoding}")
                except Exception as e:
                    logger.warning(f"Failed to re-decode with detected encoding: {e}")
            doc = Document(str(decoded_html))
            summary_html = doc.summary(html_partial=True)
            
            if not summary_html or len(summary_html) < 100:
                body = decoded_html.find('body')
                if body:
                    summary_html = str(body)
                    logger.info(f"Readability extraction failed, using body tag for {url}")
            tree = SelectolaxParser(summary_html)
            for node in tree.css('script, style, nav, footer, header, aside, form, a, img, figure, iframe, noscript'):
                node.decompose()
            
            main_text = ""
            if tree.body:
                main_text = tree.body.text(separator='\n')
            cleaned_text = self._clean_text(main_text)
            if not self._is_text_valid(cleaned_text):
                logger.warning(f"Text validity check failed for {url}, attempting encoding fixes")
                fixed_text = self._fix_encoding_issues(main_text)
                cleaned_text = self._clean_text(fixed_text)
            
            return cleaned_text
        except Exception as e:
            logger.error(f"Error parsing HTML for {url}: {e}", exc_info=True)
            return ""

    def _extract_pdf_content(self, pdf_bytes: bytes, url: str) -> str:
        try:
            full_text = []
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                for page in doc:
                    full_text.append(page.get_text()) # type: ignore
            return self._clean_text(" ".join(full_text))
        except Exception as e:
            print(f"Error extracting PDF content for {url}: {e}")
            logger.error(f"Error extracting PDF content for {url}: {e}")
            return ""

    def _fetch_one(self, web_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        link = web_info.get('link')
        query_key = web_info.get('query_key')

        if not link or not isinstance(link, str) or not link.startswith('http'):
            logger.error(f"Skipping invalid link for query '{query_key}': {link}")
            return None

        for attempt in range(self.MAX_RETRIES):
            try:
                headers = {
                    'User-Agent': self._get_random_user_agent(),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Cache-Control': 'max-age=0'
                }
                try:
                    head_response = self.client.head(link, headers=headers, follow_redirects=True, timeout=5.0)
                    content_length = int(head_response.headers.get('Content-Length', '0'))
                    if content_length > self.MAX_FILE_SIZE:
                        logger.warning(f"Skipping large file ({content_length/1024/1024:.1f}MB > {self.MAX_FILE_SIZE/1024/1024}MB): {link}")
                        return None
                    content_type = head_response.headers.get('Content-Type', '').lower()
                    if any(media_type in content_type for media_type in ['image/', 'audio/', 'video/', 'application/zip', 'application/x-rar', 'application/x-tar']):
                        logger.info(f"Skipping unsupported media type {content_type}: {link}")
                        return None
                except Exception as e:
                    logger.warning(f"HEAD request failed for {link}, will try direct GET: {e}")
                response = self.client.get(link, headers=headers)
                
                if 400 <= response.status_code < 500:
                    logger.error(f"Client error {response.status_code} for {link}. Won't retry.")
                    return None
                    
                response.raise_for_status()
                if len(response.content) > self.MAX_FILE_SIZE:
                    logger.warning(f"Skipping large response ({len(response.content)/1024/1024:.1f}MB > {self.MAX_FILE_SIZE/1024/1024}MB): {link}")
                    return None
                content_type = response.headers.get('Content-Type', '').lower()
                if any(media_type in content_type for media_type in ['image/', 'audio/', 'video/', 'application/zip', 'application/x-rar', 'application/octet-stream']):
                    logger.info(f"Skipping media content {content_type}: {link}")
                    return None
                if 'pdf' in content_type or str(response.url).lower().endswith('.pdf'):
                    content = self._extract_pdf_content(response.content, str(response.url))
                elif 'text/plain' in content_type:
                    try:
                        text = response.text
                        content = self._clean_text(text)
                    except Exception as e:
                        logger.error(f"Error decoding plain text: {e}")
                        encoding = chardet.detect(response.content[:10000])['encoding']
                        if encoding:
                            text = response.content.decode(encoding, errors='replace')
                            content = self._clean_text(text)
                        else:
                            return None
                else:
                    content = self._parse_html_with_selectolax(response.content, str(response.url))
                if content and len(content) > 20:
                    if not self._is_text_valid(content):
                        logger.warning(f"Content quality check failed for {link}")
                        return None
                        
                    return {
                        'id': web_info['id'],
                        'title': web_info.get('title', ''),
                        'link': link,
                        'content': content,
                        'query_key': query_key
                    }
                else:
                    logger.warning(f"Content for {link} is too short or empty after cleaning")
                    return None
                    
            except httpx.RequestError as e:
                logger.error(f"Attempt {attempt + 1}/{self.MAX_RETRIES}: Network error for {link}: {type(e).__name__}")
                if attempt < self.MAX_RETRIES - 1:
                    sleep_time = (2 ** attempt) + random.uniform(0.5, 1.0)
                    time.sleep(sleep_time)
                else:
                    logger.error(f"FAIL: Max retries reached for {link}. Error: {e}")
                    return None
            except Exception as e:
                logger.error(f"An unexpected error occurred for {link}: {e}", exc_info=True)
                return None
                
        return None

    def crawl(self, search_results: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        crawled_results = {query: [] for query in search_results.keys()}
        tasks = []

        for query_key, items in search_results.items():
            for item in items:
                task_item = item.copy()
                task_item['query_key'] = query_key
                tasks.append(task_item)

        with ThreadPoolExecutor(max_workers=max(1,min(self.MAX_WORKERS, len(tasks)))) as executor:
            future_to_task = {executor.submit(self._fetch_one, task): task for task in tasks}

            for future in as_completed(future_to_task):
                result = future.result()
                if result:
                    original_query = result.pop('query_key')
                    crawled_results[original_query].append(result)
        
        for query in crawled_results:
            crawled_results[query] = sorted(crawled_results[query], key=lambda x: x['id'])
        logger.info(f'crawled_results: {crawled_results}')
            
        return crawled_results

    def close(self):
        self.client.close()

if __name__ == '__main__':
    sample_search_data = {
        "武汉天气预报": [
            {
                "id": 0, "title": "武汉天气预报15天", "link": "https://www.weather.com.cn/weather15d/101200101.shtml"
            },
            {
                "id": 1, "title": "武汉天气-中国天气网", "link": "http://www.weather.com.cn/weather/101200101.shtml"
            },
            {
                "id": 2, "title": "Invalid link test", "link": "/some/relative/path"
            }
        ],
        "python tutorial": [
            {
                "id": 0, "title": "Python Tutorial - W3Schools", "link": "https://www.w3schools.com/python/"
            },
            {
                "id": 1, "title": "The Python Tutorial — Python 3.12.4 documentation", "link": "https://docs.python.org/3/tutorial/"
            },
            {
                "id": 2, "title": "Python For Beginners", "link": "https://www.python.org/about/gettingstarted/"
            },
            {
                "id": 3, "title": "Real Python: Python Tutorials", "link": "https://realpython.com/"
            }
        ]
    }

    crawler = Crawl(max_workers=5)
    
    start_time = time.time()
    final_results = crawler.crawl(sample_search_data)
    end_time = time.time()
    
    crawler.close()
    print(json.dumps(final_results, ensure_ascii=False, indent=4))
    
    print(f"\nCrawling complete.")
    print(f"Total time taken: {end_time - start_time:.2f} seconds.")
