import logging
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    TextLoader,
    UnstructuredExcelLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader,
    WebBaseLoader,
)
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

def load_and_split_document(
    file_path: str,
    user_id: int,
    upload_id: int,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[Document]:
    """
    从指定文件路径或URL加载文档，更新元数据，并将文档拆分为多个块。

    Args:
        file_path (str): 本地文件路径或网页URL。
        user_id (int): 上传用户ID，用于更新文档元数据。
        upload_id (int): 上传记录ID，用于更新文档元数据。
        chunk_size (int, optional): 文本块最大长度。默认为500字符。
        chunk_overlap (int, optional): 文本块之间的重叠字符数。默认为50字符。

    Returns:
        list[Document]: 拆分后的文档块列表。

    Raises:
        ValueError: 当文件类型不受支持时抛出异常。
    """
    logger.debug(f"Loading document from: {file_path}")

    # 判断文件来源，选择合适的加载器
    if file_path.startswith("http://") or file_path.startswith("https://"):
        loader = WebBaseLoader(web_path=file_path)
    else:
        if file_path.endswith(".pdf"):
            loader = PyMuPDFLoader(file_path)
        elif file_path.endswith(".docx"):
            loader = UnstructuredWordDocumentLoader(file_path)
        elif file_path.endswith(".pptx"):
            loader = UnstructuredPowerPointLoader(file_path)
        elif file_path.endswith(".xlsx"):
            loader = UnstructuredExcelLoader(file_path)
        elif file_path.endswith(".txt"):
            loader = TextLoader(file_path)
        elif file_path.endswith(".html"):
            loader = UnstructuredHTMLLoader(file_path)
        elif file_path.endswith(".md"):
            loader = UnstructuredMarkdownLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")

    # 加载文档
    documents = loader.load()
    logger.debug(f"Loaded {len(documents)} documents")

    # 更新每个文档的元数据
    for doc in documents:
        doc.metadata.update({"user_id": user_id, "upload_id": upload_id})

    # 使用递归字符文本分割器拆分文档
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    split_docs = text_splitter.split_documents(documents)
    logger.debug(f"Split into {len(split_docs)} chunks")
    
    return split_docs
