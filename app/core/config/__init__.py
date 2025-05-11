import os
import warnings
from typing import Annotated, Any, Literal
from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import SettingsConfigDict, BaseSettings
from typing_extensions import Self

def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )
    API_V1_STR: str = "/api/v1"
    # SECRET_KEY: str = secrets.token_urlsafe(32)
    SECRET_KEY: str = "1"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    FRONTEND_HOST: str = "http://localhost:5173"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    PROJECT_NAME: str
    SENTRY_DSN: HttpUrl | None = None
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_MIGRATE_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg2",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_RUNNABLE_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )
    
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: EmailStr | None = None

    PROTECTED_NAMES: list[str] = ["user", "ignore", "error"]

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str 
    AWS_S3_ENDPOINT_URL: str
    AWS_S3_BUCKET_NAME: str
    AWS_S3_UPLOAD_BUFFER: int = 5 * 1024 * 1024  # 5MB 分块大小
    AWS_S3_DOWNLOAD_BUFFER: int = 1024 * 1024
    AWS_S3_UPLOAD_PREFIX: str

    """Milvus 配置"""
    MILVUS_HOST: str
    MILVUS_PORT: int
    MILVUS_USER: str
    MILVUS_PASSWORD: str
    MILVUS_DB_NAME: str = "default"
    MILVUS_ASYNC: bool = True
    MILVUS_INDEX_TYPE: str = "IVF_FLAT"
    MILVUS_DIMENSION: int = 1024
    MILVUS_METRIC_TYPE: str = "L2"
    MILVUS_MAX_RETRIES: int = 3
    MILVUS_RETRY_DELAY: float = 1.0
    MILVUS_INDEX_PARAMS: dict[str, Any] = {
        "nlist": 1024,
        "nprobe": 10,
        "ef": 1024,
        "m": 16,
        "ef_construction": 1024,
    }

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    EMAIL_TEST_USER: EmailStr = "test@example.com"
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )

        return self
    
    MODEL_PROVIDER_ENCRYPTION_KEY: str = ""

    LOGGING_DIR: str = 'logs'

    if not os.path.exists(LOGGING_DIR): 
        os.makedirs(LOGGING_DIR)

    SERVER_LOGS_FILE: str = os.path.join(LOGGING_DIR, 'server.log')
    ERROR_LOGS_FILE: str = os.path.join(LOGGING_DIR, 'error.log')

    LOGGING: dict[str, Any] = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '%(asctime)s [%(trace_id)s] [%(name)s] [%(filename)s:%(lineno)d] [%(levelname)s] - %(message)s',
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            'standard': {
                'format': '{"time": "%(asctime)s", "level": "%(levelname)s", "func": "%(name)s.%(module)s.%(funcName)s:%(lineno)d", "trace_id": "%(trace_id)s",  "message": "%(message)s"}',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'filters': {
            'info_filter': "app.utils.logger.filters.InfoFilter",
            'trace_id_filter': "app.utils.logger.filters.TraceIdFilter"
        },
        'handlers': {
            'error_file': {
                'level': 'ERROR',
                'class': 'aiologger.handlers.files.AsyncTimedRotatingFileHandler',
                'filename': ERROR_LOGS_FILE,
                'when': "midnight",
                'backup_count': 7,  # 保留最近7天的日志文件
                'formatter': 'standard',
                'filters': ['trace_id_filter'],
                'encoding': 'utf-8'  # 设置文件编码为UTF-8
            },
            'info_file': {
                'level': 'INFO',
                'class': 'aiologger.handlers.files.AsyncTimedRotatingFileHandler',
                'filename': SERVER_LOGS_FILE,
                'when': "midnight",
                'backup_count': 7,  # 保留最近7天的日志文件
                'formatter': 'standard',
                'filters': ['trace_id_filter', 'info_filter'],
                'encoding': 'utf-8'  # 设置文件编码为UTF-8
            }
        }
    }

settings = Settings()  # type: ignore
