

from time import time
from json import dumps

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.utils.logger import get_logger
from app.utils.context import trace_id_ctx


logger = get_logger(__name__)

# 自定义 Trace ID 管理器，保证在一个请求上下文中 trace_id 一样且唯一

class CoreMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:

        trace_id_ctx.trace_id = None

        start_time = time()
        response = await call_next(request)
        process_time = time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Trace-ID-Var"] = trace_id_ctx.trace_id

        client_ip = request.client.host if request.client else "unknown"

        response.headers["X-Request-IP-Host"] = client_ip

        message = dumps({
            "path_params": dumps(request.path_params, ensure_ascii=False),
            "query_params": str(request.query_params),
            "method": request.method,
            "url": request.url.hostname,
            "status_code": response.status_code,
            "process_time": f"{process_time:.4f}s",
            "client_ip": client_ip,
            "trace_id": trace_id_ctx.trace_id,
            "user_agent": request.headers.get("User-Agent"),
        }, ensure_ascii=False)

        await logger.info(message)

        return response


def register_middleware(app: FastAPI):
    app.add_middleware(CoreMiddleware)