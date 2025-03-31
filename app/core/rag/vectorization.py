from langchain_community.document_loaders import (
    TextLoader,
    UnstructuredExcelLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredCSVLoader,
    UnstructuredPDFLoader,
)
from langchain_community.document_loaders.base import BaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.api.dependencies import SessionDep
from app.api.models import Upload, Document
from sentence_transformers import SentenceTransformer


model = SentenceTransformer("all-MiniLM-L6-v2")


# 支持不同类型文件的处理器
FILE_LOADERS = {
    "application/pdf": UnstructuredPDFLoader,  # PDF
    "application/msword": UnstructuredWordDocumentLoader,  # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": UnstructuredWordDocumentLoader,  # .docx
    "application/vnd.ms-powerpoint": UnstructuredPowerPointLoader,  # .ppt
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": UnstructuredPowerPointLoader,  # .pptx
    "application/vnd.ms-excel": UnstructuredExcelLoader,  # .xls
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": UnstructuredExcelLoader,  # .xlsx
    "text/plain": TextLoader,  # .txt
    "text/html": UnstructuredHTMLLoader,  # .html
    "text/markdown": UnstructuredMarkdownLoader,  # .md
    "text/csv": UnstructuredCSVLoader,  # .md
}


def get_loader(file_type: str):
    """
    根据 MIME 类型返回合适的 Loader 类
    """
    loader_class = FILE_LOADERS.get(file_type)
    if not loader_class:
        raise ValueError(f"Unsupported file type: {file_type}")
    return loader_class


async def chunk_to_vector(
    session: SessionDep, 
    buffer: bytearray, 
    file: Upload, 
    chunk_index: int
):
    
    loader_class = get_loader(file.file_type)
    
    loader = loader_class(buffer)
    documents = loader.load()
    
    # 文本分块
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=file.chunk_size, 
        chunk_overlap=file.chunk_overlap
    )

    split_docs = text_splitter.split_documents(documents)

    # 向量化并存入数据库
    for doc in split_docs:
        text_content = doc.page_content
        vector = model.encode(text_content).tolist()

        vector_entry = Document(
            upload_id=file.id,
            chunk_index=chunk_index,
            text_content=text_content,
            embedding=vector
        )
        session.add(vector_entry)
        chunk_index += 1

    await session.commit()
