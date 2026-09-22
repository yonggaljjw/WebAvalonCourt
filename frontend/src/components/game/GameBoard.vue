<!-- 학습용 주석: 게임의 현재 단계에 맞는 행동 UI를 보여주는 핵심 컴포넌트입니다. -->
<script setup>
import { computed, ref, watch } from "vue";
import { phases } from "../../constants/game.js";
import GameResult from "./GameResult.vue";

// props: 부모가 내려준 값을 script에서도 여러 번 참조하므로 변수로 받아 사용합니다.
const props = defineProps({
  room: { type: Object, required: true },
  seconds: { type: Number, required: true },
  host: { type: Boolean, required: true },
  myPlayer: { type: Object, default: null },
});
// emit: 자식이 직접 부모 상태를 바꾸지 않고 사용자 행동을 이벤트로 알립니다.
const emit = defineEmits(["send", "leave"]);

// 대장이 원정대 구성 단계에서 선택 중인 플레이어 ID 목록입니다.
const selected = ref([]);
// 현재 내가 원정대장이고 proposal 단계인지 계산해 선택 가능 여부를 만듭니다.
const canSelect = computed(
  () =>
    (props.room.phase === "proposal" &&
      props.room.leader === props.room.me.id) ||
    (props.room.phase === "assassination" &&
      props.room.me.role === "assassin") ||
    (props.room.phase === "lady" && props.room.lady === props.room.me.id),
);
// 현재 단계에서 내가 이미 투표/카드를 제출했는지 확인합니다.
const submitted = computed(() =>
  props.room.submitted.includes(props.room.me.id),
);
const playerName = (id) =>
  props.room.players.find((player) => player.id === id)?.name || "퇴장한 기사";

watch(
  [() => props.room.phase, () => props.room.round],
  () => (selected.value = []),
);

// 원정대 인원 수 제한을 지키면서 플레이어 선택/해제를 토글합니다.
function select(id) {
  if (!canSelect.value) return;
  if (props.room.phase === "proposal") {
    selected.value = selected.value.includes(id)
      ? selected.value.filter((value) => value !== id)
      : [...selected.value, id];
  } else {
    selected.value = [id];
  }
}
</script>

<template>
  <div class="phase-banner">
    <div>
      <small>ROUND {{ Math.min(room.round, 5) }} / 5</small>
      <h2>{{ phases[room.phase] }}</h2>
    </div>
    <strong v-if="!['lobby', 'ended'].includes(room.phase)">
      {{ room.paused ? "일시 정지" : seconds + "초" }}
    </strong>
    <span v-else>{{ room.players.length }} / {{ room.settings.capacity }} 명</span>
  </div>

  <GameResult v-if="room.phase === 'ended'" :room="room" @leave="emit('leave')" />

  <template v-else>
    <div class="quest-track">
      <div
        v-for="(_, index) in 5"
        :key="index"
        :class="{
          success: room.quests[index]?.success,
          fail: room.quests[index] && !room.quests[index].success,
          current: index === room.round - 1,
        }"
      >
        <span>{{ room.quests[index] ? (room.quests[index].success ? "✓" : "✕") : index + 1 }}</span>
        <small>{{ index + 1 }}차 원정</small>
        <small v-if="index === 3 && room.players.length >= 7">실패 2장 필요</small>
      </div>
    </div>

    <div class="table-area">
      <div class="table-center">
        <p class="eyebrow">THE ROUND TABLE</p>
        <h2>
          {{ room.phase === "lobby" ? "기사들을 기다리는 중" : playerName(room.leader) + "의 원정" }}
        </h2>
        <p>
          {{ room.phase === "lobby" ? "모두 준비하면 방장이 시작합니다." : `원정대 ${room.required}명 · 연속 부결 ${room.rejected}/5` }}
        </p>
      </div>
      <div class="seats">
        <button
          v-for="(player, index) in room.players"
          :key="player.id"
          class="seat"
          :class="{
            selected: selected.includes(player.id),
            nominated: room.team.includes(player.id),
            offline: !player.connected,
          }"
          :aria-pressed="selected.includes(player.id)"
          @click="select(player.id)"
        >
          <span class="seat-top">
            {{
              player.id === room.leader && room.phase !== "lobby"
                ? "♛ 원정대장"
                : player.id === room.host
                  ? "♜ 방장"
                  : `SEAT ${index + 1}`
            }}
          </span>
          <img src="/assets/knight.webp" alt="" />
          <b>{{ player.name }} {{ player.id === room.me.id ? "(나)" : "" }}</b>
          <small>
            {{
              !player.connected
                ? "접속 대기"
                : room.phase === "lobby"
                  ? player.ready
                    ? "준비 완료"
                    : "준비 중"
                  : room.submitted.includes(player.id)
                    ? "제출 완료"
                    : room.team.includes(player.id)
                      ? "원정대원"
                      : "회의 참여"
            }}
          </small>
          <small v-if="room.settings.lady && player.id === room.lady">♧ 호수의 여인</small>
        </button>
      </div>
    </div>

    <section v-if="!room.paused" class="actions">
      <template v-if="room.phase === 'lobby'">
        <button class="gold" @click="emit('send', 'ready', { ready: !myPlayer?.ready })">
          {{ myPlayer?.ready ? "준비 취소" : "준비 완료" }}
        </button>
        <button
          v-if="host"
          class="blue"
          :disabled="room.players.length < 5 || room.players.some((player) => !player.ready || !player.connected)"
          @click="emit('send', 'start')"
        >
          ⚔ 원정 시작
        </button>
        <p>최소 5명 · 모든 기사 준비 필요</p>
      </template>

      <template v-else-if="room.phase === 'proposal'">
        <p>
          {{ canSelect ? "아래 원정에 함께할 기사를 선택하세요." : "원정대장이 팀을 구성하고 있습니다. 채팅으로 의견을 나누세요." }}
        </p>
        <button
          v-if="canSelect"
          class="gold"
          :disabled="selected.length !== room.required"
          @click="emit('send', 'propose', { team: selected })"
        >
          원정대 제안 · {{ selected.length }} / {{ room.required }}
        </button>
      </template>

      <template v-else-if="room.phase === 'vote'">
        <h3>이 원정대를 신뢰하십니까?</h3>
        <p>{{ room.team.map(playerName).join(" · ") }}</p>
        <template v-if="!submitted">
          <button class="blue" @click="emit('send', 'vote', { approve: true })">찬성 · APPROVE</button>
          <button class="red" @click="emit('send', 'vote', { approve: false })">반대 · REJECT</button>
        </template>
        <p v-else>투표 완료 · 다른 기사들을 기다립니다.</p>
      </template>

      <template v-else-if="room.phase === 'quest'">
        <h3>원정 카드 제출</h3>
        <p>카드 작성자는 공개되지 않습니다.</p>
        <template v-if="room.team.includes(room.me.id) && !submitted">
          <button class="blue" @click="emit('send', 'quest', { success: true })">원정 성공</button>
          <button v-if="room.me.evil" class="red" @click="emit('send', 'quest', { success: false })">원정 실패</button>
        </template>
        <p v-else>{{ submitted ? "카드를 제출했습니다." : "원정대의 귀환을 기다립니다." }}</p>
      </template>

      <template v-else-if="room.phase === 'assassination'">
        <p>선 진영의 원정이 세 번 성공했습니다. 암살자가 멀린을 찾으면 악 진영의 승리입니다.</p>
        <button
          v-if="canSelect"
          class="red"
          :disabled="selected.length !== 1"
          @click="emit('send', 'assassinate', { target: selected[0] })"
        >
          {{ selected.length ? playerName(selected[0]) + " 암살 확정" : "암살 대상을 선택하세요" }}
        </button>
      </template>

      <template v-else-if="room.phase === 'lady'">
        <p>
          {{ playerName(room.lady) }} 님이 한 명의 진영을 비공개로 조사합니다. 이전 보유자는 선택할 수 없습니다.
        </p>
        <button
          v-if="canSelect"
          class="gold"
          :disabled="selected.length !== 1 || room.lady_used.includes(selected[0])"
          @click="emit('send', 'lady', { target: selected[0] })"
        >
          진영 조사
        </button>
      </template>
    </section>
  </template>
</template>
