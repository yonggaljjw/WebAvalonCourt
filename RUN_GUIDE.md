# 리마스터 통합본 실행 안내

## 새로 설치하기 — Windows / Docker Desktop

1. ZIP 전체를 풀고 `compose.yaml`이 있는 `WebAvalonCourt` 폴더에서 PowerShell을 연다.
2. Docker Desktop을 실행한다. 이 프로젝트는 Linux 컨테이너를 사용한다.
3. Python이 설치되어 있으면 다음을 실행한다.

```powershell
python scripts/init_env.py
docker compose up --build -d
docker compose ps
```

`python` 명령이 없고 `py`가 동작하면 첫 명령을 `py scripts/init_env.py`로 실행한다. `.env`가 이미 있으면 초기화 스크립트는 덮어쓰지 않는다. Python을 이용하지 않는 경우 `.env.example`을 `.env`로 복사하고 세 개의 `GENERATE_ME`를 서로 다른 충분히 긴 임의 비밀값으로 직접 바꾼다.

브라우저에서 **http://localhost:8080**에 접속한다. 첫 빌드는 Docker 이미지와 패키지를 내려받으므로 인터넷 연결이 필요하다. BGM·효과음·이미지는 ZIP에 포함되며 게임 실행 중 별도 미디어 계정이나 API 키는 필요 없다.

## 기존 설치 업데이트

기존 폴더와 `.env`를 먼저 백업한다. 기존 프로젝트 폴더에 통합본 내용을 덮어써서 Compose 프로젝트 이름과 기존 MySQL 볼륨을 유지한다. ZIP에는 실제 `.env`와 DB가 포함되지 않는다. 게임이 끝난 뒤 아래 명령으로 반영한다.

```powershell
docker compose up --build -d
```

브라우저에서 Ctrl+F5로 새로고침한다. `docker compose down -v`는 기존 DB 데이터를 지우므로 업데이트 명령으로 사용하지 않는다. 서버 재시작은 진행 게임을 무효 종료할 수 있다.

다른 폴더에서 실행하려면 기존 Compose 프로젝트 이름을 확인하고 동일한 이름을 `docker compose -p 기존이름 up --build -d`처럼 지정한다. 프로젝트 이름이 달라지면 다른 MySQL 볼륨이 연결된다.

## 다른 기기와 함께 접속

같은 공유기의 기기는 호스트 PC의 실제 내부 IP와 포트를 사용한다. 예를 들어 접속 주소가 `http://192.168.0.10:8080`이면 `.env`의 `ALLOWED_ORIGINS`에 이 주소를 쉼표로 추가하고, 변경 반영 후 접속한다. 호스트 방화벽에서 해당 포트의 접근도 허용되어 있어야 한다.

Cloudflare 등으로 HTTPS 도메인을 연결했다면 `ALLOWED_ORIGINS`에 **실제 HTTPS Origin**을 추가하고 `COOKIE_SECURE=true`로 설정한 뒤 반영한다. 이번 통합본은 기존 Tunnel을 자동 설정하거나 공개 배포하지 않는다. 외부 공개 접속은 이 환경에서 검증하지 않았다.

## 소리 사용

상단 `소리 설정`을 열고 `소리 켜기`를 누른다. 기본 배경음 25%·효과음 50%이며 개별 조절한다. 볼륨 설정은 브라우저에 저장하지만, 새로고침 뒤 재생은 다시 클릭해야 한다. 탭 숨김·연결 중단·일시정지 시 음악을 중단한다. 선/악 종료 음악은 공개된 진영 결과를 나타내며 본인의 승패를 별도로 판단하지 않는다.

소리가 없으면 설정 음량, OS/브라우저 탭 음소거를 확인한다. 파일 로딩 실패는 소리 설정에 안내하며 기본 합성음으로 대체한다. 오류 때문에 게임 진행을 중단하지 않는다. 설정의 `음악 출처·라이선스`에서 외부 음원 정보를 확인할 수 있다.

## 정상 동작 확인

```powershell
docker compose ps
docker compose logs --tail 80 backend web
docker compose exec backend python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/health').read().decode())"
```

서로 독립된 브라우저 프로필 또는 기기 5개로 같은 방에 들어가 준비 → 시작 → 역할 확인 → 원정대 제안 → 투표 → 원정을 확인한다. 같은 프로필의 일반 탭은 쿠키를 공유하므로 별도 플레이어가 되지 않을 수 있다. 채팅은 하단에서 최신 메시지를 따라가고, 과거 대화 열람 중에는 새 메시지 버튼을 사용한다.

## 종료와 소스 확인

```powershell
docker compose down
```

일반 `down`은 MySQL 볼륨을 보존한다. 실제 사용 파일은 `frontend/public/` 안에 있다. Node·Python 패키지와 Docker 이미지는 ZIP에 포함하지 않는다.

프론트 테스트는 `node --test frontend/tests/*.test.js`로 확인한다. 빌드는 `cd frontend` 후 `npm ci`, `npm run build` 순서다. 백엔드 테스트는 별도 Python 환경에 `backend/requirements.txt`를 설치한 뒤 `cd backend`에서 `python -m pytest -q tests`로 실행한다.

## 검증 범위

최신 검증 결과는 `TEST_REPORT.md`를 따른다. 이 작업 환경에는 Docker가 없어 Docker/MySQL 실기동을 보증하지 않는다. 모바일 폭 검사는 Chromium 화면 크기 검사이며 실제 휴대폰·키보드·Safari/Firefox 시험과 다르다. 사람의 청취 평가와 음원 반복부의 감성적 완성도 검수도 별도로 남아 있다.

