# `services` — 외부 통신

`api.js`는 브라우저의 `fetch()`를 한 번 감싸서 모든 REST 요청이 같은 규칙으로 동작하게 합니다.

공통 처리 내용:
- `/api` 접두사 자동 추가
- JSON 요청 본문 직렬화
- JSON 응답 파싱
- HTTP 오류를 JavaScript `Error`로 변환

API 함수가 하나뿐이어도 이런 래퍼를 두면 각 컴포넌트에서 매번 `fetch`, 헤더, 오류 처리를 반복하지 않아도 됩니다.
