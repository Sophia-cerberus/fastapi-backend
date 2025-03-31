from langchain_community.document_loaders import PyMuPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from sqlmodel import Session
from models import VectorDocument


model = SentenceTransformer("all-MiniLM-L6-v2")

# 支持不同类型文件的处理器
FILE_LOADERS = {
    "application/pdf": PyMuPDFLoader,
    "text/plain": TextLoader,
}

def process_and_store_file(session: Session, file_name: str, file_chunks: list[bytes], file_type: str, upload_path: str):
    """
    处理 S3 文件数据，将文本提取后进行向量化并存储
    """
    loader_class = FILE_LOADERS.get(file_type)
    if not loader_class:
        raise ValueError(f"Unsupported file type: {file_type}")
    
    # 组合所有块
    full_content = b"".join(file_chunks)
    
    # 临时文件处理
    temp_file_path = f"/tmp/{file_name}"
    with open(temp_file_path, "wb") as f:
        f.write(full_content)
    
    loader = loader_class(temp_file_path)
    documents = loader.load()
    
    # 文本分块
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = text_splitter.split_documents(documents)

    # 向量化并存入数据库
    for idx, doc in enumerate(split_docs):
        text_content = doc.page_content
        vector = model.encode(text_content).tolist()
        
        vector_entry = VectorDocument(
            file_name=file_name,
            file_path=upload_path,
            chunk_index=idx,
            text_content=text_content,
            embedding=vector
        )
        session.add(vector_entry)
    
    session.commit()