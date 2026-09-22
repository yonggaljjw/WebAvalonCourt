"""FastAPI 애플리케이션을 조립하는 팩토리 모듈."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .core.config import ALLOWED_ORIGINS
from .domain.game import RuleError
from .lifecycle import lifespan
from .routers.http import router as api_router
from .routers.websocket import router as websocket_router


def create_app():
    """설정, 공통 처리, 라우터를 묶어 최종 FastAPI 앱을 생성합니다."""
    app = FastAPI(
        title="Avalon Court",
        # 서버 시작/종료 시 실행할 lifespan 함수를 연결합니다.
        lifespan=lifespan,
        # 외부 공개 서비스에서 자동 API 문서를 노출하지 않도록 비활성화합니다.
        docs_url=None,
        redoc_url=None,
    )

    @app.exception_handler(RuleError)
    async def rule_error(request, exc):
        """도메인 규칙 오류를 HTTP 400 JSON 응답으로 통일합니다."""
        return JSONResponse({"detail": str(exc)}, status_code=400)

    @app.middleware("http")
    async def protect(request, call_next):
        """쓰기 요청의 Origin을 검사하고 공통 보안/캐시 헤더를 추가합니다."""
        # GET은 조회이므로 제외하고, 상태를 바꾸는 HTTP 메서드만 Origin을 검사합니다.
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

        # 실제 엔드포인트 함수를 실행합니다.
        response = await call_next(request)

        # 게임 상태는 사용자별/시점별로 바뀌므로 브라우저 캐시에 남기지 않습니다.
        response.headers["Cache-Control"] = "no-store"
        # 브라우저가 응답 MIME 타입을 임의로 추측하지 않도록 합니다.
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    # HTTP와 WebSocket 라우터를 하나의 FastAPI 앱에 등록합니다.
    app.include_router(api_router)
    app.include_router(websocket_router)
    return app
