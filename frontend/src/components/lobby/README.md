# `components/lobby` — 로비 보조 UI

현재는 `RoomModal.vue`가 있습니다. 방 만들기와 방 입장에 필요한 입력폼을 모달 하나에서 처리합니다.

학습 포인트는 `v-model`입니다. Vue 3에서 `v-model:nickname`처럼 이름이 있는 v-model을 사용하면 부모 상태를 자식 입력창과 연결할 수 있습니다. 자식은 `update:nickname` 이벤트를 발생시켜 값을 갱신합니다.
