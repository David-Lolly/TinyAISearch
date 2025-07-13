import json
import os
import time
from typing import List, Dict, Any, Optional
import jieba
import numpy as np
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from scipy.special import softmax
from rank_bm25 import BM25Okapi
import logging
from .config_manager import config

logger = logging.getLogger(__name__)

class Retrieval_v2:
    def __init__(self):

        self.API_MAX_BATCH_SIZE = 10
        self.EMBEDDING_MAX_LENGTH = 1024
        self.max_workers = min(self.API_MAX_BATCH_SIZE, (os.cpu_count() or 1) + 4)
        self.max_retries = 3
        self.request_timeout = 30  # seconds
        self.session = requests.Session()
        retries = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.session.headers.update({
            "Authorization": f"Bearer {config.get('embedding_api_key')}",
            "Content-Type": "application/json"
        })


    def _embed_batch_cloud(self, texts: List[str]) -> Optional[List[List[float]]]:
        payload = {
            "model": config.get('embedding_model_name'),
            "input": texts,
            "encoding_format": "float"
        }
        try:
            response = self.session.post(
                config.get('embedding_base_url'), 
                json=payload, 
                timeout=self.request_timeout
            )
            response.raise_for_status()
            data = response.json()["data"]
            data.sort(key=lambda x: x['index'])
            return [item["embedding"] for item in data]
        except Exception as e:
            logger.error(f"Cloud embedding batch failed: {e}")
            return None

    def _embed_texts(self, texts: List[str]) -> List[Optional[np.ndarray]]:
        all_embeddings: List[Optional[np.ndarray]] = [None] * len(texts)
        batches = [texts[i:i + self.API_MAX_BATCH_SIZE] for i in range(0, len(texts), self.API_MAX_BATCH_SIZE)]
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_index = {
                executor.submit(self._embed_batch_cloud, batch): i * self.API_MAX_BATCH_SIZE
                for i, batch in enumerate(batches)
            }
            for future in as_completed(future_to_index):
                start_index = future_to_index[future]
                batch_embeddings = future.result()
                if batch_embeddings:
                    for i, emb in enumerate(batch_embeddings):
                        all_embeddings[start_index + i] = np.array(emb)
        return all_embeddings

    @staticmethod
    def _cosine_similarity(v1: Optional[np.ndarray], v2: Optional[np.ndarray]) -> float:
        if v1 is None or v2 is None: return 0.0
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        if norm_v1 == 0 or norm_v2 == 0: return 0.0
        return np.dot(v1, v2) / (norm_v1 * norm_v2)

    @staticmethod
    def _get_bm25_scores(query: str, corpus: List[str]) -> np.ndarray:
        if not corpus:
            return np.array([])

        tokenized_corpus = [list(jieba.cut(doc)) for doc in corpus]
        if not any(tokenized_corpus):
            logger.warning("BM25 corpus is empty after tokenization. Returning zero scores.")
            return np.zeros(len(corpus))

        bm25 = BM25Okapi(tokenized_corpus)
        tokenized_query = list(jieba.cut(query))
        return bm25.get_scores(tokenized_query)

    def retrieve(self, search_plan_data: Dict[str, Any], search_results: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        final_results = {}
        complexity = search_plan_data.get('query_analysis', {}).get('assessed_complexity', '[Moderate]')
        top_k = 1 if complexity == '[Simple]' else 2
        
        queries = list(search_results.keys())
        if not queries:
            return {}

        logger.info("Embedding all unique queries...")
        query_embeddings = self._embed_texts(queries)
        query_embedding_map = {query: emb for query, emb in zip(queries, query_embeddings)}

        for query, pages in search_results.items():
            if not pages:
                final_results[query] = []
                continue

            logger.info(f"Processing {len(pages)} pages for query: '{query}'")
            contents_for_embedding = ["Title: " + p.get('title', '') + " Content: " + p.get('content', '')[:self.EMBEDDING_MAX_LENGTH] for p in pages]
            contents_for_bm25 = ["Title: " + p.get('title', '') + " Content: " + p.get('content', '') for p in pages]
            logger.info("Calculating embedding similarities...")
            page_embeddings = self._embed_texts(contents_for_embedding)
            query_emb = query_embedding_map.get(query)

            embedding_scores = np.array([self._cosine_similarity(query_emb, page_emb) for page_emb in page_embeddings])
            logger.info("Calculating BM25 similarities...")
            bm25_scores = self._get_bm25_scores(query, contents_for_bm25)
            norm_embedding_scores = softmax(embedding_scores) if np.any(embedding_scores) else embedding_scores
            norm_bm25_scores = softmax(bm25_scores) if np.any(bm25_scores) else bm25_scores
            logger.info(f'norm_embedding_scores: {norm_embedding_scores}')
            logger.info(f'norm_bm25_scores: {norm_bm25_scores}')

            combined_scores = norm_embedding_scores + 0.7*norm_bm25_scores
            for i, page in enumerate(pages):
                page['embedding_score'] = norm_embedding_scores[i]
                page['bm25_score'] = norm_bm25_scores[i]
                page['combined_score'] = combined_scores[i]

            sorted_pages = sorted(pages, key=lambda x: x['combined_score'], reverse=True)
            logger.info(f"Sorted pages: {sorted_pages}")
            final_results[query] = sorted_pages[:top_k]
            logger.info(f"Selected top {len(final_results[query])} pages for query '{query}'.")

        return final_results

    def close(self):
        if hasattr(self, 'session'):
            self.session.close()
            logger.info("HTTP session closed.")


if __name__ == '__main__':
    mock_search_plan = {
        'query_analysis': {'assessed_complexity': '[Complex]'}
    }
    mock_search_results = {
      "中东局势": [
        {"id": 0, "title": "中东最新动态", "link": "http://example.com/1", "content": "关于中东地区的最新局势非常复杂，涉及多个国家和非国家行为者。"},
        {"id": 1, "title": "以色列和巴勒斯坦冲突", "link": "http://example.com/2", "content": "以色列与巴勒斯坦的长期冲突是中东地区不稳定的一个核心因素。"},
        {"id": 2, "title": "伊朗核问题", "link": "http://example.com/3", "content": "伊朗的核计划及其与西方的关系也是影响中东局势的关键。"},
        {"id": 3, "title": "不相关的食谱", "link": "http://example.com/4", "content": "如何制作一个美味的巧克力蛋糕，首先需要准备面粉和糖。"}
      ]
    }
    
    try:
        retriever = Retrieval_v2()
        start_time = time.time()
        ranked_results = retriever.retrieve(mock_search_plan, mock_search_results)
        end_time = time.time()

        retriever.close()

    except FileNotFoundError as e:
        logger.error(f"Could not run example: {e}")
    except Exception as e:
        logger.error(f"An error occurred during the example run: {e}", exc_info=True)
