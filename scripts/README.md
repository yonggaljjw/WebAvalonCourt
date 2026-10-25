# scripts — 최초 실행 보조 도구

`init_env.py`는 `.env.example`을 읽어 프로젝트 루트에 `.env`를 생성합니다. APP_SECRET과 MySQL 비밀번호를 서로 다른 임의 값으로 채우며 기존 파일은 덮어쓰지 않습니다.

```sh
python scripts/init_env.py
```

학습할 부분은 `Path(__file__)`로 작업 디렉터리와 무관하게 프로젝트 위치를 찾는 방법, `secrets`로 비밀값을 생성하는 방법, 기존 설정을 보존하는 검사입니다.

이 스크립트는 DB와 게임 서버를 직접 실행하지 않습니다. 생성한 설정을 compose.yaml이 컨테이너 환경변수로 전달하고, 서버의 core/config.py가 읽습니다. 전체 실행은 루트 RUN_GUIDE.md를 따릅니다.
