<script setup>
defineProps({ message: { type: String, default: "" } });
const emit = defineEmits(["close"]);
</script>

<template>
  <div v-if="message" role="alert" class="error">
    {{ message }}
    <button aria-label="알림 닫기" @click="emit('close')">×</button>
  </div>
</template>
