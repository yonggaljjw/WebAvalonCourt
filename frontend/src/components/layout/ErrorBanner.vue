<!-- 학습용 주석: 전역 오류 메시지를 보여주고 닫기 이벤트를 올리는 작은 공통 컴포넌트입니다. -->
<script setup>
// props: 부모 컴포넌트가 이 컴포넌트에 내려주는 입력값입니다.
defineProps({ message: { type: String, default: "" } });
// emit: 자식이 직접 부모 상태를 바꾸지 않고 사용자 행동을 이벤트로 알립니다.
const emit = defineEmits(["close"]);
</script>

<template>
  <div v-if="message" role="alert" class="error">
    {{ message }}
    <button aria-label="알림 닫기" @click="emit('close')">×</button>
  </div>
</template>
