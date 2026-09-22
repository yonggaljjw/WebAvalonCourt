<script setup>
import { ref } from "vue";
import {
  roleDescriptions,
  roleImage,
  roleNames,
} from "../../constants/game.js";

defineProps({ room: { type: Object, required: true } });
const reveal = ref(false);
</script>

<template>
  <section v-if="room.me.role && room.phase !== 'ended'" class="identity panel">
    <div>
      <span class="eyebrow">YOUR SECRET IDENTITY</span>
      <h3>{{ reveal ? roleNames[room.me.role] : "당신의 정체는 봉인되어 있습니다" }}</h3>
    </div>
    <button @click="reveal = !reveal">
      {{ reveal ? "정체 숨기기" : "나의 역할 확인" }}
    </button>
    <div v-if="reveal" class="secret">
      <img
        class="secret-portrait"
        :src="roleImage(room.me.role)"
        :alt="roleNames[room.me.role] + ' 역할 초상화'"
        width="1024"
        height="1536"
      />
      <div class="secret-description">
        <p>{{ roleDescriptions[room.me.role] }}</p>
        <p v-for="knowledge in room.me.knowledge" :key="knowledge.id">
          {{ knowledge.name }} · {{ knowledge.label }}
        </p>
        <p v-for="(inspection, index) in room.me.inspections" :key="index">
          조사 결과: {{ inspection.name }} · {{ inspection.evil ? "악" : "선" }} 진영
        </p>
      </div>
    </div>
  </section>
</template>
