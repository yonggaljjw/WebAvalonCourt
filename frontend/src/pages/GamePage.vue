<!-- 학습용 주석: 게임 화면 페이지. 게임 보드, 역할 정보, 설정, 채팅 컴포넌트를 배치하는 조립 역할을 합니다. -->
<script setup>
import ChatPanel from "../components/game/ChatPanel.vue";
import GameBoard from "../components/game/GameBoard.vue";
import IdentityPanel from "../components/game/IdentityPanel.vue";
import LobbySettings from "../components/game/LobbySettings.vue";

// props: 부모 컴포넌트가 이 컴포넌트에 내려주는 입력값입니다.
defineProps({
  room: { type: Object, default: null },
  connection: { type: String, required: true },
  seconds: { type: Number, required: true },
  host: { type: Boolean, required: true },
  myPlayer: { type: Object, default: null },
  settings: { type: Object, required: true },
});
// emit: 자식이 직접 부모 상태를 바꾸지 않고 사용자 행동을 이벤트로 알립니다.
const emit = defineEmits([
  "back",
  "copy",
  "leave",
  "send",
  "save-settings",
]);
</script>

<template>
  <div v-if="!room" class="panel">
    <h2>{{ connection }}</h2>
    <button @click="emit('back')">로비로 돌아가기</button>
  </div>

  <template v-else>
    <section class="room-heading">
      <div>
        <p class="eyebrow">{{ room.code }} · {{ connection }}</p>
        <h1>{{ room.title }}</h1>
      </div>
      <div>
        <button @click="emit('copy')">초대 링크 복사</button>
        <button @click="emit('leave')">방 나가기</button>
      </div>
    </section>

    <div v-if="room.paused" class="notice">
      재접속 확인 중 · 모든 진행을 일시 정지했습니다.
      {{ room.settings.reconnect_seconds }}초 내 복귀하지 않으면 무효 종료됩니다.
    </div>

    <!-- 왼쪽은 게임 진행, 오른쪽은 채팅으로 나누는 큰 레이아웃입니다. -->
    <div class="game-layout">
      <section class="play-column">
        <GameBoard
          :room="room"
          :seconds="seconds"
          :host="host"
          :my-player="myPlayer"
          @send="(action, data) => emit('send', action, data)"
          @leave="emit('leave')"
        />
        <IdentityPanel :room="room" />
        <LobbySettings
          v-if="room.phase === 'lobby'"
          :settings="settings"
          :host="host"
          @save="(value) => emit('save-settings', value)"
        />
      </section>

      <ChatPanel :room="room" @send="(action, data) => emit('send', action, data)" />
    </div>
  </template>
</template>
