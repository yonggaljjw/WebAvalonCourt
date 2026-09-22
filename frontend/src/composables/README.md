# `composables` — 화면과 로직 분리

Vue Composition API에서 `useSomething()` 형태로 상태와 함수를 묶은 것을 흔히 **Composable**이라고 부릅니다.

## `useAvalon.js`

가장 중요한 프론트 로직입니다. 로비 상태, REST API, WebSocket 연결, 재접속, 초대 링크, 타이머 보정 등을 관리합니다.

## `useAudio.js`

`audio.js`의 저수준 Web Audio 코드를 Vue의 `ref/watch/lifecycle`과 연결합니다. 방 단계가 바뀌면 음악 장면을 바꾸고 효과음을 재생합니다.

컴포넌트에서 네트워크나 오디오 구현 세부사항을 제거해 화면 코드를 읽기 쉽게 만드는 것이 목적입니다.
