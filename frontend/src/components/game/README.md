# `components/game` — 게임 화면 기능

- `GameBoard.vue`: 현재 단계, 플레이어, 원정대 선택, 투표/원정/암살/조사 행동
- `ChatPanel.vue`: 채팅과 기록 탭, 메시지 전송, 자동 스크롤/읽지 않음 처리
- `IdentityPanel.vue`: 내 역할과 내가 알고 있는 비밀 정보 표시
- `LobbySettings.vue`: 게임 시작 전 방 설정 수정
- `GameResult.vue`: 종료 결과와 전체 역할 공개

`GamePage.vue`가 이 컴포넌트들을 조립합니다. 실제 서버 전송은 상위로 `emit("send", ...)`한 뒤 `useAvalon.js`의 WebSocket 함수가 담당합니다.


## 공개 상태를 표시하는 컴포넌트

- `RoundTable.vue` / `PlayerSeat.vue`: 공개 정보만 사용하는 원탁 배치와 좌석. 역할을 공개 좌석에 전달하지 않습니다.
- `QuestTrack.vue`: 서버가 공개한 원정 결과와 진행 표시.
- `RolePortrait.vue`: 본인 공개/정적 도감/종료에서 쓰는 초상화·프레임·실패 안내.
- `EventOverlay.vue`: presentation.js의 공개 이벤트 결과를 비차단 배너로 표시.

GameBoard의 selected/canSelect/submitted/select가 로컬 선택과 행동 가능 여부를 계산하고, 하위 컴포넌트에는 필요한 표시 값만 전달합니다. 서버는 action/payload를 다시 검증합니다.
