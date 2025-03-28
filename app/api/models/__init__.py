from .user import *
from .apikey import *
from .checkpoint import *
from .graph import *
from .member import *
from .subgraph import *
from .team import *
from .thread import *
from .model import *

from sqlmodel import Field, SQLModel


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class AccessToken(SQLModel):
    access_token: str
    token_type: str = "bearer"


# JSON payload containing access token & refresh token
class Token(AccessToken):
    refresh_token: str


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None
    exp: float | None = None
    type: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)
