from typing import List, Dict, Any, Optional 
from abc import ABC, abstractmethod 
from langchain.schema.document import Document 


class KnowledgeManager(ABC):
    """Agent知识管理基础类"""
   
    def __init__(self): 
        pass 
      
    @abstractmethod  
    async def retrieve_relevant_documents(
        self,
        query_texts: List[str],
        top_k: int=5,
        **kwargs      
    ) -> List[Document]:
        """检索与查询相关的文档"""
        
    @abstractmethod  
    async def add_documents(
        self,
        documents: List[Document],
        **kwargs     
    ) -> bool:
        """添加新文档到知识库"""  
        
    @abstractmethod  
    async def delete_documents(
        self,
        document_ids: List[str],
        **kwargs     
    ) -> bool:
        """从知识库删除文档"""  
        
    @property   
    @abstractmethod  
    async def document_count(self) -> int:
        """获取知识库中的文档数量"""   
        
    @property   
    @abstractmethod  
    async def metadata_fields(self) -> Dict[str,Dict]: 
        """获取知识库支持的元数据字段信息"""     