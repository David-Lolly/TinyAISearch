import json
from typing import List, Dict
from langchain_core.documents import Document
from .retrieval import BM25, split_doc_direct, Rerank, Similarity


class Retrieval:
    """
    Retrieval 类：实现多种文档检索与融合算法，包括相似度检索、BM25 检索和 RRF 融合等。
    """

    def __init__(self):
        """
        初始化 Retrieval 类，从配置文件加载检索参数。
        """
        # 加载配置文件
        with open(r'./config/config.json', encoding='utf-8') as f:
            self.config = json.load(f)

        # 检索方法激活状态
        self.similarity_method = self.config['retrieval']['method']['similarity']['activate']  # 是否启用相似度检索
        self.rank_method = self.config['retrieval']['method']['rank']['activate']  # 是否启用排序检索
        self.quality = self.config['retrieval']['quality']  # 检索质量 (high 或 higher)
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

        # 处理重排检索结果
        for rank, doc in enumerate(rerank_results):
            content = doc.page_content
            if content not in doc_scores:
                doc_scores[content] = {'doc': doc, 'score': 0}
            doc_scores[content]['score'] += 1 / (rank + m)

        # 处理文本检索结果
        for rank, doc in enumerate(text_results):
            content = doc.page_content
            if content not in doc_scores:
                doc_scores[content] = {'doc': doc, 'score': 0}
            doc_scores[content]['score'] += 1 / (rank + m)

        # 处理所有综合重排结果
        for rank, doc in enumerate(rerank_results_all):
            content = doc.page_content
            if content not in doc_scores:
                doc_scores[content] = {'doc': doc, 'score': 0}
            doc_scores[content]['score'] += 1 / (rank + m)

        # 根据得分排序并返回前 k 个文档
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
        print('Executing similarity+rerank for high quality retrieval')


        similarity_results = self.similarity.similarity_retrieval(docs,[query],2*top_k)
        # 对结果进行重排
        rerank_results = self.rerank.rerank(similarity_results, query, top_k)
        print(f'Rerank results: {rerank_results}')

        return rerank_results

    def similarity_retrieval_plus(self, docs: List[Document], queries: List, top_k: int = 10) -> List[Document]:
        """
        执行相似度检索结合 BM25 检索和重排以提高文档检索质量。

        Args:
            docs (list): 文档分块列表。
            queries (list): 查询内容列表。
            top_k (int): 返回文档数量。

        Returns:
            list: 检索和重排后的文档列表。
        """
        print('Executing similarity+BM25+rerank for higher quality retrieval')

        # 使用 BM25 检索
        bm25_results = self.bm25.bm25_retrieval(docs, queries, top_k)
        print(f'BM25 results: {bm25_results}')

        # similarity_results = self.similarity.similarity_retrieval(docs, queries, 2*top_k)
        similarity_results = self.similarity.similarity_retrieval(docs, queries, top_k)


        # 融合 BM25 和相似度检索结果
        results_all = bm25_results + similarity_results
        rerank_results_all = self.rerank.rerank(results_all, queries[0], top_k)

        # 使用 RRF 算法对3中检索结果进行融合
        # rrf_results = self.rrf(rerank_results, bm25_results, rerank_results_all, k=top_k)
        rrf_results = self.rrf(similarity_results, bm25_results, rerank_results_all, k=top_k)
        return rrf_results

    def rank_retrieval(self, docs: List[Document], query: str, top_k: int = 10) -> List[Document]:
        """
        使用 BM25 检索和排序功能返回高质量文档。

        Args:
            docs (list): 文档分块列表。
            query (str): 查询内容。
            top_k (int): 返回文档数量。

        Returns:
            list: 排序后的文档列表。
        """
        print('Executing bm25+rank for high quality retrieval')

        # 使用 BM25 检索
        bm25_results = self.bm25.bm25_retrieval(docs, [query], top_k)
        print(f'BM25 results: {bm25_results}')

        # 使用排序模型对文档进行排序
        rank_results = self.rerank.rerank(docs, query, top_k)
        print(f'Rerank results: {rank_results}')

        rrf_results = self.rrf(rank_results, bm25_results, [], k=top_k)

        return rrf_results

    def rank_retrieval_plus(self, docs: List[Document], queries: List, top_k: int = 10) -> List[Document]:
        """
        使用 BM25 检索和排序模型结合多个查询进行更高质量的文档检索。

        Args:
            docs (list): 文档分块列表。
            queries (list): 查询内容列表。
            top_k (int): 返回文档数量。

        Returns:
            list: 融合排序后的文档列表。
        """
        print('Executing bm25+rank for higher quality retrieval')
        bm25_results = self.bm25.bm25_retrieval(docs, queries, top_k)
        print(f'BM25 results: {bm25_results}')

        # 使用排序模型对文档进行排序
        rerank_results = self.rerank.rerank(docs, queries[0], top_k)
        print(f'Rerank results: {rerank_results}')

        # 融合 BM25 和重排结果
        results_all = bm25_results + rerank_results
        rerank_results_all = self.rerank.rerank(results_all, queries[0],top_k)

        # 使用 RRF 算法对3种检索结果进行融合
        rrf_results = self.rrf(rerank_results, bm25_results, rerank_results_all, top_k)
        return rrf_results

    def user_defined(self,docs):
        """
        自定义的召回方法，你可以尝试不同的文本切分方法，不同的召回策略
        """
        pass

    def retrieve(self, docs: List[Dict], queries: List[str]) -> List[Document]:
        """
        主检索函数，根据配置选择合适的检索方法（相似度检索或排序检索）。

        Args:
            docs (list): 原始文档列表，内容如下：
                {
                    'id': web id,
                    'title': web title,
                    'link': web link,
                    'text': web text,
                }
            queries (list): 查询内容列表,queries[0]是用户查询，queries[1]是搜索关键词。

        Returns:
            list: 检索结果。
        """
        # 将文档分块
        split_docs = split_doc_direct(docs)

        if len(split_docs) >150:
            split_docs = split_docs[:150]
        
        # 根据配置执行检索方法
        if self.similarity_method:
            top_k = self.config['retrieval']['method']['similarity']['top_k']
            if self.quality == 'high':
                # 高质量召回
                return self.similarity_retrieval(split_docs, queries[1], top_k)
            else:
                # 更高质量召回
                return self.similarity_retrieval_plus(split_docs, queries, top_k)
        elif self.rank_method:
            top_k = self.config['retrieval']['method']['rank']['top_k']
            if self.quality == 'high':
                # 高质量召回
                return self.rank_retrieval(split_docs, queries[1], top_k)
            else:
                # 更高质量召回
                return self.rank_retrieval_plus(split_docs, queries, top_k)
        else:
            # 自定义的召回方法
            return self.user_defined(docs)
