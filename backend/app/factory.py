"""FastAPI 애플리케이션 조립."""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .core.config import ALLOWED_ORIGINS
from .domain.game import RuleError
from .lifecycle import lifespan
from .routers.http import router as api_router
from .routers.websocket import router as websocket_router


def create_app():
    app = FastAPI(
        title="Avalon Court",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
    )

    @app.exception_handler(RuleError)
    async def rule_error(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=400)

    @app.middleware("http")
    async def protect(request, call_next):
        if (
            request.method in ("POST", "PUT", "DELETE", "PATCH")
            and request.headers.get("origin") not in ALLOWED_ORIGINS
        ):
            return JSONResponse(
                {
                    "detail": "허용되지 않은 출처입니다. "
                    "ALLOWED_ORIGINS를 확인해주세요."
                },
                status_code=403,
            )
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    app.include_router(api_router)
    app.include_router(websocket_router)
    return app
