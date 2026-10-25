# `frontend/src` 구조

브라우저에서 실제로 실행되는 Vue 소스코드입니다.

| 위치 | 역할 |
|---|---|
| `main.js` | Vue 앱을 HTML의 `#app`에 붙이는 시작점 |
| `App.vue` | 현재 페이지를 선택하고 주요 상태/이벤트를 조립하는 최상위 컴포넌트 |
| `pages/` | 로비, 게임, 규칙, 역할도감처럼 화면 단위 컴포넌트 |
| `components/` | 화면 안에서 재사용/분리한 작은 기능 단위 UI |
| `composables/` | UI와 분리한 상태 및 로직 |
| `services/` | 백엔드 HTTP API 호출 |
| `constants/` | 역할명, 단계명, 규칙 등 바뀌지 않는 데이터 |
| `audio.js` | 파일 BGM·효과음 재생, 크로스페이드와 합성 대체음 |
| `presentation.js` | 공개 게임 상태로부터 이벤트 배너를 선택 |
| `style.css` | 프로젝트 전체 공통 스타일 |

`App.vue`가 너무 커지지 않도록 **보여주는 일은 pages/components, 동작은 composables/services**에 배치한 구조입니다.
