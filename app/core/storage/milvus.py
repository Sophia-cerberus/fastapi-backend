from typing import List, Optional, Dict, Any
from pymilvus import AsyncMilvusClient, DataType, CollectionSchema, FieldSchema
import asyncio
from functools import wraps

from app.utils.logger import get_logger
from app.core.config import settings


logger = get_logger(__name__)


def with_retry(
    max_retries: int = settings.MILVUS_MAX_RETRIES, 
    delay: float = settings.MILVUS_RETRY_DELAY
):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
                        await logger.warning(f"Retrying {func.__name__} after error: {str(e)}")
                    else:
                        await logger.error(f"Failed after {max_retries} attempts: {str(e)}")
            # 最后一次异常直接抛出
            raise last_exception
        return wrapper
    return decorator


class MilvusClient:
    """Milvus 客户端类"""
    
    def __init__(self, collection_name: str):
        self._validate_settings()
        self.client = self._create_client()
        self._initialized = False
        self.collection_name = collection_name

    def _validate_settings(self):
        """验证设置参数"""
        required_settings = [
            'MILVUS_HOST',
            'MILVUS_PORT',
            'MILVUS_USER',
            'MILVUS_PASSWORD',
            'MILVUS_DB_NAME',
            'MILVUS_DIMENSION',
            'MILVUS_INDEX_TYPE',
            'MILVUS_METRIC_TYPE'
        ]
        
        for setting in required_settings:
            if not hasattr(settings, setting):
                raise ValueError(f"Missing required setting: {setting}")
            
            value = getattr(settings, setting)
            if value is None or value == "":
                raise ValueError(f"Setting {setting} cannot be empty")

    def _create_client(self) -> AsyncMilvusClient:
        """创建 Milvus 客户端"""
        return AsyncMilvusClient(
            uri=f"{settings.MILVUS_HOST}:{settings.MILVUS_PORT}",
            user=settings.MILVUS_USER,
            password=settings.MILVUS_PASSWORD,
            db_name=settings.MILVUS_DB_NAME,
        )

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @with_retry()
    async def initialize(self):
        """初始化客户端"""
        if not self._initialized:
            await self.ensure_collection_exists()
            self._initialized = True

    async def close(self):
        """关闭客户端连接"""
        try:
            await self.client.close()
        except Exception as e:
            await logger.error(f"Error closing Milvus client: {str(e)}")

    @with_retry()
    async def ensure_collection_exists(self):
        """确保集合存在"""
        # 直接尝试创建集合，如果集合已存在则会捕获异常
        fields = [
            FieldSchema(name="id", dtype=DataType.STRING, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.MILVUS_DIMENSION),
            FieldSchema(name="document", dtype=DataType.VARCHAR, max_length=16384),
            FieldSchema(name="metadata", dtype=DataType.JSON),
            FieldSchema(name="upload_id", dtype=DataType.STRING),
            FieldSchema(name="owner_id", dtype=DataType.STRING),
            FieldSchema(name="team_id", dtype=DataType.STRING),
        ]
        schema = CollectionSchema(fields=fields)
        
        try:
            await self.client.create_collection(
                collection_name=self.collection_name,
                schema=schema,
            )
            await self.create_index()
            await logger.info(f"Created collection {self.collection_name} with index")
        except Exception as e:
            # 如果集合已存在，则忽略错误
            if "already exists" in str(e).lower():
                await logger.info(f"Collection {self.collection_name} already exists")
            else: raise e

    @with_retry()
    async def insert(
        self, 
        embeddings: List[List[float]], 
        documents: List[str], 
        metadata: List[Dict], 
        upload_ids: List[str], 
        owner_ids: List[str], 
        team_ids: List[str]
    ):
        """插入向量数据"""
        # 验证数据
        self._validate_insert_data(
            embeddings, documents, metadata, upload_ids,
            owner_ids, team_ids
        )
        # 特别处理嵌入向量，确保它们是正确的浮点数列表
        processed_embeddings = []
        for emb in embeddings:
            if isinstance(emb, list) and len(emb) > 0:
                # 如果嵌入是嵌套列表(如[[0.1, 0.2...]])，提取第一个元素
                if isinstance(emb[0], list):
                    emb = emb[0]
                processed_embeddings.append([float(val) for val in emb])
            else:
                processed_embeddings.append(emb)
        
        entities = [
            processed_embeddings,
            documents,
            metadata,
            upload_ids,
            owner_ids,
            team_ids,
        ]
        return await self.client.insert(
            collection_name=self.collection_name,
            data=entities
        )

    def _validate_insert_data(self, *args):
        """验证插入数据"""
        if not all(len(lst) == len(args[0]) for lst in args):
            raise ValueError("All input lists must have the same length")
            
        for doc in args[1]:  # documents
            if len(doc.encode('utf-8')) > 16384:
                raise ValueError(f"Document length exceeds 16KB limit: {len(doc)} bytes")

    @with_retry()
    async def search(
        self, 
        query_embedding: Optional[List[float]] = None,
        top_k: int = 5,
        filter_expr: Optional[str] = None,
        output_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """搜索数据"""
        if query_embedding is not None:
            results = await self.client.search(
                collection_name=self.collection_name,
                data=[query_embedding],
                anns_field="embedding",
                param={
                    "metric_type": settings.MILVUS_METRIC_TYPE,
                    "params": {"nprobe": 10}  # 默认搜索参数
                },
                limit=top_k,
                expr=filter_expr,
                output_fields=output_fields or ["document", "metadata", "upload_id", "owner_id", "team_id"]
            )
            
            return self._process_search_results(results[0], output_fields)
        else:
            return await self.client.query(
                collection_name=self.collection_name,
                filter_=filter_expr,
                output_fields=output_fields or ["document", "metadata", "upload_id", "owner_id", "team_id"],
                limit=top_k
            )

    def _process_search_results(self, results, output_fields):
        """处理搜索结果"""
        hits = []
        for hit in results:
            hits.append({
                "score": hit.score,
                **{field: hit.entity.get(field) for field in output_fields or []}
            })
        return hits

    @with_retry()
    async def delete_by_upload_id(self, upload_id: str):
        """根据 upload_id 删除数据"""
        await self.client.delete(
            collection_name=self.collection_name,
            filter_=f"upload_id == '{upload_id}'"
        )

    @with_retry()
    async def create_index(self):
        """创建索引"""
        index_params = {
            "metric_type": settings.MILVUS_METRIC_TYPE,
            "index_type": settings.MILVUS_INDEX_TYPE,
            "field_name": "embedding",
            "params": {"nlist": 1024}  # 默认参数
        }
        
        await self.client.create_index(
            collection_name=self.collection_name,
            field_name="embedding",
            index_params=index_params
        )
        await logger.info(f"Created index for collection {self.collection_name}")
