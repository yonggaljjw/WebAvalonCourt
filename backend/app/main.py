"""ASGI 진입점. 애플리케이션 조립은 factory.py에서 담당합니다."""
from .factory import create_app

app = create_app()
