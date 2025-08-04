# -*- coding: utf-8 -*-
import json
import time
from typing import List, Dict, Any, Optional, Tuple
import jieba
import numpy as np
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import chromadb
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from tqdm import tqdm
from langchain.retrievers.document_compressors.cross_encoder_rerank import CrossEncoderReranker
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# Import the config manager
from .config_manager import config

logger = logging.getLogger(__name__)

# ... split_doc_direct 函数保持不变 ...
def split_doc_direct(documents: List[Dict[str, Any]]) -> List[Document]:
    """
    将输入文档拆分为更小的文本块，便于后续检索和处理

    :param documents: 原始文档列表，每个文档包含text和title
    :return: 拆分后的文档列表
    """
    # 将输入文档转换为Langchain的Document对象
    langchain_docs = [Document(
        page_content=item.get('content', '') ,
        metadata={'url': item.get('link', ''),
        'title': item.get('title', '')}
    ) for item in documents]

    # 递归字符拆分器
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=256,
        chunk_overlap=32,
        separators=["\n\n", "\n", "。", ".", "？", "?", "！", "!", ";", '，', ','],
        strip_whitespace=True
    )

    # 执行文本拆分
    split_docs = text_splitter.split_documents(langchain_docs)
    return split_docs


class Similarity():
    """
    文本相似度检索和嵌入处理类。
    - 云端模式使用并发请求和批量处理进行优化。
    - 底层向量数据库已从 FAISS 替换为 Chroma。
    - 提供多种相似度检索方法。
    """

    def __init__(self):
        """
        从 ConfigManager 加载嵌入模型相关配置。
        """
        # Load config from the manager
        self.embedding_model_name = config.get('embedding_model_name')
        self.embedding_api_key = config.get('embedding_api_key')
        self.embedding_base_url = config.get('embedding_base_url')

        if not all([self.embedding_model_name, self.embedding_api_key, self.embedding_base_url]):
            raise ValueError("Cloud embedding model configuration is incomplete. Please check your settings.")

        # New optimization parameters, defined directly as requested
        self.API_MAX_BATCH_SIZE = 10
        self.batch_size = self.API_MAX_BATCH_SIZE
        self.max_workers = min(self.batch_size, (os.cpu_count() or 1) + 4)
        self.max_retries = 3
        self.request_timeout = 30  # seconds

        # Session for connection pooling and robust retries for cloud mode
        self.session = requests.Session()
        retries = Retry(
            total=self.max_retries,
            backoff_factor=1,  # Will sleep for {1, 2, 4} seconds between retries
            status_forcelist=[429, 500, 502, 503, 504]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.session.headers.update({
            "Authorization": f"Bearer {self.embedding_api_key}",
            "Content-Type": "application/json"
        })

    # embed_documents 和 _embed_batch_cloud 方法保持不变
    def _embed_batch_cloud(self, batch_of_texts: List[str]) -> Optional[List[List[float]]]:
        """Embeds a batch of texts using the cloud API with retry logic."""
        payload = {
            "model": self.embedding_model_name,
            "input": batch_of_texts,
            "encoding_format": "float"
        }
        try:
            assert self.embedding_base_url is not None
            response = self.session.post(self.embedding_base_url, json=payload, timeout=self.request_timeout)
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
            data = response.json()["data"]
            data.sort(key=lambda x: x['index'])  # Ensure original order is restored
            return [item["embedding"] for item in data]
        except requests.exceptions.RequestException as e:
            logger.error(f"Batch embedding request failed after all retries: {e}")
            return None
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse API response: {e}. Response text: {response.text if 'response' in locals() else 'N/A'}")
            return None

    def embed_documents(self, split_docs: List[Document]) -> List[Dict[str, Any]]:
        """
         Generates embeddings for all documents efficiently using concurrency and batching.
        """
        texts_to_embed = [doc.page_content for doc in split_docs]
        batches = [texts_to_embed[i:i + self.batch_size] for i in range(0, len(texts_to_embed), self.batch_size)]

        all_embeddings: List[Optional[List[float]]] = [None] * len(split_docs)
        logger.info(f"Starting cloud embedding for {len(split_docs)} documents in {len(batches)} batches...")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_start_index = {
                executor.submit(self._embed_batch_cloud, batch): i * self.batch_size
                for i, batch in enumerate(batches)
            }
            with tqdm(total=len(split_docs), desc="Cloud Document Embedding", unit="doc") as pbar:
                for future in as_completed(future_to_start_index):
                    start_index = future_to_start_index[future]
                    try:
                        batch_embeddings = future.result()
                        if batch_embeddings:
                            batch_len = len(batch_embeddings)
                            for i in range(batch_len):
                                all_embeddings[start_index + i] = batch_embeddings[i]
                            pbar.update(batch_len)
                        else:
                            failed_batch_size = min(self.batch_size, len(split_docs) - start_index)
                            logger.error(f"Batch starting at index {start_index} failed embedding.")
                            pbar.update(failed_batch_size)
                    except Exception as exc:
                        logger.critical(f"An exception was generated by an embedding task: {exc}", exc_info=True)

        results = []
        successful_count = 0
        for i, vector in enumerate(all_embeddings):
            if vector is not None:
                doc = split_docs[i]
                results.append({'vector': vector, 'metadata': doc.metadata, 'page_content': doc.page_content})
                successful_count += 1

        logger.info(f"Embedding complete. Successfully embedded {successful_count}/{len(split_docs)} documents.")
        if successful_count == 0 and len(split_docs) > 0:
            raise RuntimeError("All document embeddings failed. Check API key, URL, and network connection.")
        return results

    # ------------------ 修正后的数据库构建逻辑 ------------------

    def build_chroma_store(self, split_docs: List[Document]) -> Tuple[Optional[Chroma], List[Document]]:
        """
        使用预嵌入的向量和文档构建一个Chroma向量存储（修正版）。
        """
        # 1. 嵌入文档，逻辑保持不变
        document_embeddings = self.embed_documents(split_docs)
        if not document_embeddings:
            logger.warning("No documents were successfully embedded. Cannot build Chroma store.")
            return None, []

        # 2. 准备建库所需的数据
        #    这满足了您“元数据文档务必是indexed_docs”的要求
        vectors = [item['vector'] for item in document_embeddings]
        page_contents = [item['page_content'] for item in document_embeddings]
        metadatas = [item['metadata'] for item in document_embeddings]
        # Chroma 需要一个唯一的字符串ID列表
        ids = [str(i) for i in range(len(page_contents))]
        
        # 将成功嵌入的文档重新包装为 Document 对象，以保持返回签名一致
        indexed_docs = [
            Document(page_content=item['page_content'], metadata=item['metadata'])
            for item in document_embeddings
        ]

        logger.info(f"Building Chroma store with {len(indexed_docs)} vectors...")

        try:
            # 3. **正确流程**：创建客户端和集合，然后添加数据
            # 创建一个临时的内存客户端
            client = chromadb.Client()
            # 创建一个集合，如果已存在则获取它
            collection = client.get_or_create_collection(name="retrieval_collection")

            # 将向量、文档、元数据和ID添加到集合中
            collection.add(
                embeddings=vectors,
                documents=page_contents,
                metadatas=metadatas,
                ids=ids
            )

            # 4. **正确流程**：实例化 LangChain 的 Chroma 包装器以进行后续查询
            # 注意：因为我们是手动添加数据并使用向量查询，所以这里不需要 embedding_function
            chroma_store = Chroma(
                client=client,
                collection_name="retrieval_collection",
                embedding_function=None # 明确设为 None
            )

            logger.info("Chroma store built successfully.")
            return chroma_store, indexed_docs
            
        except Exception as e:
            logger.error(f"Failed to build Chroma store: {e}", exc_info=True)
            return None, []


    def query_embedding(self, query: str) -> Optional[np.ndarray]:
        """ Embeds a single query string."""
        response = self._embed_batch_cloud([query])
        if response:
            return np.array(response[0], dtype='float32')
        return None

    def similarity_retrieve(self, split_docs: List[Document], queries: List[str], top_k: int = 10) -> List[List[Document]]:
        """ Retrieves the most relevant documents based on query content using Chroma."""
        results = []
        # 调用新的、修正后的方法构建 Chroma store
        # indexed_docs 在这里不是必须的，因为信息已存入chroma_store，但为了保持签名一致性而接收它
        chroma_store, _ = self.build_chroma_store(split_docs)

        if chroma_store is None:
            logger.error("Chroma store is not available. Cannot perform retrieval.")
            return []

        for query in queries:
            query_vector = self.query_embedding(query)
            if query_vector is None:
                logger.warning(f"Query '{query}' embedding failed, skipping retrieval for this query.")
                continue

            # 使用 Chroma 的 similarity_search_by_vector 方法进行查询
            retrieved_docs = chroma_store.similarity_search_by_vector(
                embedding=query_vector.tolist(),
                k=top_k
            )
            results.append(retrieved_docs)

        return results


    def rrf(self, results: List[List[Document]], top_k: int = 10, m: int = 60) -> List[Document]:
        doc_scores = {}
        for result_list in results:
            for rank, doc in enumerate(result_list):
                content = doc.page_content
                if content not in doc_scores:
                    doc_scores[content] = {'doc': doc, 'score': 0}
                doc_scores[content]['score'] += 1 / (rank + m)

        sorted_results = [
            doc_data['doc'] for doc_data in sorted(doc_scores.values(), key=lambda x: x['score'], reverse=True)[:top_k]
        ]
        return sorted_results



class BM25():

    def __init__(self):

        pass
    def rrf(self, results: List[List[Document]], top_k: int = 10, m: int = 60) -> List[Document]:
        doc_scores = {}
        for result_list in results:
            for rank, doc in enumerate(result_list):
                content = doc.page_content
                if content not in doc_scores:
                    doc_scores[content] = {'doc': doc, 'score': 0}
                doc_scores[content]['score'] += 1 / (rank + m)

        sorted_results = [
            doc_data['doc'] for doc_data in sorted(doc_scores.values(), key=lambda x: x['score'], reverse=True)[:top_k]
        ]
        return sorted_results

    def bm25_retrieval(self, split_docs: List[Document], queries: List[str], top_k: int = 10):
        def preprocessing_func(text: str) -> List[str]:
            return list(jieba.cut(text))

        # 使用BM25Retriever
        bm25_retriever = BM25Retriever.from_documents(
            documents=split_docs,
            preprocess_func=preprocessing_func,
            k=top_k
        )
        bm25_results = bm25_retriever.get_relevant_documents(queries[0])
        return bm25_results


class Rerank():

    def __init__(self):
        self.rerank_model_name = config.get('rerank_model_name')
        self.rerank_api_key = config.get('rerank_api_key')
        self.rerank_base_url = config.get('rerank_base_url')

        if not all([self.rerank_model_name, self.rerank_api_key, self.rerank_base_url]):
            raise ValueError("Rerank model configuration is incomplete. Please check your settings.")

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
            "Authorization": f"Bearer {self.rerank_api_key}",
            "Content-Type": "application/json"
        })

    def _rerank_batch_cloud(self, documents: List[str], query: str, top_k: int) -> Optional[List[Dict]]:
        payload = {
            "model": self.rerank_model_name,
            "query": query,
            "documents": documents,
            "top_n": top_k,
            "return_documents": False
        }
        try:
            assert self.rerank_base_url is not None
            response = self.session.post(self.rerank_base_url, json=payload, timeout=self.request_timeout)
            response.raise_for_status()
            return response.json().get("results")
        except requests.exceptions.RequestException as e:
            logger.error(f"Rerank request failed after retries: {e}")
            return None
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse rerank API response: {e}")
            return None

    def rerank_cloud(self, results: List[Document], query: str, k=10) -> List[Document]:
        if not results:
            return []

        doc_contents = [doc.page_content for doc in results]

        reranked_results = self._rerank_batch_cloud(doc_contents, query, top_k=k)

        if reranked_results is None:
            logger.warning("Reranking failed, returning original top-k results.")
            return results[:k]

        final_docs = []
        for res in sorted(reranked_results, key=lambda x: x['relevance_score'], reverse=True):
            original_index = res.get('index')
            if original_index is not None and 0 <= original_index < len(results):
                final_docs.append(results[original_index])

        return final_docs[:k]



    def rerank(self, results: List[Document], query: str, k: int = 10) -> List[Document]:
        return self.rerank_cloud(results, query, k)