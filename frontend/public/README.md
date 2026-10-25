# public — 브라우저가 직접 읽는 정적 파일

Vite는 이 폴더의 파일을 `dist`에 같은 경로로 복사합니다. `public` 안에 두면 JavaScript에서 import하지 않아도 배포되므로, 프로그램이 직접 읽는 파일만 둡니다.

| 위치 | 내용 | URL 예시 |
|---|---|---|
| [assets/remaster](assets/remaster/README.md) | 배경·원탁·역할·토큰·프레임 WebP 38개 | `/assets/remaster/board/round-table.webp` |
| [audio](audio/README.md) | BGM OGG 6개, 효과음 WAV 11개 | `/audio/bgm/camelot.ogg` |
| audio/CREDITS.txt | 소리 설정에서 열어 보는 음악 크레딧 | `/audio/CREDITS.txt` |

역할 이미지처럼 파일명을 조합하는 코드도 있습니다. 문자열을 검색해 나오지 않는다는 이유만으로 파일을 지우면 `roleImage()`·모바일 배경·이벤트 아이콘이 깨질 수 있습니다. 이름을 바꿀 때는 constants/game.js, audio.js, presentation.js, Vue 템플릿과 CSS를 함께 확인합니다.
