# `constants` — 정적 게임 데이터

`game.js`에는 서버 요청이나 Vue 상태가 아니라 역할 이름/설명, 단계 이름, 규칙 문구, 인원별 원정대 크기처럼 **고정된 표시 데이터**를 모았습니다.

같은 문자열을 여러 컴포넌트에 직접 적지 않으면 오타와 중복 수정을 줄일 수 있습니다.

## 이미지 경로 함수

`roleImage(role, thumbnail=false)`는 `/assets/remaster/roles/{role}.webp` 또는 `-thumb.webp`를 반환합니다. 파일명을 조합하므로 사용 여부는 개별 URL 검색만으로 판단할 수 없습니다. 역할명/설명은 표시 데이터이며 참가자의 실제 역할 배정은 서버 domain/game.py가 수행합니다.
