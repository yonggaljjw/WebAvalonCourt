<script setup>
defineProps({
  showCreate: { type: Boolean, required: true },
  joinCode: { type: String, required: true },
  user: { type: Object, default: null },
  nickname: { type: String, required: true },
  title: { type: String, required: true },
  password: { type: String, required: true },
  busy: { type: Boolean, required: true },
  error: { type: String, default: "" },
});
const emit = defineEmits([
  "close",
  "submit",
  "update:nickname",
  "update:title",
  "update:joinCode",
  "update:password",
]);
</script>

<template>
  <div
    v-if="showCreate || joinCode"
    class="modal-backdrop"
    role="dialog"
    aria-modal="true"
    :aria-label="showCreate ? '원탁 만들기' : '원탁 참여'"
    @click.self="emit('close')"
    @keydown.esc="emit('close')"
  >
    <form class="modal panel" @submit.prevent="emit('submit')">
      <button type="button" class="close" aria-label="닫기" @click="emit('close')">
        ×
      </button>
      <p class="eyebrow">JOIN THE COUNCIL</p>
      <h2>{{ showCreate ? "새로운 원탁 만들기" : "초대받은 원탁에 참여" }}</h2>
      <label v-if="!user">
        닉네임
        <input
          :value="nickname"
          required
          maxlength="16"
          autofocus
          @input="emit('update:nickname', $event.target.value)"
        />
      </label>
      <label v-if="showCreate">
        방 이름
        <input
          :value="title"
          required
          maxlength="40"
          @input="emit('update:title', $event.target.value)"
        />
      </label>
      <label v-else>
        초대 코드
        <input
          :value="joinCode"
          required
          maxlength="6"
          @input="emit('update:joinCode', $event.target.value)"
        />
      </label>
      <label>
        방 비밀번호 {{ showCreate ? "(선택)" : "" }}
        <input
          type="password"
          :value="password"
          maxlength="64"
          autocomplete="off"
          @input="emit('update:password', $event.target.value)"
        />
      </label>
      <p v-if="showCreate" class="muted">
        인원·역할·시간은 생성 후 대기실에서 설정할 수 있습니다.
      </p>
      <p v-if="error" class="error">{{ error }}</p>
      <button class="gold wide" :disabled="busy">
        {{ busy ? "처리 중…" : showCreate ? "원탁 만들기" : "원탁에 입장" }}
      </button>
    </form>
  </div>
</template>
