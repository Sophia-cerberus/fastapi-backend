from fastapi import APIRouter

from . import (
    login, user, utils, apikey, team, graph, model,
    provider, thread, upload, dataset, embedding
)
from app.core.config import settings


api_router = APIRouter()

api_router.include_router(login.router)
api_router.include_router(user.router)
api_router.include_router(utils.router)
api_router.include_router(apikey.router)
api_router.include_router(team.router)
api_router.include_router(graph.router)
api_router.include_router(model.router)
api_router.include_router(provider.router)
api_router.include_router(thread.router)
api_router.include_router(upload.router)
api_router.include_router(dataset.router)
api_router.include_router(embedding.router)


if settings.ENVIRONMENT == "local":
    ...