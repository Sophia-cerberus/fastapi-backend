from fastapi import APIRouter

from app.api.routes import (
    login, private, users, utils, apikey, team, graph, member, model,
    provider, skill, thread
)
from app.core.config import settings


api_router = APIRouter()

api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(apikey.router)
api_router.include_router(team.router)
api_router.include_router(graph.router)
api_router.include_router(member.router)
api_router.include_router(model.router)
api_router.include_router(provider.router)
api_router.include_router(skill.router)
api_router.include_router(thread.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
