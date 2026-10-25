# Frontend 학습 가이드

이 폴더는 **Vue 3 + Vite**로 만든 브라우저 화면입니다. 개발 시 Vite가 코드를 번들링하고, 배포용 Docker 이미지에서는 Nginx가 빌드 결과를 제공합니다.

## Vue에서 먼저 알아둘 개념

- **Component**: 화면을 작은 부품으로 나눈 `.vue` 파일입니다.
- **Props**: 부모 컴포넌트가 자식에게 내려주는 값입니다.
- **Emit**: 자식이 부모에게 “이 일이 발생했다”고 이벤트를 올리는 방법입니다.
- **ref/reactive**: 값이 바뀌면 화면도 자동 갱신되는 반응형 상태입니다.
- **computed**: 다른 상태를 이용해 계산되는 값입니다.
- **watch**: 특정 상태 변화가 생겼을 때 부수효과를 실행합니다.
- **Composable**: 여러 컴포넌트에서 쓰거나 화면과 분리하고 싶은 상태/로직을 함수로 묶는 Vue 패턴입니다.

## 화면 흐름

```text
main.js
  ↓
App.vue
  ├─ pages/            큰 화면 단위
  │   └─ components/  작은 UI 부품
  ├─ composables/      상태 + 게임/오디오 로직
  ├─ services/         HTTP 통신
  └─ constants/        고정 데이터
```

추천 순서는 `main.js → App.vue → pages → components → useAvalon.js → api.js`입니다.

## 게임 상태와 표현을 나누는 이유

`useAvalon.js`는 REST/WS에서 받은 room을 관리하고 `GamePage.vue`와 자식 컴포넌트가 표시합니다. `presentation.js`는 공개 상태로 배너를 고르며 `useAudio.js`는 같은 상태를 오디오 엔진에 전달합니다. 음악·효과 때문에 서버의 원본 room을 변경하지 않습니다.

## 정적 파일과 빌드

실행 이미지와 음원은 [public/README.md](public/README.md)를 참고하세요. `npm ci`는 lock 파일대로 패키지를 설치하며 `npm run build`는 dist를 만듭니다. Dockerfile은 Node에서 빌드한 dist만 Nginx 이미지에 복사합니다. JSON은 주석을 지원하지 않으므로 package.json의 scripts와 dependencies의 역할은 이 안내에서 설명합니다.
