import json
from typing import List, Dict
from faiss import logger
from langchain_core.documents import Document
from .retrieval_method import BM25, split_doc_direct, Rerank, Similarity
import logging
from .config_manager import config

logger = logging.getLogger(__name__)

class Retrieval_v1:
    """
    Retrieval 类：实现多种文档检索与融合算法，包括相似度检索、BM25 检索和 RRF 融合等。
    """

    def __init__(self):
        """
        初始化 Retrieval 类，从 ConfigManager 加载检索参数。
        """
        self.quality = config.get('retrieval_quality', 'high') # 'high' or 'higher'
        self.similarity_method = True 
        self.rank_method = True

        self.similarity = Similarity() # 初始化Similarity实例
        self.rerank = Rerank() # 初始化Rerank实例
        self.bm25 = BM25()


    def rrf(self, rerank_results: List[Document], text_results: List[Document], rerank_results_all: List[Document], k: int = 10, m: int = 60) -> List[Document]:
        """
        使用 RRF（Reciprocal Rank Fusion）算法融合多个检索结果。

        Args:
            rerank_results (list): 重排检索结果。
            text_results (list): 文本检索结果。
            rerank_results_all (list): 综合重排的检索结果。
            k (int): 返回的文档数量。
            m (int): RRF 算法的平滑参数。

        Returns:
            list: 融合后的排序文档列表。
        """
        doc_scores = {}  # 存储文档及其对应分数
        for rank, doc in enumerate(rerank_results):
            content = doc.page_content
            if content not in doc_scores:
                doc_scores[content] = {'doc': doc, 'score': 0}
            doc_scores[content]['score'] += 1 / (rank + m)
        for rank, doc in enumerate(text_results):
            content = doc.page_content
            if content not in doc_scores:
                doc_scores[content] = {'doc': doc, 'score': 0}
            doc_scores[content]['score'] += 1 / (rank + m)
        for rank, doc in enumerate(rerank_results_all):
            content = doc.page_content
            if content not in doc_scores:
                doc_scores[content] = {'doc': doc, 'score': 0}
            doc_scores[content]['score'] += 1 / (rank + m)
        sorted_results = [
            doc_data['doc'] for doc_data in sorted(doc_scores.values(), key=lambda x: x['score'], reverse=True)[:k]
        ]
        return sorted_results

    def similarity_retrieval(self, docs: List[Document], query: str, top_k: int = 10) -> List[Document]:
        """
        执行相似度检索并结合重排返回高质量文档。

        Args:
            docs (list): 文档分块列表。
            query (str): 查询内容。
            top_k (int): 返回文档数量。


        Returns:
            list: 检索和重排后的文档列表。
        """
        logger.info('Executing similarity+rerank for high quality retrieval')


        similarity_results = self.similarity.similarity_retrieve(docs,[query],2*top_k)
        flat_similarity_results = [doc for sublist in similarity_results for doc in sublist]
        logger.info(f"similarity_results: {flat_similarity_results}")
        rerank_results = self.rerank.rerank(flat_similarity_results, query, top_k)
        logger.info(f"rerank_results: {rerank_results}")
        print(f'Rerank results: {rerank_results}')

        return rerank_results

    def similarity_retrieval_plus(self, docs: List[Document], queries: List[str], top_k: int = 10) -> List[Document]:
        """
        执行相似度检索结合 BM25 检索和重排以提高文档检索质量。

        Args:
            docs (list): 文档分块列表。
            queries (list): 查询内容列表。
            top_k (int): 返回文档数量。

        Returns:
            list: 检索和重排后的文档列表。
        """
        logger.info('Executing similarity+BM25+rerank for higher quality retrieval')
        bm25_results = self.bm25.bm25_retrieval(docs, queries, top_k)
        logger.info(f"bm25_results: {bm25_results}")

        similarity_results_nested = self.similarity.similarity_retrieve(docs, queries, top_k)
        similarity_results = [doc for sublist in similarity_results_nested for doc in sublist]
        logger.info(f"similarity_results: {similarity_results}")
        results_all = bm25_results + similarity_results
        rerank_results = self.rerank.rerank(results_all, queries[0], top_k)
        logger.info(f"rerank_results: {rerank_results}")
        rrf_results = self.rrf(similarity_results, bm25_results, rerank_results, k=top_k)
        return rrf_results



    def user_defined(self,docs: List[Document]) -> List[Document]:
        """
        自定义的召回方法，你可以尝试不同的文本切分方法，不同的召回策略
        """
        return []

    def retrieve(self, web_pages: List[Dict], queries: List[str],search_plan_data: dict) -> List[Document]:
        """
        主检索函数，根据配置选择合适的检索方法（相似度检索或排序检索）。

        Args:
            web_pages (list): 原始文档列表.
            queries (list): 查询内容列表,queries[0]是用户查询，queries[1]是搜索关键词。

        Returns:
            list: 检索结果。
        """
        all_pages = []
        if isinstance(web_pages, dict):
            for results in web_pages.values():
                all_pages.extend(results)
        else:
            all_pages = web_pages

        foundational_queries = search_plan_data.get('search_plan',{}).get('foundational_queries',[])
        if foundational_queries:
            queries.extend([q['query'] for q in foundational_queries if 'query' in q])
        logger.info(f"Queries: {queries}")
        split_docs = split_doc_direct(all_pages)
        if self.similarity_method:
            top_k = 5 if search_plan_data.get('query_analysis',{}).get('assessed_complexity',{}) == "[Simple]" else 10
            if self.quality == 'high':
                return self.similarity_retrieval(split_docs, queries[0], top_k)
            else:
                return self.similarity_retrieval_plus(split_docs, queries, top_k)
        
        else:
            return self.user_defined(split_docs)
