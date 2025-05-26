from .apikey import (
    ApiKey, ApiKeyBase, ApiKeyCreate, ApiKeyOut, ApiKeyOutPublic, ApiKeyUpdate
)
from .checkpoint import (
    Checkpoint, CheckpointBlobs, CheckpointOut, Write
)
from .graph import (
    Graph, GraphBase, GraphCreate, GraphOut, GraphUpdate
)
from .provider import (
    Model, ModelCapability, ModelOut, ModelCategory,
    ModelCreate, ModelProvider, ModelProviderBase, ModelProviderCreate,
    ModelProviderOut, ModelProviderUpdate, ModelsBase, ModelUpdate
)
from .team import (
    Team, TeamBase, TeamCreate, TeamOut,
    TeamUpdate
)
from .thread import (
    Thread, ThreadBase, ThreadCreate, ThreadOut, ThreadRead, ThreadUpdate
)
from .upload import (
    Upload, UploadBase, UploadCreate, UploadOut, UploadUpdate
)
from .user import (
    UpdateLanguageMe, UpdatePassword, User, UserBase, UserCreate, UserOut,
    UserRegister, UserUpdate, UserUpdateMe, TeamUserJoin, InviteCodes, RoleTypes
)
from .tenant import (
    Tenant, TenantBase, TenantCreate, TenantOut, TenantUpdate
)
from .argument import (
    Dictionary, DictionaryBase, DictionaryCreate, DictionaryOut, DictionaryUpdate,
    DictionaryArgument, DictionaryArgumentBase, DictionaryArgumentCreate, DictionaryArgumentOut,
    DictionaryArgumentUpdate
)
from .dataset import (
    Dataset, DatasetBase, DatasetCreate, DatasetOut, DatasetUpdate
)
from .embedding import (
    Embedding, EmbeddingBase, EmbeddingCreate, EmbeddingOut, EmbeddingUpdate
)

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

