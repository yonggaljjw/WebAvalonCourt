# `components/game` — 게임 화면 기능

- `GameBoard.vue`: 현재 단계, 플레이어, 원정대 선택, 투표/원정/암살/조사 행동
- `ChatPanel.vue`: 채팅과 기록 탭, 메시지 전송, 자동 스크롤/읽지 않음 처리
- `IdentityPanel.vue`: 내 역할과 내가 알고 있는 비밀 정보 표시
- `LobbySettings.vue`: 게임 시작 전 방 설정 수정
- `GameResult.vue`: 종료 결과와 전체 역할 공개

`GamePage.vue`가 이 컴포넌트들을 조립합니다. 실제 서버 전송은 상위로 `emit("send", ...)`한 뒤 `useAvalon.js`의 WebSocket 함수가 담당합니다.
