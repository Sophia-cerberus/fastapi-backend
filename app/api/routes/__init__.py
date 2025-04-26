from fastapi import APIRouter

from . import (
    login, user, utils, apikey, team, graph, member, model,
    provider, skill, thread, upload
)
from app.core.config import settings


api_router = APIRouter()

api_router.include_router(login.router)
api_router.include_router(user.router)
api_router.include_router(utils.router)
api_router.include_router(apikey.router)
api_router.include_router(team.router)
api_router.include_router(graph.router)
api_router.include_router(member.router)
api_router.include_router(model.router)
api_router.include_router(provider.router)
api_router.include_router(skill.router)
api_router.include_router(thread.router)
api_router.include_router(upload.router)


if settings.ENVIRONMENT == "local":
    ...