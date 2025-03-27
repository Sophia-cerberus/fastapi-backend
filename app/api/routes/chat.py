import asyncio
import json
from typing import TypedDict, List, Optional, Dict, Any, AsyncIterator
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain.schema import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph

router = APIRouter(prefix="/chat", tags=['chat'])

class AgentState(TypedDict):
    messages: List[dict]
    current_stage: str
    search_details: Dict[str, Any]
    stage_details: Dict[str, Any]

async def research_agent(state: AgentState) -> AgentState:
    state["current_stage"] = "检索"
    query = state["messages"][-1]["content"]
    llm = ChatOllama(model="deepseek-r1:8b", temperature=0.7)
    messages = [SystemMessage(content="介绍输出关键词"), HumanMessage(content=query)]
    response = llm.astream(messages)
    state["search_details"] = {"analysis": response}
    return state

async def reflection_agent(state: AgentState) -> AgentState:
    state["current_stage"] = "批判"
    llm = ChatOllama(model="deepseek-r1:8b", temperature=0.7)
    
    content = state["search_details"]["analysis"]
    content_str = ""
    async for chunk in content:
        content_str += chunk
    
    print(2222, content_str, content)
    messages = [SystemMessage(content="你是一个批判专家，如果输入不完美,给出意见"), HumanMessage(content=content_str)]
    response = llm.astream(messages)
    state["stage_details"] = {"analysis": response}
    return state

async def finalize_response(state: AgentState) -> AgentState:
    state["current_stage"] = "结束"
    final_text = f"最终回答: {state["stage_details"]["analysis"]}"
    state["messages"].append({"type": "ai", "content": final_text})
    return state

workflow = StateGraph(AgentState)
workflow.add_node("research", research_agent)
workflow.add_node("reflection", reflection_agent)
workflow.add_node("finalize", finalize_response)
workflow.set_entry_point("research")
workflow.add_edge("research", "reflection")
workflow.add_edge("reflection", "finalize")
graph = workflow.compile()


@router.post("/")
async def advanced_chat_endpoint(message: str):
    initial_state = {"messages": [{"type": "human", "content": message}], "current_stage": "init", "stage_details": {}, "research_data": None}
    async def generate_stream() -> AsyncIterator[str]:
        async for step_output in graph.astream(initial_state):
            print(step_output)
            value = list(step_output.values())[0]
            stage = value.get("current_stage", "unknown")
            
            yield json.dumps({"stage": stage, "token": "", "status": "starting", "result": False}, ensure_ascii=False) + "\n"
            
            if detail := value['search_details'].get('analysis', None):
                async for chunk in detail:
                    yield chunk.content

            if detail := value['stage_details'].get('analysis', None):
                async for chunk in detail:
                    yield chunk.content
            
            yield  "\n" + json.dumps({"stage": stage, "token": "", "status": "ending", "result": stage == "结束"}, ensure_ascii=False) + "\n\n"
    return StreamingResponse(generate_stream(), media_type='text/event-stream')
