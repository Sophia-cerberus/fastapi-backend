# app/core/exceptions.py
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import (
    HTTPException, WebSocketException,
    RequestValidationError, ResponseValidationError
)
from pydantic_core._pydantic_core import ValidationError
import sqlalchemy
from sqlalchemy.exc import ArgumentError, DBAPIError


async def request_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
     return JSONResponse(
         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
         content={
            "status_code": 422,
            "message": f"Request Validation Error",
            "errors": [
                {'.'.join(map(str, e['loc'])): e['msg']}
                for e in exc.errors()
            ]
        },   
    )


async def response_exception_handler(request: Request, exc: ResponseValidationError) -> JSONResponse:
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
     return JSONResponse(
         status_code=exc.status_code,
         content={
            "status_code": exc.status_code,
            "message": "HTTP Error", 
            "errors": exc.detail
        },   
    )


async def websocket_exception_handler(request: Request, exc: WebSocketException) -> JSONResponse:
     return JSONResponse(
         status_code=exc.code,
         content={
            "status_code": exc.code,
            "message": "WebScoket Error", 
            "errors": exc.reason
        },   
    )


async def argument_exception_handler(request: Request, exc: ArgumentError) -> JSONResponse:
     return JSONResponse(
         status_code=400,
         content={
            "status_code": 400,
            "message": "Argument Error", 
            "errors": str(exc)
        },   
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
     return JSONResponse(
         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
         content={
            "status_code": 500,
            "message": f"API Error",
            "errors": str(exc)

        },   
    )

async def sqlalchemy_exception_handler(request: Request, exc: DBAPIError) -> JSONResponse:
     return JSONResponse(
          
         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
         content={
            "status_code": 500,
            "message": f"sqlalchemy DBAPIError Error",
            "errors": exc._message()
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