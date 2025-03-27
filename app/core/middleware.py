

from time import time
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware


class ProcessTimeMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        start_time = time()
        response = await call_next(request)
        process_time = time() - start_time
        
        # X- as prefix indicates custom proprietary header
        response.headers["X-Process-Time"] = str(process_time)
        return response


def register_middleware(app: FastAPI):
    app.add_middleware(ProcessTimeMiddleware)