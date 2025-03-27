from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langgraph.graph.state import CompiledStateGraph
from sqlmodel import SQLModel
from typing import Dict, Any
from app.core.agent.bases.graph import AgentGraph as _AgentGraph
from app.core.agent.bases.tools.web_search import WebSearchTool
# from app.core.agent.bases.tools.db_retriever import DBRetrieverTool

from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END, START

router = APIRouter(prefix="/chat", tags=['chat'])


def setup_pdf_retriever(pdf_file_path: str):
    """Read a PDF file and setup an ensemble retriever"""

    pages = PyMuPDFLoader(file_path=pdf_file_path).load()
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=1000, chunk_overlap=100
    )
    docs = text_splitter.split_documents(pages)

    embeddings = OllamaEmbeddings(  
        model="mxbai-embed-large"  
    )
    vectorstore_faiss = FAISS.from_documents(docs, embeddings)
    faiss_retriever = vectorstore_faiss.as_retriever(
        search_kwargs={"k": 1}
    )  # dense search
    bm25_retriever = BM25Retriever.from_documents(docs)  # sparse search
    bm25_retriever.k = 1

    retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, faiss_retriever],
        weights=[0.5, 0.5],  # sum equals to 1
    )
    return retriever

basic_doc_path = "周宇-13293359750.pdf"  # YOUR PDF FILENAME HERE
retriever = setup_pdf_retriever(basic_doc_path)

local_llm = "deepseek-r1:8b"
llm = ChatOllama(model=local_llm, temperature=0)
prompt = PromptTemplate(  # Instruct in Enlgish, but force to generate in Korean
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|> You are an assistant for question-answering strictly based on context.
    Do not guess the answer. You must only use Context, not other information for answer. Only incude highly related information in Context. 
    Just say you don't know if you can't find related information in Context. 
    Answer only in Korean. <|eot_id|><|start_header_id|>user<|end_header_id|>
    \n Question: {question}
    \n Context: {context}
    \n Answer: <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
    input_variables=["context", "question"],
)
chain = prompt | llm | StrOutputParser()

def format_docs(docs):
    """Convert retrieved documents into str format"""
    return "\n\n".join(doc.page_content for doc in docs)


# 请求参数模型（改用 SQLModel）
class ChatRequest(SQLModel):
    model: str  # 选择的模型
    enable_web_search: bool = False  # 是否联网搜索
    enable_knowledge_retrieval: bool = False  # 是否启用知识库检索
    inference_mode: str = "default"  # 推理模式（如普通推理、深度推理等）
    inference_depth: int = 3  # 推理深度
    user_input: str  # 用户输入
    documents: str | None = None


# 动态推理流程集成 LangGraph
class AgentGraph(_AgentGraph):
    def __init__(self, request: ChatRequest):
        super().__init__()
        self.request = request

    def define_nodes(self) -> Dict[str, Any]:
        nodes = {"retrieve": self.parse_input, "generate": self.invoke_model}
        return nodes

    def define_edges(self) -> list:
        edges = [
             (START, "retrieve"),
             ("retrieve", "generate"),
             ("generate", END),
        ]
        return edges

    async def parse_input(self, state):
        """Retrieve documents based on user input."""
        print(state)
        question = state.get("user_input", "")
        docs = await retriever.ainvoke(question)  # 修正错误，使用异步方式
        state["documents"] = format_docs(docs) if docs else ""
        print("state", state['documents'])
        return state

    async def invoke_model(self, state):
        """Invoke LLM to generate response."""
        question = state.get("user_input", "")
        documents = state.get("documents", "")

        if not documents:
            state["generation"] = "죄송합니다. 관련 정보를 찾을 수 없습니다."  # "Sorry, no related information found."
            return state

        result = await chain.ainvoke({"context": documents, "question": question})
        state["generation"] = result
        print("generation", state['generation'])
        return state


# WebSocket 推理流程
async def inference_process(request: ChatRequest, websocket: WebSocket):
    agent = AgentGraph(request)
    compiled_graph: CompiledStateGraph = agent.compile()
    async for event in compiled_graph.astream_events({"user_input": request.user_input}):
        await websocket.send_json({"type": "event", "data": event})

    async for log in compiled_graph.astream_log({"user_input": request.user_input}):
        await websocket.send_json({"type": "log", "data": log})

    async for chunk in compiled_graph.astream({"user_input": request.user_input}):
        await websocket.send_json({"type": "generation", "data": chunk})


# WebSocket 端点
@router.websocket("/", name='chat')
async def chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while 1:
            data = await websocket.receive_json()
            request = ChatRequest(**data)
            await inference_process(request, websocket)
    except WebSocketDisconnect:
        await websocket.close()
