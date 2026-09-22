# AVALON COURT · 레지스탕스 아발론 웹 게임 — 통합본

이 압축 하나에 백엔드·프런트엔드·역할 초상화 8종·효과음/배경음 코드·Docker 설정이 모두 들어 있습니다. 이전 압축이나 별도 패치는 필요하지 않습니다.

Vue 3 + FastAPI + MySQL + Docker Compose로 실행하는 5~10인 실시간 추리 게임입니다.
첨부 Stitch 디자인의 검정·금색 테마와 기사·암살자·문장 이미지를 반영했습니다.
PC는 게임판과 채팅을 나란히, 모바일은 좌우로 넘기는 참가자 카드와 세로 채팅으로 구성했습니다.


## 프로젝트 구조 한눈에 보기

처음 프로젝트를 열었을 때는 아래 순서로 보면 됩니다.

- **프론트 화면을 수정**하려면 `frontend/src/pages`, `frontend/src/components`부터 확인합니다.
- **서버 통신 / WebSocket 동작을 수정**하려면 `frontend/src/composables/useAvalon.js`와 `backend/app/routers`를 확인합니다.
- **게임 규칙을 수정**하려면 `backend/app/domain/game.py`를 확인합니다.
- **DB / 환경변수 / 보안 설정을 수정**하려면 `backend/app/core`를 확인합니다.
- `frontend/src/App.vue`와 `backend/app/main.py`는 가능한 한 **조립과 진입점 역할만** 담당하도록 구성했습니다.

```text
WebAvalonCourt/
├─ compose.yaml                  # 전체 서비스(MySQL / FastAPI / Nginx) 실행
├─ .env.example                 # 환경변수 예시
├─ README.md                    # 프로젝트 실행 및 구조 설명
├─ ROLE_ART.md                  # 역할 초상화 관련 설명
├─ TEST_REPORT.md               # 테스트 / 검증 결과
│
├─ scripts/
│  └─ init_env.py               # 최초 실행용 .env 비밀값 자동 생성
│
├─ frontend/                    # Vue 3 클라이언트
│  ├─ Dockerfile
│  ├─ nginx.conf                # 정적 파일 제공 + /api, /ws 리버스 프록시
│  ├─ package.json
│  ├─ vite.config.js
│  ├─ public/
│  │  └─ assets/                # 기사/문장/역할 이미지
│  └─ src/
│     ├─ main.js                # Vue 애플리케이션 시작점
│     ├─ App.vue                # 최상위 페이지 조립 / 전역 이벤트 연결
│     ├─ style.css              # 공통 스타일 / 반응형 레이아웃
│     ├─ audio.js               # Web Audio 기반 효과음 / BGM 생성
│     │
│     ├─ pages/                 # 화면 단위 컴포넌트
│     │  ├─ LobbyPage.vue       # 방 목록 / 방 생성 / 입장
│     │  ├─ GamePage.vue        # 실제 게임 화면
│     │  ├─ RulesPage.vue       # 게임 방법
│     │  └─ RolesPage.vue       # 역할 도감
│     │
│     ├─ components/
│     │  ├─ game/               # 게임 화면에서 사용하는 기능별 UI
│     │  │  ├─ GameBoard.vue    # 원정대 구성 / 투표 / 행동 영역
│     │  │  ├─ ChatPanel.vue    # 채팅 / 자동 스크롤
│     │  │  ├─ IdentityPanel.vue# 자신의 역할 / 정보 표시
│     │  │  ├─ LobbySettings.vue# 방 설정
│     │  │  └─ GameResult.vue   # 종료 결과 / 역할 공개
│     │  ├─ lobby/
│     │  │  └─ RoomModal.vue    # 방 생성 / 입장 모달
│     │  └─ layout/
│     │     ├─ AppHeader.vue    # 공통 헤더
│     │     ├─ ErrorBanner.vue  # 오류 표시
│     │     └─ SoundControls.vue# 음량 / 음소거 UI
│     │
│     ├─ composables/           # 화면과 분리한 상태 / 로직
│     │  ├─ useAvalon.js        # 로비 상태, REST, WebSocket, 재접속
│     │  └─ useAudio.js         # BGM / 효과음 상태 및 장면 전환
│     │
│     ├─ services/
│     │  └─ api.js              # fetch 공통 처리
│     └─ constants/
│        └─ game.js             # 역할명 / 게임 단계 등 정적 데이터
│
└─ backend/                     # FastAPI 서버
   ├─ Dockerfile
   ├─ requirements.txt
   ├─ tests/
   │  ├─ test_game.py           # 순수 게임 규칙 테스트
   │  └─ test_api.py            # REST / WebSocket 통합 테스트
   └─ app/
      ├─ main.py                # ASGI 진입점: app 생성만 담당
      ├─ factory.py             # FastAPI 앱 조립 / 라우터 등록
      ├─ lifecycle.py           # 서버 시작 / 종료 시 처리
      ├─ schemas.py             # API 요청/응답 스키마
      ├─ state.py               # 방 / 연결 / lock 등 런타임 상태
      │
      ├─ core/                  # 인프라 공통 기능
      │  ├─ config.py           # 환경변수 / 설정
      │  ├─ database.py         # DB 연결 / 저장
      │  └─ security.py         # 토큰 / 비밀번호 해시
      │
      ├─ domain/
      │  └─ game.py             # 아발론 핵심 게임 규칙
      │
      ├─ routers/               # 외부 요청 진입점
      │  ├─ http.py             # 세션 / 방 관리 REST API
      │  └─ websocket.py        # 실시간 게임 WebSocket
      │
      └─ services/              # 여러 계층에서 공유하는 업무 로직
         ├─ session_service.py   # 익명 세션 처리
         ├─ room_service.py      # 방 조회 / 검증 / 저장 보조
         └─ realtime.py          # 브로드캐스트 / 서버 시계 / 실시간 처리
```

### 요청이 처리되는 흐름

```text
브라우저
  ↓
Vue Page / Component
  ↓
useAvalon.js
  ├─ REST 요청 ─────→ routers/http.py
  └─ WebSocket ─────→ routers/websocket.py
                         ↓
                    services / domain
                         ↓
                  MySQL + 실시간 상태
```

게임 규칙 자체는 `domain/game.py`, 네트워크 입출력은 `routers`, 세션·방 관리 같은 공통 업무는 `services`로 분리했습니다. 따라서 새로운 기능을 추가할 때도 먼저 **UI → 통신 → 서비스 → 게임 규칙** 중 어느 영역인지 정한 뒤 해당 파일을 수정하면 됩니다.

## 빠른 실행 (Windows / macOS / Linux)

Docker Engine + Compose 또는 Docker Desktop이 실행 중이어야 합니다. `.env` 생성에 Python 3이 필요합니다.
압축을 풀고 `compose.yaml`이 있는 폴더에서 다음을 실행합니다.

```sh
python scripts/init_env.py
docker compose up --build -d
```

Windows에서 `python`이 없고 Python Launcher가 있다면 `py scripts/init_env.py`를 사용하세요.
첫 실행은 이미지 다운로드·의존성 설치·DB 초기화로 시간이 걸립니다.

접속: http://localhost:8080

```sh
docker compose ps
docker compose logs -f backend
```

닉네임 입력 → 원탁 만들기 → 역할·인원·시간 설정 저장 → 초대 링크 전달 → 모두 준비 완료 → 방장 원정 시작.
회원가입은 없으며 7일짜리 익명 세션 쿠키로 본인을 구별합니다. 같은 브라우저의 탭은 같은 사람입니다.
여러 명 테스트는 서로 다른 기기 또는 분리된 브라우저 프로필을 사용하세요. 시크릿 창 여러 개도 쿠키가 공유될 수 있습니다.

## 휴대폰 / 다른 PC 접속

1. 서버 PC의 내부 IPv4 주소를 확인합니다. Windows는 `ipconfig`를 사용합니다.
2. `.env`의 `ALLOWED_ORIGINS`에 실제 접속 주소를 추가합니다. 공백이나 마지막 `/` 없이 입력합니다.

```dotenv
ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080,http://192.168.0.10:8080
```

3. 설정 반영: `docker compose up -d --force-recreate backend`
4. 같은 Wi-Fi에 있는 휴대폰에서 `http://192.168.0.10:8080`으로 접속합니다. 위 IP는 예시이며 실제 PC 주소로 바꿉니다.
5. Windows 방화벽에서 TCP 8080의 사설 네트워크 접근을 허용합니다.

인터넷에서 공개하려면 서버 네트워크에 맞는 포트포워딩 또는 HTTPS 리버스 프록시가 필요합니다.
도메인 접속 시 해당 `https://도메인`을 ALLOWED_ORIGINS에 추가하고 HTTPS 사용 시 `COOKIE_SECURE=true`로 설정합니다.
WebSocket Upgrade도 프록시에서 전달해야 합니다. `*`로 출처 검증을 해제하지 않습니다.
DB와 백엔드 포트는 외부에 공개하지 않고 Nginx의 8080 포트만 사용합니다.
이 프로젝트에 유료 API·음성 통신·검색 서비스 의존성은 없습니다. 직접 사용하는 서버나 회선 비용은 별도입니다.

## 환경변수

| 변수 | 용도 |
|---|---|
| APP_SECRET | 익명 토큰·방 비밀번호의 HMAC 해시 키 |
| MYSQL_DATABASE / MYSQL_USER | 애플리케이션 DB와 계정 |
| MYSQL_PASSWORD / MYSQL_ROOT_PASSWORD | DB 비밀번호; 자동 생성 |
| WEB_PORT | 웹 공개 포트; 기본 8080 |
| ALLOWED_ORIGINS | HTTP 쓰기와 WebSocket 접속을 허용할 정확한 Origin 목록 |
| COOKIE_SECURE | HTTPS에서는 true, 로컬 HTTP에서는 false |

`init_env.py`는 기존 `.env`를 덮어쓰지 않습니다. 비밀값은 소스와 분리하며 압축에는 `.env.example`만 포함됩니다.
MySQL 볼륨 생성 후 `.env`의 DB 비밀번호만 변경하면 DB의 기존 계정 암호는 자동 변경되지 않습니다.
운영 데이터를 유지하려면 DB 계정 암호를 함께 변경해야 합니다.

## 구현된 게임 규칙

- 5~10명. 선 / 악은 5인 3/2, 6인 4/2, 7인 4/3, 8인 5/3, 9인 6/3, 10인 6/4.
- 멀린·암살자 고정. 퍼시벌·모르가나·모드레드·오베론 선택. 나머지 신하/하수인은 자동 배정.
- 실제 참가 인원에 맞지 않는 특수 역할 조합은 시작 시 거절합니다. 정원 설정 시에도 악의 역할 상한을 검사합니다.
- 모두 준비하고 연결되어 있어야 방장이 시작할 수 있습니다. 설정 변경 시 준비 상태를 초기화합니다.
- 팀 구성 → 전원 승인 투표 → 원정대 비공개 카드 제출 → 다음 원정. 대장은 순서대로 교대합니다.
- 과반 찬성만 승인, 동수는 부결. 연속 5회 부결 시 악 승리. 승인 시 부결 횟수 초기화.
- 7명 이상 4차 원정은 실패 2장 필요. 다른 원정은 실패 1장이면 실패.
- 원정 3회 실패 시 악 승리. 3회 성공 시 암살자가 멀린을 맞히면 악, 틀리면 선 승리.
- 호수의 여인 옵션: 2·3·4차 원정 후 계속 진행할 때 조사. 이전 보유자 재조사 금지, 비공개 진영 확인, 대상에게 토큰 이양.
- 멀린은 모드레드 제외 악을 봅니다. 퍼시벌은 멀린·모르가나 후보를 봅니다. 오베론은 다른 악과 서로 보이지 않습니다.
- 채팅, 공개 투표 기록, 원정 실패 카드 수, 종료 시 전체 역할 공개.
- 방 비밀번호, 방 검색, 초대 코드/링크, 게임 방법·역할 도감.

랜슬롯, 엑스칼리버, 빅박스 확장 역할은 이번 구현 범위에 포함하지 않았습니다.
원본 규칙서: https://avalon.fun/pdfs/rules.pdf
사용자가 제공한 나무위키 주소는 작업 환경에서 열리지 않아 원본 규칙서로 대조했습니다.

## 연결 중단 처리 — 온라인용 추가 규칙

아발론은 역할이 배정된 뒤 한 명이라도 빠지면 정보와 진영 균형을 유지하기 어렵습니다.
따라서 인원만 줄여 계속 진행하지 않고 **재접속 성공 시에만 계속**합니다.

| 상황 | 동작 |
|---|---|
| 정상적인 연결 닫힘 | 즉시 확인하고 일시 정지 |
| 응답 없이 네트워크 단절 | 4초 간격 ping, 마지막 수신으로부터 15초 초과 시 중단 판정 |
| 재접속 유예 내 복귀 | 동일 쿠키/방으로 복귀, 일시 정지한 시간만큼 마감 연장 |
| 유예시간 초과 | 무효 종료, 승패 없음 |
| 유예 0초 | 연결 중단이 감지되는 즉시 무효 종료 |
| 진행 중 방 나가기 | 복귀 의사가 없는 명시적 퇴장으로 무효 종료 |
| 필수 행동 제한시간 초과 | 자동 투표를 조작하지 않고 무효 종료 |
| 서버 재시작 | 저장된 진행 중 게임을 무효 종료; 종료 결과는 다시 확인 가능 |
| 대기실 이탈 | 최소 15초 또는 설정 유예 후 좌석 제거; 필요 시 방장 이양 |

물리적인 인터넷 단절 순간 자체를 즉시 알 수는 없습니다. 위 기준으로 확인합니다.
휴대폰 브라우저가 백그라운드에서 정지되면 이탈로 판정될 수 있으므로 게임 중 화면을 유지하세요.
동일 세션의 다른 탭이 연결되면 기존 탭을 닫아 중복 행동을 방지합니다.
게임 종료 뒤 방에서 나가 새 방을 만들면 다음 판을 시작할 수 있습니다.

## 코드 읽는 순서

1. **전체 실행 흐름**은 루트 `compose.yaml`에서 시작합니다. MySQL → FastAPI → Nginx 순서로 어떤 서비스가 뜨는지 확인할 수 있습니다.
2. **백엔드 진입점**은 `backend/app/main.py`이며, 실제 앱 조립은 `factory.py`에서 합니다.
3. **게임 규칙**을 이해하려면 `backend/app/domain/game.py`의 `action()`과 `view()`를 먼저 보면 됩니다.
4. **REST 요청**은 `routers/http.py`, **실시간 게임 행동**은 `routers/websocket.py`에서 시작합니다.
5. 프론트에서는 `App.vue`보다 먼저 `pages/`를 보고, 세부 UI는 `components/`에서 찾는 것이 빠릅니다.
6. 서버 통신과 재접속 로직은 `useAvalon.js`, 오디오는 `useAudio.js`, API 공통 호출은 `services/api.js`에 모여 있습니다.
7. 기능 수정 후에는 `backend/tests/`와 `frontend/tests/`를 함께 확인하면 기존 동작이 깨졌는지 검증하기 쉽습니다.

## 저장과 운영 범위

MySQL에 방의 전체 상태와 익명 세션 해시를 저장합니다. `room_state`에는 역할 등 비공개 게임 정보가 포함되므로 DB는 서버 운영자만 접근해야 합니다.
원정 진행 중 카드는 복구용 스냅샷에 잠시 저장되고, 정산 후 작성자별 카드는 지웁니다. 공개 기록에는 실패 카드 수만 남습니다.
참가자가 전혀 접속하지 않는 대기/종료 방은 마지막 행동 기준 24시간 뒤 정리됩니다.
한 서버 프로세스가 메모리의 방 상태와 연결을 관리하고 MySQL에 저장하는 구조입니다. **Uvicorn worker는 반드시 1개**로 유지합니다.
이 구성은 소규모 자체 호스팅용입니다. 다중 서버/worker 확장에는 Redis 같은 공용 상태·이벤트 전달 체계와 DB 저장 단위 개선이 필요합니다.
요청별 동기 DB 저장과 잠금 내부 전송 때문에 대규모 동시접속 성능을 보장하지 않습니다. 부하 시험은 수행하지 않았습니다.
익명 참가자를 대상으로 하므로 동일 인물의 다른 기기 다중 참여, 외부 메신저를 통한 담합은 방지하지 않습니다.

## 개발·검증

백엔드 테스트 (MySQL 대신 일회성 SQLite 사용):

```sh
python -m pip install -r backend/requirements.txt
cd backend
python -m pytest -q tests
```

프런트엔드 빌드:

```sh
cd frontend
npm ci
npm run build
```

컨테이너에서 실제 MySQL 연결 확인:

```sh
docker compose ps
docker compose exec backend python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/health').read().decode())"
```

기본 테스트와 프런트 빌드 결과, 검증하지 못한 항목은 `TEST_REPORT.md`에 기록했습니다.

## 종료 / 업데이트

```sh
docker compose down
docker compose up --build -d
```

`down`은 DB 볼륨을 보존합니다. **`docker compose down -v`는 모든 게임/세션 DB 데이터를 삭제하므로 초기화할 때만 사용합니다.**
배포 중 진행 게임은 서버 재시작으로 무효 종료되므로 플레이가 끝난 뒤 업데이트하세요.

## 디자인 출처

첨부 `stitch_.zip`의 Avalon Court 디자인 명세, PC·모바일 목업과 3개 삽화를 참고했습니다.
삽화는 WebP로 변환해 로컬 제공하며 외부 이미지·폰트 CDN에 의존하지 않습니다.
정식 상품과 무관한 비공식 팬 구현이며 원본 디자인 13장을 이미지로 붙인 데모가 아니라 실제 Vue 화면입니다.

## 역할 초상화 업데이트

8개 역할에 각각 전용 생성 이미지를 추가했습니다. 역할 도감·본인의 역할 확인·종료 결과에 적용됩니다.
이미지 경로와 생성 프롬프트, 기존 설치 업데이트 방법은 `ROLE_ART.md`를 참고하세요.

## 배경음과 효과음

상단 **소리 켜기**를 누르면 배경음과 효과음이 활성화됩니다. 기본 배경음 25%, 효과음 50%이며 각각 조절 가능합니다.
볼륨은 이 브라우저에 저장하고, 새로고침 뒤에는 다시 소리 켜기를 눌러 재생합니다.
브라우저의 사용자 제스처 정책에 따라 자동으로 큰 음악을 재생하지 않습니다.
참고: https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API/Best_practices

- 로비/토론은 차분한 패턴, 투표/원정/암살은 긴장감 있는 패턴으로 변경합니다.
- 라운드에 따라 반복 선율을 변형합니다. 원정 시작, 투표, 조사, 암살, 성공/실패, 부결, 승패/무효 종료에 효과음이 있습니다.
- 같은 상태의 채팅 갱신에는 효과음이 반복되지 않습니다. 최초 접속과 재접속에서 지난 효과음을 재생하지 않습니다.
- 게임 일시 정지·종료·탭이 숨겨진 동안 배경음을 멈춥니다.
- 녹음된 오케스트라 음원이 아니라 `frontend/src/audio.js`의 직접 작곡한 음계/리듬을 Web Audio로 합성하는 방식입니다. 외부 음원 다운로드, API 키, 유료 라이브러리가 필요 없습니다.

## 카카오톡 방식 채팅

- 내 메시지: 오른쪽 금색 말풍선, 상대 메시지: 왼쪽 어두운 말풍선.
- 닉네임·전송 시각 표시, 긴 글 자동 줄바꿈.
- 서버가 인증된 세션으로 `sender_id`를 붙입니다. 클라이언트가 보낸 발신자 ID는 사용하지 않습니다.
- 맨 아래를 보고 있으면 새 메시지로 이동하고, 지난 대화를 읽는 중이면 위치를 유지하며 새 메시지 버튼을 표시합니다.
- 기존 DB의 옛 메시지는 발신자 ID가 없으므로 왼쪽에 표시됩니다. 새 메시지부터 정확히 구별됩니다.

## 기존 버전에서 통합본으로 업데이트

압축을 새 폴더에 풀고 기존 `.env`를 복사합니다. 기존 MySQL 데이터를 계속 사용하려면 기존 Compose 프로젝트 이름을 유지해야 합니다.
가장 간단한 방법은 기존 프로젝트를 백업한 뒤 통합본의 소스 파일들을 기존 프로젝트 폴더에 덮어쓰는 것입니다. 압축에는 `.env`가 없으므로 기존 비밀값을 덮어쓰지 않습니다.
프로젝트 폴더에서 `docker compose up --build -d`로 전체 변경을 반영합니다. 진행 중 게임이 없는 때 업데이트하세요.
`docker compose down -v`는 사용하지 않습니다. 업데이트 후 Ctrl+F5로 새로고침합니다.
역할 설명 페이지는 상단 **역할 도감** 메뉴이며 8종의 초상화·진영·능력 설명을 포함합니다.
