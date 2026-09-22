<!-- 학습용 주석: 현재 플레이어의 역할과 본인만 알 수 있는 정보를 표시합니다. -->
<script setup>
import { ref } from "vue";
import {
  roleDescriptions,
  roleImage,
  roleNames,
} from "../../constants/game.js";

// props: 부모 컴포넌트가 이 컴포넌트에 내려주는 입력값입니다.
defineProps({ room: { type: Object, required: true } });
// 역할 정보는 기본적으로 가리고 사용자가 직접 눌렀을 때만 보여줍니다.
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
