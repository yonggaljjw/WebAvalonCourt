<script setup>
import { nextTick, onMounted, ref, watch } from "vue";

const props = defineProps({ room: { type: Object, required: true } });
const emit = defineEmits(["send"]);

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

function bottom() {
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight;
  unread.value = false;
}

function scrollChat() {
  const element = chatBox.value;
  if (
    element &&
    element.scrollHeight - element.scrollTop - element.clientHeight < 70
  ) {
    unread.value = false;
  }
}

function submitChat() {
  if (!message.value.trim()) return;
  emit("send", "chat", { message: message.value });
  message.value = "";
}

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
      <button :class="{ active: tab === 'chat' }" @click="tab = 'chat'">원탁의 대화</button>
      <button :class="{ active: tab === 'history' }" @click="tab = 'history'">원정 기록</button>
    </div>

    <div
      v-if="tab === 'chat'"
      ref="chatBox"
      class="messages chat-messages"
      role="log"
      aria-label="원탁 채팅"
      aria-live="polite"
      @scroll="scrollChat"
    >
      <p class="system">
        정체는 숨기고, 의견은 나누세요.<br />모든 참가자에게 보이는 대화입니다.
      </p>
      <article
        v-for="(entry, index) in room.chat"
        :key="entry.id || index"
        class="chat-message"
        :class="{ mine: isMine(entry) }"
      >
        <b>{{ isMine(entry) ? "나" : entry.name }}</b>
        <div class="bubble-row">
          <p class="bubble">{{ entry.message }}</p>
          <time :datetime="new Date(entry.at * 1000).toISOString()">{{ chatTime(entry) }}</time>
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
        <b>{{ history.round }}차 원정 · {{ history.approved ? "승인" : "부결" }}</b>
        <p>팀: {{ history.team.map(playerName).join(", ") }}</p>
        <p v-for="(vote, id) in history.votes" :key="id">
          {{ playerName(id) }} · {{ vote ? "찬성" : "반대" }}
        </p>
      </article>
      <p v-if="!room.history.length" class="muted">아직 기록이 없습니다.</p>
    </div>

    <button v-if="unread && tab === 'chat'" class="new-message" @click="bottom">
      새 메시지 ↓
    </button>
    <form class="chat-form" @submit.prevent="submitChat">
      <input
        v-model="message"
        maxlength="300"
        placeholder="원탁에 전할 말…"
        aria-label="채팅 메시지"
      />
      <button class="gold" :disabled="!message.trim()">전송</button>
    </form>
  </aside>
</template>
