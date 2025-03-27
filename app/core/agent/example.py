from typing import TypedDict
from langchain_ollama import ChatOllama
from langchain.schema import SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

# 定义状态类
class AgentState(TypedDict):
    messages: list

# 定义智能体节点
def agent_node(state: AgentState):
    local_llm = "deepseek-r1:8b"
    llm = ChatOllama(model=local_llm, temperature=0)
    response = llm.astream(([SystemMessage(content="你是一个智能助手。")] + state['messages']))
    state["messages"].append(response)
    return state

# 构建有向图
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.set_entry_point("agent")
workflow.add_edge("agent", END)

graph: CompiledStateGraph = workflow.compile()
