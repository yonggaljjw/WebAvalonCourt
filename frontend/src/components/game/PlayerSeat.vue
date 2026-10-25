<!-- 공개 정보만 받는 좌석. 역할/진영은 이 컴포넌트에 전달하지 않습니다. -->
<script setup>
defineProps({
  player: { type: Object, required: true },
  index: Number,
  mine: Boolean,
  leader: Boolean,
  host: Boolean,
  ready: Boolean,
  submitted: Boolean,
  selected: Boolean,
  nominated: Boolean,
  selectable: Boolean,
  lady: Boolean,
  lobby: Boolean,
});
const emit = defineEmits(["select"]);
</script>
<template>
  <button
    class="seat"
    :class="{
      selected,
      nominated,
      offline: !player.connected,
      'is-leader': leader,
      'is-ready': lobby && ready,
      'is-mine': mine,
    }"
    :aria-pressed="selected"
    :aria-disabled="!selectable"
    @click="emit('select', player.id)"
  >
    <span class="seat-top">{{
      leader ? "♛ 원정대장" : host ? "♜ 방장" : `기사 ${index + 1}`
    }}</span>
    <span class="avatar-ring"
      ><img
        src="/assets/remaster/board/neutral-knight.webp"
        alt=""
        width="512"
        height="512"
      /><span v-if="mine" class="me-tag">나</span></span
    >
    <b :title="player.name">{{ player.name }}</b>
    <small class="seat-state">{{
      !player.connected
        ? "◌ 접속 대기"
        : lobby
          ? ready
            ? "✓ 준비 완료"
            : "준비 중"
          : submitted
            ? "✓ 제출 완료"
            : nominated
              ? "⚑ 원정대원"
              : "회의 참여"
    }}</small>
    <small v-if="lady" class="lady-tag">♧ 호수의 여인</small>
    <span v-if="selected" class="selection-tag">✓ 선택</span>
  </button>
</template>
