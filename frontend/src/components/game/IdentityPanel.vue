<!-- 비밀 초상화/설명은 명시적으로 열었을 때만 DOM에 존재합니다. -->
<script setup>
import { ref, watch } from "vue";
import { roleDescriptions, roleNames } from "../../constants/game.js";
import RolePortrait from "./RolePortrait.vue";
const props = defineProps({ room: { type: Object, required: true } });
const reveal = ref(false);
watch(
  [() => props.room.code, () => props.room.me.role],
  () => (reveal.value = false),
);
</script>
<template>
  <section v-if="room.me.role && room.phase !== 'ended'" class="identity panel">
    <img
      v-if="!reveal"
      class="sealed-mini"
      src="/assets/remaster/cards/sealed-back.webp"
      alt="봉인된 역할 카드 뒷면"
      width="768"
      height="1152"
    />
    <div class="identity-heading">
      <span class="eyebrow">YOUR SECRET IDENTITY</span>
      <h3>
        {{
          reveal ? roleNames[room.me.role] : "당신의 정체는 봉인되어 있습니다"
        }}
      </h3>
      <p v-if="!reveal" class="muted">
        다른 기사가 화면을 보지 않을 때 확인하세요.
      </p>
    </div>
    <button :aria-expanded="reveal" @click="reveal = !reveal">
      {{ reveal ? "정체 숨기기" : "나의 역할 확인" }}
    </button>
    <div v-if="reveal" class="secret">
      <RolePortrait :role="room.me.role" loading="eager" sizes="180px" />
      <div class="secret-description">
        <p class="eyebrow">오직 당신에게만 공개되는 정보</p>
        <p>{{ roleDescriptions[room.me.role] }}</p>
        <p v-for="knowledge in room.me.knowledge" :key="knowledge.id">
          {{ knowledge.name }} · {{ knowledge.label }}
        </p>
        <p v-for="(inspection, index) in room.me.inspections" :key="index">
          조사 결과: {{ inspection.name }} ·
          {{ inspection.evil ? "악" : "선" }} 진영
        </p>
      </div>
    </div>
  </section>
</template>
