from fastapi import APIRouter
from app.api.routes import items, login, private, users, utils
from app.api.routes import clients, policies, quotes
from app.api.routes import agent
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(clients.router)
api_router.include_router(policies.router)
api_router.include_router(quotes.router)
api_router.include_router(agent.router)

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)