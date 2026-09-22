# `pages` — 화면 단위 컴포넌트

페이지는 사용자가 보게 되는 큰 화면 단위입니다.

- `LobbyPage.vue`: 닉네임, 방 검색/목록, 방 생성/입장
- `GamePage.vue`: 게임에 필요한 여러 컴포넌트를 조립
- `RulesPage.vue`: 규칙 설명
- `RolesPage.vue`: 역할 설명

별도의 Vue Router를 사용하지 않고 `App.vue`의 `page` 상태로 화면을 전환합니다. 프로젝트가 더 커져 URL별 페이지 이동이 필요해지면 Vue Router 도입을 고려할 수 있습니다.
