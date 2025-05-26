from app.third_party.core.base import BaseAsyncThirdPartyRequest, ThirdPartyRequestException
from app.third_party.plugins.retry import RetryPlugin
import httpx


class ExampleSDK(BaseAsyncThirdPartyRequest):
    
    BASE_URL = ""

    def __init__(self, **kwargs):
        super().__init__(base_url=self.BASE_URL, **kwargs)
        self.retry_plugin = RetryPlugin(max_retries=3, retry_interval=1.0)

    async def handle_response(self, response: httpx.Response):
        try:
            data = response.json()
        except Exception as e:
            raise ThirdPartyRequestException(f"Failed to parse response: {e}")
        if not data.get("flag"):
            raise ThirdPartyRequestException(f"Third-party API error at {response.url}: {data}")
        return data["data"]


if __name__ == '__main__':
    sdk = ExampleSDK()