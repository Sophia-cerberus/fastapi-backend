import requests
from langchain.tools import BaseTool
from typing import List, Optional, Type
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """单个搜索结果模型"""
    title: str = Field(..., description="搜索结果标题")
    url: str = Field(..., description="结果URL链接")
    snippet: Optional[str] = Field(None, description="结果摘要文本")
    source: Optional[str] = Field(None, description="结果来源/域名")


class WebSearchInput(BaseModel):
    """网络搜索输入参数模型"""
    query: str = Field(..., min_length=2, description="搜索查询内容")
    max_results: int = Field(5, ge=1, le=10, description="最大返回结果数量")
    region: Optional[str] = Field("zh-CN", description="搜索区域/语言")


class WebSearchTool(BaseTool):
    """
    专业的网络搜索引擎工具，提供实时、准确的互联网信息检索功能。
    
    特性：
    - 支持多种搜索引擎API切换
    - 结果结构化返回
    - 自动请求重试机制
    - 支持多语言区域设置
    """
    name = "web_search"
    description: str = (
        "当需要获取最新、实时的互联网信息时使用此工具。"
        "输入应为明确的搜索查询内容。"
        "适用于查找新闻、事实数据、产品信息等。"
    )
    args_schema: Type[BaseModel] = WebSearchInput
    
    # 配置参数
    class Config:
        search_endpoint: str  # 可替换为其他API端点
        api_key: Optional[str] = None  # 应从安全存储获取
        timeout: int = 10  # 请求超时时间(秒)
        max_retries: int = 3  # 最大重试次数

        @classmethod
        def set_api_key(cls, key: str):
            cls.api_key = key

    def _validate_response(self, response_data: dict) -> bool:
        """验证API响应数据是否有效"""
        return bool(response_data.get("organic_results"))
    
    def _parse_results(self, api_data: dict) -> List[SearchResult]:
        """解析API原始数据为结构化结果"""
        results = []
        for item in api_data.get("organic_results", [])[:self.args.max_results]:
            results.append(SearchResult(
                title=item.get("title"),
                url=item.get("link"),
                snippet=item.get("snippet"),
                source=item.get("source")
            ))
        return results

    def _call_search_api(self) -> dict:
        """调用实际的搜索API"""
        params = {
            "q": self.args.query,
            "num": self.args.max_results,
            "hl": self.args.region,
            "api_key": self.Config.api_key
        }
        
        for attempt in range(self.Config.max_retries):
            try:
                response = requests.get(
                    self.Config.search_endpoint,
                    params=params,
                    timeout=self.Config.timeout
                )
                response.raise_for_status()
                data = response.json()
                
                if self._validate_response(data):
                    return data
            
            except Exception as e:
                if attempt == self.Config.max_retries -1:
                    raise RuntimeError(f"搜索API请求失败,最终错误: {str(e)}") from e
        
        return {"organic_results": []}
    
    def _format_output(self, results: List[SearchResult]) -> str:
        """格式化输出为易读文本"""
        if not results:
            return f"未找到关于 '{self.args.query}' 的相关结果"
            
        output_lines = [
            f"关于 '{self.args.query}' (区域:{self.args.region})的搜索结果：",
            f"共找到 {len(results)} 条相关结果：\n"
        ]
        
        for i, result in enumerate(results, start=1):
            output_lines.append(
                f"{i}. 【{result.title}】\n"
                f"   URL: {result.url}\n"
                f"   {result.snippet or '无摘要'}\n"
                f"   {'来源：'+result.source if result.source else ''}"
            )
        
        return "\n".join(output_lines)
    
    def _run(self) -> str:
        try:
            # Step 1: API调用获取原始数据
            raw_data = self._call_search_api()
            
            # Step 2: 解析结构化数据
            search_results = self._parse_results(raw_data)
            
            # Step 3: 格式化输出文本
            return self._format_output(search_results)
            
        except Exception as e:
            error_msg = (
                f"网络搜索执行失败\n"
                f"查询：{self.args.query}\n"
                f"错误原因：{str(e)}"
            )
            return error_msg
