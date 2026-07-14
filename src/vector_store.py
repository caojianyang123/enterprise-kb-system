import os
import shutil
from typing import List, Tuple
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from config import Config

class VectorStoreManager:
    """向量存储管理器，负责向量的存储、检索和管理"""
    
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=Config.CHROMA_DB_PATH,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        self.collection_name = "enterprise_kb"
        self._init_collection()
    
    def _init_collection(self):
        """初始化向量集合，若不存在则创建"""
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
    
    def add_documents(self, doc_id: int, chunks: List[str], filename: str):
        """
        添加文档向量到向量库
        :param doc_id: 文档ID
        :param chunks: 文本块列表
        :param filename: 文件名
        """
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [{
            "doc_id": doc_id,
            "filename": filename,
            "chunk_index": i
        } for i in range(len(chunks))]
        
        self.collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
    
    def search(self, query: str, top_k: int = None) -> List[dict]:
        """
        语义检索，根据查询词查找相关文档
        :param query: 查询词
        :param top_k: 返回数量，默认为配置值
        :return: 检索结果列表
        """
        k = top_k or Config.TOP_K
        
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )
        
        return self._format_results(results)
    
    def _format_results(self, results: dict) -> List[dict]:
        """
        格式化检索结果
        :param results: 原始检索结果
        :return: 格式化后的结果列表
        """
        formatted = []
        for i in range(len(results["ids"][0])):
            formatted.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })
        return formatted
    
    def delete_by_doc_id(self, doc_id: int):
        """
        根据文档ID删除相关向量
        :param doc_id: 文档ID
        """
        results = self.collection.get(
            where={"doc_id": doc_id}
        )
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
    
    def get_collection_stats(self) -> dict:
        """
        获取集合统计信息
        :return: 统计信息字典
        """
        stats = self.collection.count()
        return {
            "total_documents": stats,
            "collection_name": self.collection_name
        }
    
    def reset_collection(self):
        """重置向量集合（清空所有数据）"""
        self.client.delete_collection(self.collection_name)
        self._init_collection()