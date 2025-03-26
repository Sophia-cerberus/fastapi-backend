# app/core/exceptions.py
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import (
    HTTPException, WebSocketException,
    RequestValidationError, ResponseValidationError
)
from pydantic_core._pydantic_core import ValidationError
from sqlalchemy.exc import ArgumentError


async def request_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
     return JSONResponse(
         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
         content={
            "status_code": 422,
            "message": f"Validation Error",
            "data": None,
            "errors": [
                f"{'.'.join(map(str, e['loc']))}: {e['msg']}"
                for e in exc.errors()
            ]
        },   
    )


async def response_exception_handler(request: Request, exc: ResponseValidationError) -> JSONResponse:
     return JSONResponse(
         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
         content={
            "status_code": 422,
            "message": f"Validation Error",
            "data": None,
            "errors": [
                f"{'.'.join(map(str, e['loc']))}: {e['msg']}"
                for e in exc.errors()
            ]
        },   
    )


async def validate_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
     return JSONResponse(
         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
         content={
            "status_code": 422,
            "message": f"Validation Error",
            "data": None,
            "errors": [
                f"{'.'.join(map(str, e['loc']))}: {e['msg']}"
                for e in exc.errors()
            ]
        },   
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
     return JSONResponse(
         status_code=exc.status_code,
         content={
            "status_code": exc.status_code,
            "message": "HTTP Error", 
            "data": None,
            "errors": exc.detail
        },   
    )


async def websocket_exception_handler(request: Request, exc: WebSocketException) -> JSONResponse:
     return JSONResponse(
         status_code=exc.code,
         content={
            "status_code": exc.code,
            "message": "WebScoket Error", 
            "data": None,
            "errors": exc.reason
        },   
    )


async def argument_exception_handler(request: Request, exc: ArgumentError) -> JSONResponse:
     return JSONResponse(
         status_code=400,
         content={
            "status_code": 400,
            "message": "Argument Error", 
            "data": None,
            "errors": str(exc)
        },   
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
     return JSONResponse(
         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
         content={
            "status_code": 500,
            "message": f"API Error",
            "data": None,
            "errors": str(exc)

        },   
    )


def register_exception_handlers(app: FastAPI):

    app.exception_handler(RequestValidationError)(request_exception_handler)
    app.exception_handler(ResponseValidationError)(response_exception_handler)
    app.exception_handler(ValidationError)(validate_exception_handler)
    app.exception_handler(HTTPException)(http_exception_handler)
    app.exception_handler(WebSocketException)(websocket_exception_handler)
    app.exception_handler(ArgumentError)(argument_exception_handler)
    app.exception_handler(Exception)(global_exception_handler)