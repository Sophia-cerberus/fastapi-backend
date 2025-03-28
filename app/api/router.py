from fastapi import APIRouter

from app.api.routes import login, private, users, utils, apikey, team, graph, member
from app.core.config import settings


api_router = APIRouter()

api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(apikey.router)
api_router.include_router(team.router)
api_router.include_router(graph.router)
api_router.include_router(member.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
