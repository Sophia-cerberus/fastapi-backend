from langchain.embeddings.base import Embeddings
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod


class EmbeddingsManager(ABC):
    """
    嵌入管理器基础类，负责处理文本的嵌入向量化
    """
    
    def __init__(self, embedding_model: Embeddings, config: Optional[Dict[str, Any]] = None):
        """
        初始化嵌入管理器
        
        :param embedding_model: LangChain 嵌入模型实例
        :param config: 配置字典
        """
        self.embedding_model = embedding_model
        self.config = config or {}
        
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """
        将单个文本转换为嵌入向量
        
        :param text: 输入文本
        :return: 嵌入向量列表
        """
        pass
    
    @abstractmethod
    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        批量将文档列表转换为嵌入向量
        
        :param documents: 文档列表
        :return: 嵌入向量列表的列表
        """
        pass
    
    @abstractmethod    
    async def aembed_text(self, text: str) -> List[float]:
        """
        异步将单个文本转换为嵌入向量
        
        :param text: 输入文本
        :return: 嵌入向量列表
        """
        pass
    
    @abstractmethod    
    async def aembed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        异步批量将文档列表转换为嵌入向量
        
        :param documents: 文档列表
        :return: 嵌入向量列表的列表 
        """
