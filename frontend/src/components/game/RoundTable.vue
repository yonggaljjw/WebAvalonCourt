<!-- 좌석 순서는 서버 배열 그대로, 위치만 화면 크기에 맞춰 계산합니다. -->
<script setup>
import PlayerSeat from "./PlayerSeat.vue";
const props = defineProps({
  players: Array,
  meId: String,
  phase: String,
  leader: String,
  host: String,
  team: Array,
  submitted: Array,
  selected: Array,
  selectable: Boolean,
  lady: String,
  ladyEnabled: Boolean,
  required: Number,
  rejected: Number,
});
const emit = defineEmits(["select"]);
function position(index) {
  const angle = ((-90 + (360 * index) / props.players.length) * Math.PI) / 180;
  return {
    "--seat-x": `${50 + 39 * Math.cos(angle)}%`,
    "--seat-y": `${50 + 35 * Math.sin(angle)}%`,
  };
}
</script>
<template>
  <div class="table-area" :class="{ 'can-select': selectable }">
    <div class="table-surface" aria-hidden="true">
      <img
        src="/assets/remaster/board/round-table.webp"
        alt=""
        width="1536"
        height="1024"
      />
    </div>
    <div class="table-center">
      <p class="eyebrow">THE ROUND TABLE</p>
      <h2>
        {{
          phase === "lobby"
            ? "서약의 원탁"
            : players.find((p) => p.id === leader)?.name + "의 원정"
        }}
      </h2>
      <p>
        {{
          phase === "lobby"
            ? "기사들의 서약을 기다립니다"
            : `원정대 ${required}명 · 연속 부결 ${rejected}/5`
        }}
      </p>
      <span class="table-hint">{{
        selectable
          ? "함께할 기사를 선택하세요"
          : "충성은 맹세하고, 정체는 감추십시오"
      }}</span>
    </div>
    <div class="seats" :aria-label="`${players.length}명의 공개 좌석`">
      <PlayerSeat
        v-for="(player, index) in players"
        :key="player.id"
        :style="position(index)"
        :player="{
          id: player.id,
          name: player.name,
          connected: player.connected,
        }"
        :index="index"
        :mine="player.id === meId"
        :leader="player.id === leader && phase !== 'lobby'"
        :host="player.id === host"
        :lobby="phase === 'lobby'"
        :ready="player.ready"
        :submitted="submitted.includes(player.id)"
        :selected="selected.includes(player.id)"
        :nominated="team.includes(player.id)"
        :selectable="selectable"
        :lady="ladyEnabled && player.id === lady"
        @select="emit('select', $event)"
      />
    </div>
  </div>
</template>
