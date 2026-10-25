<!-- 학습용 주석: 게임 종료 후 승패와 전체 역할을 공개하는 결과 컴포넌트입니다. -->
<script setup>
import RolePortrait from "./RolePortrait.vue";
import { roleImage, roleNames } from "../../constants/game.js";

// props: 부모 컴포넌트가 이 컴포넌트에 내려주는 입력값입니다.
defineProps({ room: { type: Object, required: true } });
// emit: 자식이 직접 부모 상태를 바꾸지 않고 사용자 행동을 이벤트로 알립니다.
const emit = defineEmits(["leave"]);
</script>

<template>
  <div v-if="room.phase === 'ended'" class="result" :class="room.winner">
    <div class="result-verdict">
      <img
        class="result-emblem"
        :src="
          room.winner === 'evil'
            ? '/assets/remaster/tokens/quest-failure.webp'
            : '/assets/remaster/emblems/royal-crest.webp'
        "
        alt=""
        width="512"
        height="512"
      />
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
    </div>
    <div class="result-roles">
      <article
        v-for="player in room.players"
        :key="player.id"
        class="result-role"
      >
        <RolePortrait
          :role="player.role"
          sizes="(max-width: 767px) 42vw, 150px"
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
