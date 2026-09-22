# Python 3.12의 최소(slim) 이미지를 백엔드 실행 기반으로 사용합니다.
FROM python:3.12-slim

# 이후 COPY/RUN/CMD의 기준 작업 디렉토리입니다.
WORKDIR /app

# 의존성 파일만 먼저 복사하면 requirements가 안 바뀐 빌드에서 Docker 캐시를 재사용할 수 있습니다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 의존성 설치 후 애플리케이션 소스를 복사합니다.
COPY app ./app

# root 권한으로 웹 서버를 실행하지 않도록 전용 일반 사용자를 만듭니다.
RUN useradd --create-home avalon
USER avalon

# 메모리 상태를 프로세스 안에서 공유하므로 worker는 1개를 유지합니다.
# --ws-max-size는 WebSocket 한 메시지의 최대 크기를 4096바이트로 제한합니다.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--ws-max-size", "4096"]
