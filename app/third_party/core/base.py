import httpx
from typing import Optional, Dict, Any
from app.utils.logger import get_logger
from .exceptions import ThirdPartyRequestException


class BaseAsyncThirdPartyRequest:
    def __init__(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
    ):
        self.base_url = base_url
        self.headers = headers or {}
        self.timeout = timeout
        self.logger = get_logger(__name__)

    async def before_request(self, method: str, url: str, kwargs: Dict[str, Any]):
        """Hook for actions before the request. Override in subclass if needed."""
        pass

    async def after_request(self, response: httpx.Response):
        """Hook for actions after the request. Override in subclass if needed."""
        pass

    async def handle_response(self, response: httpx.Response) -> Any:
        return response

    async def request(self, method: str, url: str, **kwargs) -> Any:
        try:
            await self.before_request(method, url, kwargs)
            async with httpx.AsyncClient() as client:
                resp: httpx.Response = await client.request(
                    method,
                    '/'.join(self.base_url, url),
                    headers=self.headers,
                    timeout=self.timeout,
                    **kwargs
                )
                resp.raise_for_status()
            await self.after_request(resp)
            return await self.handle_response(resp)
        except httpx.RequestError as e:
            await self.logger.error(f"Third-party async request failed: {e}")
            raise ThirdPartyRequestException(f"Third-party async request failed: {e}") from e 