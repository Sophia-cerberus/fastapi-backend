import aiohttp
import asyncio
from langchain.tools import BaseTool
from typing import List, Optional, Type, Dict
from sqlmodel import SQLModel, Field


class SearchResult(SQLModel):
    """单个搜索结果模型"""
    title: str = Field(..., description="搜索结果标题")
    url: str = Field(..., description="结果URL链接")
    snippet: Optional[str] = Field(None, description="结果摘要文本")
    source: str = Field("未知来源", description="结果来源/域名")


class WebSearchInput(SQLModel):
    """网络搜索输入参数模型"""
    query: str = Field(..., min_length=2, description="搜索查询内容")
    max_results: int = Field(5, ge=1, le=10, description="最大返回结果数量")
    region: Optional[str] = Field("zh-CN", description="搜索区域/语言")
    engine: Optional[str] = Field("google", description="搜索引擎类型，如 'google'、'bing'、'ddg'")


class WebSearchTool(BaseTool):
    """
    专业的网络搜索引擎工具，提供实时、准确的互联网信息检索功能。
    支持 Google, Bing, DuckDuckGo 等多个搜索引擎，使用异步 `aiohttp` 进行并发查询。
    """
    name: str = "web_search"
    description: str = (
        "当需要获取最新、实时的互联网信息时使用此工具。\n"
        "支持 Google、Bing、DuckDuckGo 搜索。\n"
        "适用于查找新闻、事实数据、产品信息等。"
    )
    args_schema: Type[SQLModel] = WebSearchInput

    SEARCH_ENDPOINTS: Dict[str, str] = {
        "google": "https://serper.dev/search",
        "bing": "https://api.bing.microsoft.com/v7.0/search",
        "ddg": "https://api.duckduckgo.com/"
    }

    def __init__(self, api_keys: Optional[Dict[str, str]] = None, timeout: int = 10,
                 max_retries: int = 3, max_concurrency: int = 5, **kwargs):
        """
        初始化搜索工具
        :param api_keys: 搜索引擎 API 密钥字典，如 {"google": "xxx", "bing": "yyy"}
        :param timeout: 请求超时时间
        :param max_retries: 失败重试次数
        :param max_concurrency: 最大并发请求数
        """
        super().__init__(**kwargs)
        self.api_keys = api_keys or {}
        self.timeout = timeout
        self.max_retries = max_retries
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def _handle_request_error(self, attempt: int, error: Exception, engine: str):
        """处理 API 请求异常"""
        if attempt == self.max_retries - 1:
            raise RuntimeError(f"[{engine}] 搜索API请求失败, 最终错误: {str(error)}")
        await asyncio.sleep(2 ** attempt)  # 指数退避

    async def _call_search_api(self, query: str, max_results: int, region: str, engine: str) -> dict:
        """调用搜索 API(异步)"""
        if engine not in self.SEARCH_ENDPOINTS:
            raise ValueError(f"不支持的搜索引擎: {engine}")

        params = {"q": query, "num": max_results, "hl": region}
        headers = {}

        # 设置 API Key（如果需要）
        api_key = self.api_keys.get(engine)
        if api_key:
            if engine == "bing":
                headers["Ocp-Apim-Subscription-Key"] = api_key
            elif engine == "google":
                params["api_key"] = api_key

        async with self.semaphore:
            for attempt in range(self.max_retries):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(self.SEARCH_ENDPOINTS[engine], params=params, headers=headers, timeout=self.timeout) as response:
                            response.raise_for_status()
                            data = await response.json()
                            return data if self._validate_response(data) else {"organic_results": []}

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    await self._handle_request_error(attempt, e, engine)

        return {"organic_results": []}

    def _validate_response(self, response_data: dict) -> bool:
        """验证API响应数据是否有效"""
        return len(response_data.get("organic_results", [])) > 0

    def _parse_results(self, api_data: dict, max_results: int) -> List[SearchResult]:
        """解析API原始数据为结构化结果"""
        return [
            SearchResult(
                title=item.get("title", "无标题"),
                url=item.get("link", "#"),
                snippet=item.get("snippet", "无摘要"),
                source=item.get("source", "未知来源"),
            )
            for item in api_data.get("organic_results", [])[:max_results]
        ]

    def _format_output(self, results: List[SearchResult], query: str, region: str, engine: str) -> str:
        """格式化输出为易读文本"""
        if not results:
            return f"未找到关于 '{query}' 的相关结果（搜索引擎: {engine}）"

        output_lines = [
            f"关于 '{query}' (区域:{region})的搜索结果 (来源: {engine})：",
            f"共找到 {len(results)} 条相关结果：\n"
        ]

        for i, result in enumerate(results, start=1):
            output_lines.append(
                f"{i}. 【{result.title}】\n"
                f"   URL: {result.url}\n"
                f"   {result.snippet or '无摘要'}\n"
                f"   {'来源：' + result.source if result.source else ''}"
            )

        return "\n".join(output_lines)

    async def _arun(self, query: str, max_results: int = 5, region: str = "zh-CN", engine: str = "google") -> str:
        """异步运行搜索"""
        try:
            raw_data = await self._call_search_api(query, max_results, region, engine)
            search_results = self._parse_results(raw_data, max_results)
            return self._format_output(search_results, query, region, engine)

        except Exception as e:
            return f"网络搜索执行失败\n查询:{query}\n错误原因:{str(e)}"
