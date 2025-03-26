from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from langchain.vectorstores import VectorStore
from langchain.embeddings.base import Embeddings
from langchain.schema import Document
from langchain.retrievers import BaseRetriever
from datetime import datetime
import time
import json


# 配置日志记录
class DatabaseRetrieverConfig(BaseModel):
    """数据库检索器配置模型"""
    embedding_model: Any = Field(..., description="嵌入模型实例")
    vector_store: Any = Field(..., description="向量存储实例")
    top_k: int = Field(5, description="返回的最相关文档数量", gt=0)
    score_threshold: Optional[float] = Field(None, description="相似度分数阈值", ge=0, le=1)
    metadata_filter: Optional[Dict[str, Any]] = Field(None, description="元数据过滤条件")
    
    @field_validator('top_k')
    def validate_top_k(cls, v):
        if v <= 0:
            raise ValueError("top_k 必须大于0")
        return v


class DatabaseRetrieverMetrics(BaseModel):
    """检索性能指标"""
    query_count: int = 0
    avg_response_time: float = 0.0
    success_count: int = 0
    error_count: int = 0


class DatabaseRetriever(BaseRetriever):
    """
    专业化的数据库检索工具类
    
    特性:
    1. 支持多种向量存储后端 (FAISS, Chroma, Pinecone等)
    2. 可配置的相似度阈值和结果数量限制
    3. 元数据过滤支持
    4. 性能监控和指标收集
    5. 完善的错误处理
    
    使用方法:
    >>> retriever = DatabaseRetriever(config)
    >>> results = retriever.get_relevant_documents("查询文本")
    """
    
    def __init__(self, config: DatabaseRetrieverConfig):
        super().__init__()
        self.config = config
        self.metrics = DatabaseRetrieverMetrics()
        self._validate_components()
        
    def _validate_components(self) -> None:
        """验证嵌入模型和向量存储是否有效"""
        if not isinstance(self.config.embedding_model, Embeddings):
            raise TypeError("embedding_model must be an instance of Embeddings")
        
        if not isinstance(self.config.vector_store, VectorStore):
            raise TypeError("vector_store must be an instance of VectorStore")
    
    def get_relevant_documents(self, query: str) -> List[Document]:
        """
        执行文档检索
        
        参数:
            query (str): 查询文本
            
        返回:
            List[Document]: 相关文档列表
            
        异常:
            RetrievalError: 当检索过程中发生错误时抛出
        """
        start_time = time.time()
        
        try:
            # 执行相似性搜索，带可选分数阈值和元数据过滤
            docs_and_scores = self.config.vector_store.similarity_search_with_score(
                query=query,
                k=self.config.top_k,
                filter=self.config.metadata_filter,
                score_threshold=self.config.score_threshold,
                embeddings=self.config.embedding_model,
            )
            
            # Process results and log metadata without the embeddings to save space in logs 
            processed_results = []
            for doc in docs_and_scores:
                processed_doc_data = {
                    "page_content": doc[0].page_content[:100] + "..." if len(doc[0].page_content) > 100 else doc[0].page_content,
                    "metadata": doc[0].metadata,
                    "score": doc[1]
                }
                processed_results.append(processed_doc_data)
            
            # Update metrics for successful operation 
            duration_ms = (time.time() - start_time) * 1000
            
            self.metrics.query_count +=1 
            self.metrics.success_count +=1 
            
            # Calculate rolling average response time 
            previous_total_time= ( self.metrics.query_count - 1 ) * self.metrics.avg_response_time  
            self.metrics.avg_response_time=( previous_total_time + duration_ms ) / self.metrics.query_count  
            
            return [doc for doc,_ in docs_and_scores]   
             
        except Exception as e :
            self.metrics.error_count +=1  
            error_msg=f"Error retrieving documents for query '{query}': {str(e)}"
            raise RetrievalError(error_msg ) from e  

    async def aget_relevant_documents(self ,query :str )->List [Document ] :
        """异步版本获取相关文档"""  
        # Implement async version here using appropriate async methods from vector store  
        raise NotImplementedError ("Async retrieval not yet implemented ")  

    def add_documents(self ,documents :List [Document ], **kwargs )->None :  
        """向向量存储添加新文档"""  
        try :  
            start_time=time .time ()  
            self .config .vector_store .add_documents (documents ,**kwargs )  

            duration_ms=(time .time ()-start_time )*1000  
            # logger .info (f"Added {len(documents)} documents in {duration_ms:.2f}ms")  

        except Exception as e :  
            error_msg=f"Failed to add documents:{str(e)}"  
            # logger .error (error_msg ,exc_info=True )  

    def get_metrics_report(self)->dict :   
        """获取当前性能指标报告"""   
        return {   
            "timestamp":datetime.now().isoformat(),   
            "total_queries":self.metrics.query_count ,   
            "success_rate":f"{100*self.metrics.success_count/max(1 ,self.metrics.query_count):.1f}%" ,   
            "average_response_time_ms":round(self.metrics .avg_response_time ,2 ),   
            "errors":self.metrics.error_count }   


class RetrievalError(Exception):     
      """自定义检索异常类"""     
      pass 

# Example usage     
if __name__=="__main__":     
    from langchain.embeddings.openai import OpenAIEmbeddings     
    from langchain.vectorstores import FAISS      

    # Initialize components      
    embeddings=OpenAIEmbeddings(model="text-embedding-ada-002")      
    documents=[Document(page_content="LangChain is a framework for building LLM applications",metadata={"source":"docs"})]      
    vectorstore=FAISS.from_documents(documents ,embeddings )      

    # Create retriever      
    config=DatabaseRetrieverConfig(      
        embedding_model=embeddings ,      
        vector_store=vectorstore ,      
        top_k=3 ,      
        score_threshold=None       
    )      

    retriever=DatabaseRetriever(config)       
    
    try :       
        results = retriever.get_relevant_documents("What is LangChain?")       
        print(f"Retrieved {len(results)} documents")       
        
        metrics_report = retriever.get_metrics_report()       
        print("\nPerformance Metrics:\n"+json.dumps(metrics_report ,indent=2 ))       
        
    except RetrievalError as e :       
        print(f"Error during retrieval:{e}")       
