# 역할 이미지가 표시되는 방법

역할 8종은 `frontend/public/assets/remaster/roles/`에 WebP로 저장됩니다. 파일명은 서버 역할 코드인 merlin, percival, servant, assassin, morgana, mordred, oberon, minion과 일치합니다. 각 역할의 `-thumb.webp`는 srcset용 축소본입니다.

## 코드 흐름

1. constants/game.js의 roleImage(role, thumbnail)가 파일 URL을 만듭니다.
2. RolePortrait.vue가 src/srcset으로 이미지와 투명 프레임을 렌더링합니다.
3. IdentityPanel.vue는 본인이 공개 버튼을 눌렀을 때만 RolePortrait를 생성합니다.
4. RolesPage.vue는 참가자와 연결하지 않은 정적 도감입니다.
5. GameResult.vue는 서버 phase가 ended일 때 참가자 전체 역할을 표시합니다.

PlayerSeat.vue는 공개된 참가자 ID·이름·접속·선택 상태만 받고 중립 기사 이미지를 사용합니다. 초상화 로딩에 실패해도 역할 설명과 게임 조작은 계속 사용할 수 있습니다.

이미지는 텍스트 명세로 생성한 아서왕 판타지 아트입니다. 이용 표기는 LICENSES_REMASTER.md를 따릅니다.
