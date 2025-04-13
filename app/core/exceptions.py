# app/core/exceptions.py
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import (
    HTTPException, WebSocketException,
    RequestValidationError, ResponseValidationError
)
from pydantic_core._pydantic_core import ValidationError
from sqlalchemy.exc import ArgumentError, DBAPIError

from app.utils.logger import get_logger


logger = get_logger(__name__)


async def request_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
     
     await logger.error(f"Request Validation Error: {(errors := exc.errors())}")

     return JSONResponse(
         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
         content={
            "status_code": 422,
            "message": f"Request Validation Error",
            "errors": [
                {'.'.join(map(str, e['loc'])): e['msg']}
                for e in errors
            ]
        },   
    )


async def response_exception_handler(request: Request, exc: ResponseValidationError) -> JSONResponse:
     
     await logger.error(f"Respone Validation Error: {(errors := exc.errors())}")

     return JSONResponse(
         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
         content={
            "status_code": 422,
            "message": f"Respone Validation Error",
            "errors": [
                {'.'.join(map(str, e['loc'])): e['msg']}
                for e in exc.errors()
            ]
        },   
    )


async def validate_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
     
     await logger.error(f"Validation Error: {(errors := exc.errors())}")

     return JSONResponse(
         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
         content={
            "status_code": 422,
            "message": f"Validation Error",
            "errors": [
                {'.'.join(map(str, e['loc'])): e['msg']}
                for e in exc.errors()
            ]
        },   
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
     
     await logger.error(f"HTTP Error: {(errors := exc.detail)}")

     return JSONResponse(
         status_code=exc.status_code,
         content={
            "status_code": exc.status_code,
            "message": "HTTP Error", 
            "errors": errors
        },   
    )


async def websocket_exception_handler(request: Request, exc: WebSocketException) -> JSONResponse:
     
     await logger.error(f"HTTP Error: {(errors := exc.reason)}")

     return JSONResponse(
         status_code=exc.code,
         content={
            "status_code": exc.code,
            "message": "WebScoket Error", 
            "errors": errors
        },   
    )


async def argument_exception_handler(request: Request, exc: ArgumentError) -> JSONResponse:
     
     await logger.error(f"HTTP Error: {(errors := str(exc))}")

     return JSONResponse(
         status_code=400,
         content={
            "status_code": 400,
            "message": "Argument Error", 
            "errors": errors
        },   
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
     
     await logger.error(f"API Error: {(errors := str(exc))}")

     return JSONResponse(
         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
         content={
            "status_code": 500,
            "message": f"API Error",
            "errors": str(exc)

        },   
    )

async def sqlalchemy_exception_handler(request: Request, exc: DBAPIError) -> JSONResponse:
     
     await logger.error(f"API Error: {(errors := exc._message())}")

     return JSONResponse(
         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
         content={
            "status_code": 500,
            "message": f"sqlalchemy DBAPIError Error",
            "errors": errors
        },   
    )


def register_exception_handlers(app: FastAPI):

    app.exception_handler(RequestValidationError)(request_exception_handler)
    app.exception_handler(ResponseValidationError)(response_exception_handler)
    app.exception_handler(ValidationError)(validate_exception_handler)
    app.exception_handler(HTTPException)(http_exception_handler)
    app.exception_handler(WebSocketException)(websocket_exception_handler)
    app.exception_handler(ArgumentError)(argument_exception_handler)
    app.exception_handler(DBAPIError)(sqlalchemy_exception_handler)
    app.exception_handler(Exception)(global_exception_handler)
    ...