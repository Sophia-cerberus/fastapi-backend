import copy
import os
from typing import Any, AsyncGenerator
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
    TextLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader
)
from langchain_community.document_loaders.base import BaseLoader 
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings

from app.api.models import Embedding, Upload
from app.core.config import settings


# 支持不同类型文件的处理器
FILE_LOADERS: dict[str, type[BaseLoader]] = {
    "application/pdf": PyMuPDFLoader,
    "application/msword": UnstructuredWordDocumentLoader,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": UnstructuredWordDocumentLoader,
    "application/vnd.ms-powerpoint": UnstructuredPowerPointLoader,
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": UnstructuredPowerPointLoader,
    "application/vnd.ms-excel": UnstructuredExcelLoader,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": UnstructuredExcelLoader,
    "text/plain": TextLoader,
    "text/html": UnstructuredHTMLLoader,
    "text/markdown": UnstructuredMarkdownLoader,
}


def get_loader(file_type: str) -> BaseLoader:
    """
    根据 MIME 类型返回合适的 Loader 类
    """
    loader_class = FILE_LOADERS.get(file_type)
    if not loader_class:
        raise ValueError(f"Unsupported file type: {file_type}")
    return loader_class


async def file_to_embeddings(
    file: Upload, 
    embeddings: OllamaEmbeddings = OllamaEmbeddings(model="mxbai-embed-large")
) -> AsyncGenerator[Embedding, Any]:
    

    bucket_name: str = settings.AWS_S3_BUCKET_NAME
    endpoint_url: str = settings.AWS_S3_ENDPOINT_URL
    remote_path: str = file.file_path

    file_path: str = os.path.join(endpoint_url, bucket_name, remote_path)

    loader_class: type[BaseLoader] = get_loader(file.file_type)
    loader = loader_class(file_path)
    documents = loader.alazy_load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=file.chunk_size,
        chunk_overlap=file.chunk_overlap,
    )

    async for doc in documents:
        text = doc.page_content
        metadata = doc.metadata or {}

        index = 0
        previous_chunk_len = 0

        for chunk in text_splitter.split_text(text):

            chunk = chunk.replace("\x00", "")

            metadata = copy.deepcopy(metadata)
            offset = index + previous_chunk_len - text_splitter._chunk_overlap
            index = text.find(chunk, max(0, offset))
            metadata["start_index"] = index
            previous_chunk_len = len(chunk)

            embedding = Embedding.model_validate({
                "embedding": embeddings.embed_documents([chunk])[0],
                "document": chunk,
                "cmetadata": metadata,
                "upload_id": file.id,
            })
            yield embedding
