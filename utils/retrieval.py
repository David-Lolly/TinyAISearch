import json
import time
from typing import List, Dict
import jieba
import numpy as np
import requests
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import faiss
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from openai import OpenAI
from tqdm import tqdm
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
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


def split_doc_direct(documents: List[Dict]) -> List[Document]:
    """
    将输入文档拆分为更小的文本块，便于后续检索和处理

    :param documents: 原始文档列表，每个文档包含text和title
    :return: 拆分后的文档列表
    """
    # 将输入文档转换为Langchain的Document对象
    documents = [Document(
        page_content=item['text'] + item['title'],
        metadata={'url': item['link'], 'title': item['title']}
    ) for item in documents]

    # 递归字符拆分器
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=256,
        chunk_overlap=32,
        separators=["\n\n", "\n", "。", ".", "？", "?", "！", "!", ";",'，',','],
        strip_whitespace=True
    )

    # 执行文本拆分
    split_docs = text_splitter.split_documents(documents)
    return split_docs


class Similarity():
    """
    文本相似度检索和嵌入处理类
    支持云端和本地嵌入模型，提供多种相似度检索方法
    """

    def __init__(self):
        """
        从配置文件加载嵌入模型相关配置
        支持云端和本地嵌入模型配置
        """
        with open(r'./config/config.json', encoding='utf-8') as f:
            config = json.load(f)

        # 云端嵌入模型配置
        self.local = config['local_embedding_model']
        self.embedding_model_name = config['embedding_model']['cloud_embedding']['model_name']
        self.embedding_api_key = config['embedding_model']['cloud_embedding']['api_key']
        self.embedding_base_url = config['embedding_model']['cloud_embedding']['base_url']

        # 本地嵌入模型配置
        self.embedding_model_path = config['embedding_model']['local_embedding']['model_path']

        self.max_attempts = 2
        if self.local:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.embedding_model_path,
                model_kwargs={'device': 'cuda:0'}
            )
            print('embedding模型初始化完成')

    def embed_documents(self, split_docs: List[Document]) -> List[Dict]:
        """
        为文档生成嵌入向量，支持重试机制和进度跟踪

        :param split_docs: 预处理后的文档列表
        :return: 包含嵌入向量和元数据的列表
        """
        embeddings = []
        total_docs = len(split_docs)  # 总文档数
        start_time = time.time()  # 记录开始时间

        # 使用tqdm显示详细进度
        with tqdm(total=total_docs, desc="文档嵌入处理", unit="doc") as progress_bar:
            for doc_index, doc in enumerate(split_docs):
                text = doc.page_content
                url = self.embedding_base_url

                # 构建嵌入请求载荷
                payload = {
                    "model": self.embedding_model_name,
                    "input": text,
                    "encoding_format": "float"
                }
                headers = {
                    "Authorization": f"Bearer {self.embedding_api_key}",
                    "Content-Type": "application/json"
                }

                # 设置最大重试次数
                max_attempts = 2
                for attempt in range(self.max_attempts):
                    try:
                        response = requests.request("POST", url, json=payload, headers=headers, timeout=3)

                        # 检查嵌入请求是否成功
                        if response.status_code == 200:
                            embeddings.append({
                                'vector': response.json()["data"][0]["embedding"],
                                'metadata': doc.metadata
                            })
                            break  # 成功后退出重试循环
                        else:
                            logger.error(f"文档嵌入失败，第{doc_index+1}个文档尝试 {attempt + 1}: 状态码 {response.status_code}")

                            # 最后一次尝试失败
                            if attempt == max_attempts - 1:
                                logger.error(f"第{doc_index+1}个文档经过 {max_attempts} 次尝试，文档嵌入仍然失败",exc_info=True)
                                break

                    except requests.RequestException as e:
                        logger.error(f"请求异常，第{doc_index+1}个文档尝试 {attempt + 1}: {e}")

                        # 最后一次尝试失败
                        if attempt == max_attempts - 1:
                            logger.error(f"第{doc_index+1}个文档经过 {max_attempts} 次尝试，文档嵌入仍然失败")
                            break

                # 更新进度条
                progress_bar.update(1)

                # 计算并显示预计剩余时间
                elapsed_time = time.time() - start_time
                avg_time_per_doc = elapsed_time / (doc_index + 1)
                remaining_time = avg_time_per_doc * (total_docs - (doc_index + 1))
                progress_bar.set_postfix({
                    '已用时间': f"{elapsed_time:.2f}s",
                    '预计剩余时间': f"{remaining_time:.2f}s"
                })

        return embeddings


    def faiss_retrieve(self, split_docs: List[Document]) -> (faiss.IndexFlatL2, List[dict]):
        """
        使用 faiss 构建索引并检索文档。

        Args:
            split_docs (List[Document]): 待检索的分块文档列表。

        Returns:
            faiss.IndexFlatL2: FAISS 索引对象。
            List[dict]: 包含文档元数据的列表。
        """
        # 嵌入计算
        document_embeddings = self.embed_documents(split_docs)
        vectors = np.array([item['vector'] for item in document_embeddings]) # 向量
        vectors = vectors.astype('float32')
        metadata = [item['metadata'] for item in document_embeddings]  # 元数据

        # 构建 FAISS 索引
        faiss_index = faiss.IndexFlatL2(vectors.shape[1])  # 使用 L2 距离
        faiss_index.add(vectors)  # 添加向量到索引
        return faiss_index, metadata

    def query_embedding(self, query: str) -> np.ndarray:
        """
        对查询进行嵌入计算。

        Args:
            query (str): 查询内容。

        Returns:
            np.ndarray: 查询向量。
        """
        payload = {
            "model": self.embedding_model_name,
            "input": query,
            "encoding_format": "float"
        }
        headers = {
            "Authorization": f"Bearer {self.embedding_api_key}",
            "Content-Type": "application/json"
        }
        for attempt in range(self.max_attempts):
            try:
                response = requests.request("POST", self.embedding_base_url, json=payload, headers=headers)
                if response.status_code == 200:
                    return response.json()["data"][0]["embedding"]
                else:
                    logger.error(f"查询嵌入失败，尝试 {attempt + 1}: 状态码 {response.status_code}")
            except requests.RequestException as e:
                logger.error(f"请求异常，尝试 {attempt + 1}: {e}")

    def similarity_retrieve(self, split_docs: List[Document], queries: List[str], top_k: int = 10) -> List[Document]:
        """
        基于查询内容检索最相关的文档。

        Args:
            split_docs (List[Document]): 分块文档列表。
            queries (list): 查询内容。
            top_k (int): 检索返回的文档数量。

        Returns:
            List[dict]: 检索结果，包含文本和元数据。
        """
        results = []
        faiss_index, metadata = self.faiss_retrieve(split_docs)
        for query in queries:
            query_vector = np.array(self.query_embedding(query)).reshape(1, -1).astype('float32')
            distances, indices = faiss_index.search(query_vector, top_k)
            results.append([split_docs[i] for i in indices[0]])
        if len(queries)>1:
            return self.rrf(results,top_k)
        return results[0]


    def similarity_retrieve_local(self, split_docs: List[Document], queries: List[str], top_k: int = 10) -> List[Document]:
        """
        使用本地embedding模型基于查询内容检索最相关的文档。

        Args:
            split_docs (List[Document]): 分块文档列表。
            queries (list): 查询内容。
            top_k (int): 检索返回的文档数量。

        Returns:
            List[dict]: 检索结果，包含文本和元数据。
        """
        results = []
        db = FAISS.from_documents(split_docs, self.embeddings)
        for query in queries:
            results.append(db.similarity_search(query,k=top_k))
        if len(queries)>1:
            return self.rrf(results,top_k)
        return results[0]

    def rrf(self,results: List[List[Document]],top_k: int = 10,m: int = 60):
        """
        使用BM25算法进行文本检索

        :param results: 不同查询检索的结果
        :param top_k: 返回的top-k结果数
        :param m: RRF 算法的平滑参数
        :return: 检索结果
        """

        doc_scores = {}  # 存储文档及其对应分数
        for result in results:
            for rank, doc in enumerate(result):
                content = doc.page_content
                if content not in doc_scores:
                    doc_scores[content] = {'doc': doc, 'score': 0}
                doc_scores[content]['score'] += 1 / (rank + m)
        sorted_results = [
            doc_data['doc'] for doc_data in sorted(doc_scores.values(), key=lambda x: x['score'], reverse=True)[:top_k]
        ]
        return sorted_results

    def similarity_retrieval(self, split_docs: List[Document], queries: List[str], top_k: int = 10) -> List[Document]:
        """
        相似度召回的主函数入口，根据配置文件选择使用云端embedding模型还是本地embedding模型

        Args:
            split_docs (List[Document]): 分块文档列表。
            queries (list): 查询内容。
            top_k (int): 检索返回的文档数量。

        Returns:
            List[dict]: 检索结果，包含文本和元数据。
        """
        if self.local:
            return self.similarity_retrieve_local(split_docs,queries,top_k)
        else:
            return self.similarity_retrieve(split_docs,queries,top_k)


class BM25():
    def __init__(self):
        pass

    def rrf(self,results: List[List[Document]],top_k: int=10,m: int=60) -> List[Document]:
        """
        使用BM25算法进行文本检索

        :param results: 不同查询检索的结果
        :param top_k: 返回的top-k结果数
        :param m: RRF 算法的平滑参数
        :return: 检索结果
        """
        doc_scores = {}  # 存储文档及其对应分数
        for result in results:
            for rank, doc in enumerate(result):
                content = doc.page_content
                if content not in doc_scores:
                    doc_scores[content] = {'doc': doc, 'score': 0}
                doc_scores[content]['score'] += 1 / (rank + m)
        sorted_results = [
            doc_data['doc'] for doc_data in sorted(doc_scores.values(), key=lambda x: x['score'], reverse=True)[:top_k]
        ]
        return sorted_results



    def bm25_retrieval(self,split_docs: List[Document], queries: List[str], top_k: int=10):
        """
        使用BM25算法进行文本检索

        :param split_docs: 预处理的文档列表
        :param queries: 查询文本
        :param top_k: 返回的top-k结果数
        :return: 检索结果
        """

        # 使用jieba对文本分词
        def preprocessing_func(text: str) -> List[str]:
            return list(jieba.cut(text))

        bm25_retriever = BM25Retriever.from_documents(split_docs, preprocess_func=preprocessing_func, k=top_k)
        results = []
        for query in queries:
            results.append(bm25_retriever.invoke(query))
        if len(queries)>1:
            return self.rrf(results,top_k)
        return results[0]


class Rerank():
    def __init__(self):
        """
        初始化 Rerank 类，从配置文件加载检索参数。
        """
        with open(r'./config/config.json', encoding='utf-8') as f:
            config = json.load(f)
        self.local = config['local_rerank_model']
        self.rerank_model = config['rerank_model']['cloud_rerank']['model_name']
        self.base_url = config['rerank_model']['cloud_rerank']['base_url']
        self.api_key = config['rerank_model']['cloud_rerank']['api_key']
        self.path = config['rerank_model']['local_rerank']['model_path']
        if self.local:
            self.model = HuggingFaceCrossEncoder(
                model_name=self.path,
                model_kwargs={'device': 'cuda:0'}
            )
            print('rerank模型初始化成功')



    def rerank_cloud(self,results: List[Document], query: str, k=10) -> List[Document]:
        """
        使用云端重排序模型模型对检索结果进行重排序

        :param results: 原始检索结果
        :param query: 查询
        :param k: 返回的top-k结果数
        :return: 重排序后的结果
        """
        texts = [item.page_content for item in results]

        url = self.base_url

        payload = {
            "model": self.rerank_model,
            "query": query,
            "documents": texts,
            "top_n": k,
            "return_documents": False,
            "max_chunks_per_doc": 1024,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = requests.request("POST", url, json=payload, headers=headers)
        try:
            if response.status_code == 200:
                response = response.json()
                indices = [item['index'] for item in response['results']]
                return [results[i] for i in indices]
        except:
            logger.error(f'Error:network error status_code={response.status_code}',exc_info=True)



    def rerank_local(self,results,query,k=10):
        """
        使用本地重排序模型模型对检索结果进行重排序

        :param results: 原始检索结果
        :param query: 查询
        :param k: 返回的top-k结果数
        :return: 重排序后的结果
        """

        compressor = CrossEncoderReranker(model=self.model, top_n=k)
        rerank_results = compressor.compress_documents(results,query)
        return rerank_results

    def rerank(self,results: List[Document],query: str,k: int = 10):
        """
        主重排序函数，根据配置选择重排序方法（使用本地模型还是云端模型）。

        :param results: 原始检索结果
        :param query: 查询
        :param k: 返回的top-k结果数
        :return: 重排序后的结果
        """
        if self.local:
            return self.rerank_local(results,query,k)
        else:
            return self.rerank_cloud(results,query,k)






