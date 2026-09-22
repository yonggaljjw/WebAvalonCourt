"""ASGI 진입점.

Uvicorn은 보통 `app.main:app` 형태로 이 파일의 `app` 객체를 찾습니다.
실제 구성 코드는 factory.py로 분리해 이 파일은 '시작점' 역할만 맡깁니다.
"""

from .factory import create_app

# FastAPI 애플리케이션 객체를 한 번 생성해 ASGI 서버에 노출합니다.
app = create_app()
