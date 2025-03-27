from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlmodel import SQLModel
from typing import List, Dict, Any
import yaml
from app.api.deps import CurrentUser
from app.core.agent.bases.graph import AgentGraph as _AgentGraph
from app.core.agent.bases.tools.web_search import WebSearchTool
# from app.core.agent.bases.tools.db_retriever import DBRetrieverTool


router = APIRouter(prefix="/chat", tags=['chat'])


# 请求参数模型（改用 SQLModel）
class ChatRequest(SQLModel):
    model: str  # 选择的模型
    enable_web_search: bool = False  # 是否联网搜索
    enable_knowledge_retrieval: bool = False  # 是否启用知识库检索
    inference_mode: str = "default"  # 推理模式（如普通推理、深度推理等）
    inference_depth: int = 3  # 推理深度
    user_input: str  # 用户输入


# WebSocket 连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: Dict[str, Any], websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()


# 读取并加载推理节点配置
with open("config/inference_nodes.yaml", "r", encoding="utf-8") as f:
    INFERENCE_NODES_CONFIG = yaml.safe_load(f)["nodes"]


# 动态推理流程集成 LangGraph
class AgentGraph(_AgentGraph):
    def __init__(self, request: ChatRequest):
        super().__init__()
        self.request = request

    def define_nodes(self) -> Dict[str, Any]:
        nodes = {"parse_input": self.parse_input, "invoke_model": self.invoke_model}
        for node_name, config in INFERENCE_NODES_CONFIG.items():
            if getattr(self.request, config["flag"], False):
                nodes[node_name] = getattr(self, config["method"])
        return nodes

    def define_edges(self) -> list:
        edges = [("parse_input", "invoke_model")]
        for node_name, config in INFERENCE_NODES_CONFIG.items():
            if getattr(self.request, config["flag"], False):
                edges.append(("parse_input", node_name))
        return edges

    async def parse_input(self, data):
        return {"parsed": data["user_input"]}

    async def invoke_model(self, data):
        return {"response": f"模型输出: {data['parsed']}"}

    async def web_search(self, data):
        tool = WebSearchTool()
        result = tool.search(data["parsed"])
        return {"web_search_result": result}

    async def knowledge_retrieval(self, data):
        # tool = DBRetrieverTool()
        # result = tool.retrieve(data["parsed"])
        result = ""
        return {"knowledge_result": result}


# WebSocket 推理流程
async def inference_process(request: ChatRequest, websocket: WebSocket):
    agent = AgentGraph(request)
    compiled_graph = agent.compile()
    result = await compiled_graph.invoke({"user_input": request.user_input})
    await manager.send_message(result, websocket)


# WebSocket 端点
@router.websocket("/")
async def chat_endpoint(websocket: WebSocket, current_user: CurrentUser):
    # await manager.connect(websocket)
    await websocket.accept()
    try:
        while 1:
            data = await websocket.receive_json()
            request = ChatRequest(**data)
            await inference_process(request, websocket)
    except WebSocketDisconnect:
        await websocket.close()
        # manager.disconnect(websocket)

