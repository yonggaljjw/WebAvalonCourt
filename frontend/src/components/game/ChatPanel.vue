<!-- 학습용 주석: 게임 채팅/기록 패널. 채팅 자동 스크롤과 읽지 않은 메시지 상태를 관리합니다. -->
<script setup>
import { nextTick, onMounted, ref, watch } from "vue";

// props: 부모가 내려준 값을 script에서도 여러 번 참조하므로 변수로 받아 사용합니다.
const props = defineProps({ room: { type: Object, required: true } });
// emit: 자식이 직접 부모 상태를 바꾸지 않고 사용자 행동을 이벤트로 알립니다.
const emit = defineEmits(["send"]);

// 채팅/게임 기록 중 현재 보고 있는 탭과 입력값을 로컬 상태로 관리합니다.
const tab = ref("chat");
const message = ref("");
const chatBox = ref(null);
const unread = ref(false);

const isMine = (entry) =>
  Boolean(entry.sender_id) && entry.sender_id === props.room.me.id;
const chatTime = (entry) =>
  new Date(entry.at * 1000).toLocaleTimeString("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
  });
const playerName = (id) =>
  props.room.players.find((player) => player.id === id)?.name || "퇴장한 기사";

// 채팅 컨테이너의 스크롤을 가장 아래로 이동합니다.
function bottom() {
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight;
  unread.value = false;
}

// 사용자가 과거 메시지를 보는 중인지 판단해 자동 스크롤 여부를 결정합니다.
function scrollChat() {
  const element = chatBox.value;
  if (
    element &&
    element.scrollHeight - element.scrollTop - element.clientHeight < 70
  ) {
    unread.value = false;
  }
}

// 빈 문자열을 제외하고 상위 컴포넌트로 chat 행동을 전달합니다.
function submitChat() {
  if (!message.value.trim()) return;
  emit("send", "chat", { message: message.value });
  message.value = "";
}

// 탭을 채팅으로 전환한 뒤 DOM 렌더링이 끝나면 최신 메시지 위치로 이동합니다.
watch(tab, () => nextTick(bottom));
watch(
  () => props.room,
  async (after, before) => {
    if (!after) return;
    const element = chatBox.value;
    const nearBottom =
      !element ||
      element.scrollHeight - element.scrollTop - element.clientHeight < 70;
    const last = after.chat.at(-1);
    const previousLast = before?.chat.at(-1);
    const newMessage =
      last && (last.id || last.at) !== (previousLast?.id || previousLast?.at);
    const ownMessage = newMessage && last.sender_id === after.me.id;
    const shouldScroll = !before || nearBottom || ownMessage;

    await nextTick();
    if (shouldScroll) bottom();
    else if (newMessage) unread.value = true;
  },
);

onMounted(() => nextTick(bottom));
</script>

<template>
  <aside class="discourse panel">
    <div class="tabs">
      <button :class="{ active: tab === 'chat' }" @click="tab = 'chat'">
        원탁의 대화
      </button>
      <button :class="{ active: tab === 'history' }" @click="tab = 'history'">
        원정 기록
      </button>
    </div>

    <div v-if="tab === 'chat'" ref="chatBox" class="messages chat-messages" role="log" aria-label="원탁 채팅"
      aria-live="polite" @scroll="scrollChat">
      <p class="system">
        정체는 숨기고, 의견은 나누세요.<br />모든 참가자에게 보이는 대화입니다.
      </p>
      <article v-for="(entry, index) in room.chat" :key="entry.id || index" class="chat-message"
        :class="{ mine: isMine(entry) }">
        <b>{{ isMine(entry) ? "나" : entry.name }}</b>
        <div class="bubble-row">
          <p class="bubble">{{ entry.message }}</p>
          <time :datetime="new Date(entry.at * 1000).toISOString()">{{
            chatTime(entry)
          }}</time>
        </div>
      </article>
      <p v-if="!room.chat.length" class="muted">첫 대화를 시작해보세요.</p>
    </div>

    <div v-else class="messages">
      <article v-for="(quest, index) in room.quests" :key="'q' + index">
        <b>{{ index + 1 }}차 원정 · {{ quest.success ? "성공" : "실패" }}</b>
        <p>실패 카드 {{ quest.fails }}장</p>
      </article>
      <article v-for="(history, index) in room.history" :key="index">
        <!-- 이번 원정대 제안의 최종 승인/부결 결과 -->
        <b>
          {{ history.round }}차 원정 ·
          {{ history.approved ? "승인" : "부결" }}
        </b>

        <!-- 원정대장이 제안했던 원정대 구성 -->
        <p>팀: {{ history.team.map(playerName).join(", ") }}</p>

        <!--
          개인별 투표 결과는 공개하지 않습니다.
          전체 찬성/반대 인원수만 표시합니다.
        -->
        <p>
          찬성 {{ history.approve_count }}명 · 반대 {{ history.reject_count }}명
        </p>
      </article>
      <p v-if="!room.history.length" class="muted">아직 기록이 없습니다.</p>
    </div>

    <button v-if="unread && tab === 'chat'" class="new-message" @click="bottom">
      새 메시지 ↓
    </button>
    <form class="chat-form" @submit.prevent="submitChat">
      <input v-model="message" maxlength="300" placeholder="원탁에 전할 말…" aria-label="채팅 메시지" />
      <button class="gold" :disabled="!message.trim()">전송</button>
    </form>
  </aside>
</template>
