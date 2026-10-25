<script setup>
defineProps({ quests: Array, round: Number, count: Number });
</script>
<template>
  <div class="quest-track" aria-label="원정 진행 기록">
    <div
      v-for="(_, i) in 5"
      :key="i"
      :class="{
        success: quests[i]?.success,
        fail: quests[i] && !quests[i].success,
        current: i === round - 1,
      }"
    >
      <span class="quest-medallion"
        ><img
          v-if="quests[i]"
          :src="`/assets/remaster/tokens/quest-${quests[i].success ? 'success' : 'failure'}.webp`"
          alt=""
          width="512"
          height="512"
        /><b v-else>{{ String(i + 1).padStart(2, "0") }}</b></span
      >
      <small
        >{{ i + 1 }}차 원정
        <b v-if="quests[i]"
          >· {{ quests[i].success ? "성공" : "실패" }}</b
        ></small
      >
      <small v-if="i === 3 && count >= 7" class="threshold"
        >실패 2장 필요</small
      >
    </div>
  </div>
</template>
