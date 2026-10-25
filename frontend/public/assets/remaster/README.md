# 화면 이미지와 코드 연결

| 폴더 | 역할 | 읽는 코드 |
|---|---|---|
| backgrounds | 성·회의실·호수·암살 장면, 모바일 파생본 | style.css의 페이지/장면 선택자 |
| board | 원탁·중립 기사 | RoundTable.vue, PlayerSeat.vue |
| roles | 역할 8종과 작은 썸네일 8개 | constants/game.js의 roleImage(), RolePortrait.vue |
| cards | 봉인된 역할 카드 뒷면 | IdentityPanel.vue |
| emblems | 왕실 문장 | AppHeader.vue, LobbyPage.vue, 결과·이벤트 |
| tokens | 찬성·반대·원정 성공·실패 | GameBoard.vue, QuestTrack.vue, presentation.js |
| results | 선·악 종료 장면과 모바일 파생본 | GameResult.vue, style.css |
| ui | 양피지·투명 카드 프레임 | RulesPage.vue의 스타일, RolePortrait.vue |

원본 크기의 역할 이미지는 8개이고 `-thumb.webp` 8개는 별도 역할이 아니라 srcset용 축소본입니다. `-mobile.webp` 배경도 CSS 미디어쿼리에서 실제 사용하므로 필요합니다. 전체 WebP는 38개입니다.

본인 역할은 IdentityPanel에서 명시적으로 열 때만 표시합니다. 공개 좌석에는 역할 초상화를 붙이지 않습니다. 전체 역할 공개는 종료 화면에서만 수행합니다. 이미지 출처는 루트 LICENSES_REMASTER.md를 확인하세요.
