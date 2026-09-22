<script setup>
import { roleImage, roleNames } from "../../constants/game.js";

defineProps({ room: { type: Object, required: true } });
const emit = defineEmits(["leave"]);
</script>

<template>
  <div class="result" :class="room.winner">
    <p class="eyebrow">THE FINAL VERDICT</p>
    <h1>
      {{
        room.winner === "aborted"
          ? "원정 무효 종료"
          : room.winner === "good"
            ? "아서의 기사들이 승리했습니다"
            : "어둠이 아발론을 삼켰습니다"
      }}
    </h1>
    <p>{{ room.reason }}</p>
    <div class="result-roles">
      <article v-for="player in room.players" :key="player.id" class="result-role">
        <img
          :src="roleImage(player.role)"
          :alt="roleNames[player.role] + ' 역할 초상화'"
          width="1024"
          height="1536"
          loading="lazy"
        />
        <div>
          <strong>{{ player.name }}</strong>
          <p>{{ roleNames[player.role] }}</p>
        </div>
      </article>
    </div>
    <button class="gold" @click="emit('leave')">로비로 돌아가기</button>
  </div>
</template>
