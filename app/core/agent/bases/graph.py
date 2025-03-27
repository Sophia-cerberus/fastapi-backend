from typing import Dict, Any, Optional, Callable
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from abc import ABC, abstractmethod

from sqlmodel import SQLModel


class ChatRequest(SQLModel):
    model: str  # 选择的模型
    enable_web_search: bool = False  # 是否联网搜索
    enable_knowledge_retrieval: bool = False  # 是否启用知识库检索
    inference_mode: str = "default"  # 推理模式（如普通推理、深度推理等）
    inference_depth: int = 3  # 推理深度
    user_input: str  # 用户输入
    documents: str | None = None


class AgentGraph(ABC):
    """Agent工作流图基础使用LangGraph构建"""
    
    def __init__(self):
        self.graph = StateGraph(ChatRequest)
        
    @abstractmethod  
    def define_nodes(self) -> Dict[str, Callable]:
        """定义图中的各个节点"""
        
    @abstractmethod  
    def define_edges(self) -> list:
        """定义节点之间的连接关系"""
        
    def compile(self) -> CompiledStateGraph:
        """编译工作流图"""
        nodes = self.define_nodes()
        edges = self.define_edges()
       
        for node_name, node_func in nodes.items():
           self.graph.add_node(node_name, node_func)
           
        for edge in edges:
            if len(edge) == 2:
                src_node_name, dst_node_name = edge 
                self.graph.add_edge(src_node_name, dst_node_name)
            else:
                src_node_name, dst_node_name_or_dict = edge 
                if isinstance(dst_node_name_or_dict, dict):
                    self.graph.add_conditional_edges(
                        src_node_name,
                        dst_node_name_or_dict["condition"],
                        dst_node_name_or_dict["mapping"]
                   )
                else:
                    raise ValueError("Invalid edge definition")
                    
        # Add entry point if specified by subclass            
        if hasattr(self.__class__, "ENTRY_POINT"):
            self.graph.set_entry_point(getattr(self.__class__, "ENTRY_POINT"))
        
        return self.graph.compile()
    
   
    @property   
    def compiled_graph(self):
        """获取已编译的工作流图"""
        if not hasattr(self.__class__, "_compiled_graph"):
            setattr(self.__class__, "_compiled_graph", self.compile())
            
        return getattr(self.__class__, "_compiled_graph")
