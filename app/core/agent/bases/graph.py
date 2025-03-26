from typing import Dict, Any, Optional, Callable
from langgraph.graph import Graph
from abc import ABC, abstractmethod


class AgentGraph(ABC):
    """Agent工作流图基础使用LangGraph构建"""
    
    def __init__(self):
        self.graph = Graph()
        
    @abstractmethod  
    def define_nodes(self) -> Dict[str, Callable]:
        """定义图中的各个节点"""
        
    @abstractmethod  
    def define_edges(self) -> list:
        """定义节点之间的连接关系"""
        
    def compile(self) -> Graph:
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
