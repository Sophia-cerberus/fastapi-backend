from typing import Any, TypeVar, Generic
from sqlmodel import Field, SQLModel
from fastapi.responses import JSONResponse


T = TypeVar('T')


class ResponseModel(SQLModel, Generic[T]):
    status: bool = Field(..., description="请求状态")
    code: int = Field(200, description="状态码") 
    message: str = Field(..., description="提示信息")
    data: object = Field(None, description="返回数据")


class SuccessResponse(ResponseModel[T]):
    status: bool = True
    code: int = 200
    message: str = "请求成功"
    
    @classmethod
    def create(cls, data: T = None, message: str = "请求成功") -> 'success_response[T]':
        return cls(message=message, data=data)


class ErrorResponse(ResponseModel[T]):
    status: bool = False
    
    @classmethod
    def create(
        cls,
        code: int = 400,
        message: str = "请求失败",
        data: T = None
    ) -> 'error_response[T]':
        return cls(code=code, message=message, data=data)
    

def success_response(data: Any = None, message: str = "请求成功") -> JSONResponse:
    response = SuccessResponse.create(data=data, message=message)
    return JSONResponse(content=response.model_dump())


def error_response(
    code: int = 400,
    message: str = "请求失败",
    data: Any = None
) -> JSONResponse:
    response = ErrorResponse.create(code=code, message=message, data=data)
    return JSONResponse(content=response.model_dump(), status_code=code)