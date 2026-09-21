<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from "vue";
import { AvalonAudio, transitionCue } from "./audio.js";
const names = {
  merlin: "멀린",
  percival: "퍼시벌",
  servant: "충성스러운 신하",
  assassin: "암살자",
  morgana: "모르가나",
  mordred: "모드레드",
  oberon: "오베론",
  minion: "악의 하수인",
};
// 역할 이미지는 도감, 본인의 비밀 확인, 종료 결과에서만 사용합니다.
// 다른 참가자의 진행 중 좌석에는 역할 이미지를 연결하지 않습니다.
const roleImage = (role) =>
  Object.hasOwn(names, role)
    ? `/assets/roles/${role}.png`
    : "/assets/knight.webp";
const descriptions = {
  merlin:
    "모드레드를 제외한 악 진영을 알고 있습니다. 정체를 숨긴 채 원정을 이끄세요.",
  percival: "멀린과 모르가나 후보를 알지만 둘을 구별할 수 없습니다.",
  servant: "대화와 투표 기록으로 동료를 찾아 원정을 성공시키세요.",
  assassin: "원정이 3회 성공하면 멀린을 찾아 암살할 마지막 기회가 있습니다.",
  morgana: "퍼시벌에게 멀린 후보로 보입니다. 혼란을 만드세요.",
  mordred: "멀린에게 정체가 보이지 않는 악의 지도자입니다.",
  oberon: "다른 악 진영과 서로 알아보지 못합니다. 멀린에게는 보입니다.",
  minion: "악의 동료와 협력해 원정을 실패시키세요.",
};
const phases = {
  lobby: "원정 준비",
  proposal: "원정대 구성 · 토론",
  vote: "원정대 승인 투표",
  quest: "원정 수행",
  lady: "호수의 여인 · 조사",
  assassination: "최후의 선택 · 멀린 암살",
  ended: "원정 종료",
};
const page = ref("lobby"),
  user = ref(null),
  nickname = ref(""),
  rooms = ref([]),
  room = ref(null),
  error = ref(""),
  busy = ref(false),
  connection = ref(""),
  reveal = ref(false),
  selected = ref([]),
  message = ref(""),
  filter = ref(""),
  tab = ref("chat"),
  now = ref(Date.now() / 1000),
  offset = ref(0),
  showCreate = ref(false),
  joinCode = ref(""),
  password = ref(""),
  title = ref("원탁의 기사들"),
  settings = ref({
    capacity: 10,
    roles: ["percival", "morgana"],
    lady: false,
    discussion_seconds: 180,
    vote_seconds: 60,
    reconnect_seconds: 30,
  });
// 소리 설정은 기기에만 저장하고, 개인 식별은 서버가 붙인 sender_id를 사용합니다.
const sound = new AvalonAudio(),
  soundOn = ref(false),
  musicVolume = ref(25),
  effectVolume = ref(50),
  chatBox = ref(null),
  unread = ref(false);
try {
  const saved = JSON.parse(localStorage.getItem("avalon_audio") || "{}");
  musicVolume.value = saved.music ?? 25;
  effectVolume.value = saved.effects ?? 50;
} catch { }
function updateVolume() {
  sound.volumes(musicVolume.value / 100, effectVolume.value / 100);
  try {
    localStorage.setItem(
      "avalon_audio",
      JSON.stringify({ music: musicVolume.value, effects: effectVolume.value }),
    );
  } catch { }
}
async function toggleSound() {
  try {
    if (soundOn.value) {
      sound.disable();
      soundOn.value = false;
    } else {
      updateVolume();
      sound.scene(room.value);
      await sound.enable();
      soundOn.value = true;
      sound.cue("resume");
    }
  } catch (e) {
    error.value = e.message;
  }
}
const isMine = (m) => Boolean(m.sender_id) && m.sender_id === room.value?.me.id;
const chatTime = (m) =>
  new Date(m.at * 1000).toLocaleTimeString("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
  });
function bottom() {
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight;
  unread.value = false;
}
function scrollChat() {
  const el = chatBox.value;
  if (el && el.scrollHeight - el.scrollTop - el.clientHeight < 70)
    unread.value = false;
}
function submitChat() {
  if (message.value.trim() && socket?.readyState === 1) {
    send("chat", { message: message.value });
    message.value = "";
  }
}
function visibility() {
  sound.visibility();
}
watch([page, tab], () => nextTick(bottom));
let socket,
  heartbeat,
  polling,
  clock,
  reconnect,
  stopped = false;
const filtered = computed(() =>
  rooms.value.filter(
    (r) =>
      r.title.includes(filter.value) ||
      r.code.includes(filter.value.toUpperCase()),
  ),
);
const myPlayer = computed(() =>
  room.value?.players.find((p) => p.id === room.value.me.id),
);
const host = computed(() => room.value?.host === room.value?.me.id);
const canSelect = computed(
  () =>
    room.value &&
    ((room.value.phase === "proposal" &&
      room.value.leader === room.value.me.id) ||
      (room.value.phase === "assassination" &&
        room.value.me.role === "assassin") ||
      (room.value.phase === "lady" && room.value.lady === room.value.me.id)),
);
const seconds = computed(() =>
  Math.max(
    0,
    Math.ceil((room.value?.deadline || 0) - now.value - offset.value),
  ),
);
const submitted = computed(() =>
  room.value?.submitted.includes(room.value.me.id),
);
const playerName = (id) =>
  room.value?.players.find((p) => p.id === id)?.name || "퇴장한 기사";
// 쿠키는 HttpOnly로 서버가 관리합니다. 브라우저 저장소에는 방 코드만 남깁니다.
async function api(path, method = "GET", body) {
  const res = await fetch("/api" + path, {
    method,
    headers: { "Content-Type": "application/json" },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const data = await res.json();
  if (!res.ok)
    throw Error(
      typeof data.detail === "string" ? data.detail : "입력값을 확인해주세요.",
    );
  return data;
}
async function run(fn) {
  if (busy.value) return;
  busy.value = true;
  error.value = "";
  try {
    await fn();
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}
async function refresh() {
  try {
    rooms.value = await api("/rooms");
  } catch (e) {
    error.value = "서버에 연결할 수 없습니다. 잠시 후 새로고침해주세요.";
  }
}
async function guest() {
  user.value = await api("/guest", "POST", { name: nickname.value });
}
async function create() {
  if (!user.value) await guest();
  const r = await api("/rooms", "POST", {
    title: title.value,
    password: password.value,
    settings: settings.value,
  });
  showCreate.value = false;
  openRoom(r.code);
}
async function join(code) {
  if (!user.value) await guest();
  await api("/rooms/" + code + "/join", "POST", { password: password.value });
  openRoom(code);
  joinCode.value = "";
}
function openRoom(code) {
  reveal.value = false;
  stopped = false;
  localStorage.setItem("avalon_room", code);
  page.value = "game";
  connect(code);
}
// 주기적인 ping으로 실제 연결을 확인하고, 끊긴 경우 동일 세션으로 재접속합니다.
function connect(code) {
  connection.value = "연결 중";
  let firstState = true;
  socket = new WebSocket(
    `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/${code}`,
  );
  socket.onopen = () => {
    connection.value = "실시간 연결";
    clearInterval(heartbeat);
    heartbeat = setInterval(() => {
      if (socket?.readyState === 1)
        socket.send(JSON.stringify({ action: "ping" }));
    }, 4000);
  };
  socket.onmessage = async (e) => {
    const d = JSON.parse(e.data);
    if (d.type === "error") {
      error.value = d.message;
      return;
    }
    if (d.type !== "state") return;

    const previous = room.value;
    if (previous?.phase !== d.room.phase || previous?.round !== d.room.round) {
      selected.value = [];
    }
    const cue = firstState ? null : transitionCue(previous, d.room);
    firstState = false;
    sound.scene(d.room);
    if (cue) sound.cue(cue);

    // 화면 갱신 전 위치를 기준으로, 지난 대화를 읽는 중인지 판단합니다.
    const el = chatBox.value;
    const nearBottom =
      !el || el.scrollHeight - el.scrollTop - el.clientHeight < 70;
    const last = d.room.chat.at(-1);
    const previousLast = previous?.chat.at(-1);
    const newMessage =
      last && (last.id || last.at) !== (previousLast?.id || previousLast?.at);
    const ownMessage = newMessage && last.sender_id === d.room.me.id;
    const shouldScroll = !previous || nearBottom || ownMessage;
    const changed =
      JSON.stringify(previous?.settings) !== JSON.stringify(d.room.settings);

    // 반드시 상태 변경 → Vue 화면 반영 완료 → 스크롤 순서로 처리합니다.
    room.value = d.room;
    offset.value = d.room.server_time - Date.now() / 1000;
    if (changed) settings.value = structuredClone(d.room.settings);
    await nextTick();

    if (shouldScroll) bottom();
    else if (newMessage) unread.value = true;
  };
  socket.onclose = (e) => {
    if (!stopped && room.value) sound.scene({ ...room.value, paused: true });
    clearInterval(heartbeat);
    connection.value = "연결 끊김";
    if (e.code === 4001) {
      stopped = true;
      error.value = "다른 창에서 접속했습니다. 한 창에서만 플레이해주세요.";
    }
    if (e.code === 1008) {
      stopped = true;
      error.value =
        "입장 정보를 확인할 수 없습니다. 로비로 돌아가 다시 입장해주세요.";
    }
    if (!stopped) reconnect = setTimeout(() => connect(code), 2000);
  };
}
// 승패·역할·타이머 판단은 서버가 담당합니다. 화면은 행동 의도만 보냅니다.
function send(action, data = {}) {
  error.value = "";
  if (socket?.readyState !== 1) {
    error.value = "서버에 재연결 중입니다.";
    return;
  }
  socket.send(JSON.stringify({ action, ...data }));
}
// 원정대 구성은 여러 명을, 조사와 암살은 한 명을 선택합니다.
function select(id) {
  if (!canSelect.value) return;
  if (room.value.phase === "proposal") {
    selected.value = selected.value.includes(id)
      ? selected.value.filter((x) => x !== id)
      : [...selected.value, id];
  } else selected.value = [id];
}
async function leave() {
  if (room.value && !stopped) {
    try {
      await api("/rooms/" + room.value.code + "/leave", "POST");
    } catch (e) {
      if (
        ![
          "방을 찾을 수 없습니다.",
          "이 방의 참가자가 아닙니다.",
          "이미 퇴장한 방입니다.",
        ].includes(e.message)
      )
        throw e;
    }
  }
  disconnect();
  room.value = null;
  page.value = "lobby";
  localStorage.removeItem("avalon_room");
  await refresh();
}
function disconnect() {
  sound.scene(null);
  stopped = true;
  clearTimeout(reconnect);
  clearInterval(heartbeat);
  socket?.close();
}
async function saveSettings() {
  await api("/rooms/" + room.value.code + "/settings", "PUT", settings.value);
}
async function copy() {
  try {
    await navigator.clipboard.writeText(
      location.origin + "/?room=" + room.value.code,
    );
  } catch {
    error.value = "초대 코드: " + room.value.code;
  }
}
onMounted(async () => {
  document.addEventListener("visibilitychange", visibility);
  try {
    user.value = await api("/me");
  } catch { }
  await refresh();
  const invite = new URLSearchParams(location.search).get("room");
  if (invite) joinCode.value = invite.toUpperCase();
  else {
    const code = localStorage.getItem("avalon_room");
    if (code && user.value) openRoom(code);
  }
  polling = setInterval(() => {
    if (!room.value) refresh();
  }, 5000);
  clock = setInterval(() => (now.value = Date.now() / 1000), 1000);
});
onUnmounted(() => {
  disconnect();
  sound.close();
  document.removeEventListener("visibilitychange", visibility);
  clearInterval(polling);
  clearInterval(clock);
});
</script>

<template>
  <header class="top">
    <a href="#" class="brand" @click.prevent="page = room ? 'game' : 'lobby'"><img src="/assets/crest.webp"
        alt="아발론 문장" /><span>AVALON <small>THE RESISTANCE</small></span></a>
    <nav>
      <button :class="{ active: page === 'lobby' || page === 'game' }" @click="page = room ? 'game' : 'lobby'">
        {{ room ? "원탁 회의" : "게임 로비" }}</button><button :class="{ active: page === 'rules' }" @click="page = 'rules'">
        게임 방법</button><button :class="{ active: page === 'roles' }" @click="page = 'roles'">
        역할 도감
      </button>
    </nav>
    <span class="profile">{{ user?.name || "이름 없는 기사" }}</span>
  </header>
  <main>
    <section class="sound-controls" aria-label="소리 설정">
      <button :aria-pressed="soundOn" @click="toggleSound">
        {{ soundOn ? "소리 끄기" : "♫ 소리 켜기" }}</button><label>배경음 {{ musicVolume }}%<input type="range" min="0" max="100"
          v-model.number="musicVolume" @input="updateVolume" aria-label="배경음 볼륨" /></label><label>효과음 {{ effectVolume
        }}%<input type="range" min="0" max="100" v-model.number="effectVolume" @input="updateVolume"
          aria-label="효과음 볼륨" /></label><small v-if="!soundOn">소리 켜기를 누르면 음악이 시작됩니다.</small>
    </section>
    <div v-if="error" role="alert" class="error">
      {{ error }} <button @click="error = ''" aria-label="알림 닫기">×</button>
    </div>
    <template v-if="page === 'lobby'">
      <section class="intro">
        <div>
          <p class="eyebrow">THE COUNCIL OF CAMELOT</p>
          <h1>충성과 배신 사이,<br />원탁에 앉으십시오.</h1>
          <p>
            누가 아서의 편이고, 누가 어둠의 하수인인가.<br />5–10명의 기사들과
            펼치는 실시간 추리 게임.
          </p>
          <div class="tags">
            <span>회원가입 없이</span><span>실시간 멀티플레이</span><span>5–10인</span>
          </div>
        </div>
        <img src="/assets/knight.webp" alt="어두운 갑옷을 입은 원탁의 기사" />
      </section>
      <div class="lobby-layout">
        <section>
          <div class="section-title">
            <h2>
              열려 있는 원탁 <small>{{ filtered.length }} ROOMS</small>
            </h2>
            <button @click="refresh">새로고침 ↻</button>
          </div>
          <input v-model="filter" aria-label="방 검색" placeholder="방 이름 또는 초대 코드로 검색" class="search" />
          <div class="room-list">
            <article v-for="r in filtered" :key="r.code" class="room-card">
              <div class="room-mark">{{ r.locked ? "♜" : "⚔" }}</div>
              <div class="grow">
                <span class="eyebrow">{{ r.code }} · {{ phases[r.phase] }}</span>
                <h3>{{ r.title }}</h3>
                <small>{{
                  r.roles.map((x) => names[x]).join(" · ") || "기본 역할"
                }}
                  · {{ r.count }} / {{ r.capacity }}명</small>
              </div>
              <button :disabled="r.phase !== 'lobby' || r.count >= r.capacity" @click="
                joinCode = r.code;
              password = '';
              ">
                입장 →
              </button>
            </article>
            <div v-if="!filtered.length" class="empty">
              <span>⚔</span>
              <h3>아직 모인 원탁이 없습니다.</h3>
              <p>첫 번째 방을 열고 동료들을 초대하세요.</p>
              <button class="gold" @click="
                showCreate = true;
              password = '';
              ">
                새로운 원탁 만들기
              </button>
            </div>
          </div>
        </section>
        <aside>
          <section class="panel">
            <p class="eyebrow">YOUR NAME AT THE TABLE</p>
            <h2>원탁으로 입장</h2>
            <label v-if="!user">닉네임<input v-model="nickname" maxlength="16" placeholder="기사의 이름을 입력하세요" /></label>
            <p v-else>{{ user.name }} 님, 원정이 기다립니다.</p>
            <button class="gold wide" @click="
              showCreate = true;
            password = '';
            ">
              ＋ 원탁 만들기</button><button class="wide" @click="
                joinCode = ' ';
              password = '';
              ">
              초대 코드로 참여
            </button>
          </section>
          <section class="panel hint">
            <h3>처음 오셨나요?</h3>
            <p>
              선 진영은 원정 3회 성공을,<br />악 진영은 원정 3회 실패를
              노립니다.<br />하지만 멀린이 발각되면 모든 것이 뒤집힙니다.
            </p>
            <button class="link" @click="page = 'rules'">
              게임 방법 알아보기 →
            </button>
          </section>
        </aside>
      </div>
    </template>
    <template v-if="page === 'game'">
      <div v-if="!room" class="panel">
        <h2>{{ connection }}</h2>
        <button @click="
          disconnect();
        page = 'lobby';
        localStorage.removeItem('avalon_room');
        ">
          로비로 돌아가기
        </button>
      </div>
      <template v-else>
        <section class="room-heading">
          <div>
            <p class="eyebrow">{{ room.code }} · {{ connection }}</p>
            <h1>{{ room.title }}</h1>
          </div>
          <div>
            <button @click="copy">초대 링크 복사</button>
            <button @click="run(leave)">방 나가기</button>
          </div>
        </section>
        <div v-if="room.paused" class="notice">
          재접속 확인 중 · 모든 진행을 일시 정지했습니다.
          {{ room.settings.reconnect_seconds }}초 내 복귀하지 않으면 무효
          종료됩니다.
        </div>
        <div class="game-layout">
          <section class="play-column">
            <div class="phase-banner">
              <div>
                <small>ROUND {{ Math.min(room.round, 5) }} / 5</small>
                <h2>{{ phases[room.phase] }}</h2>
              </div>
              <strong v-if="!['lobby', 'ended'].includes(room.phase)">{{
                room.paused ? "일시 정지" : seconds + "초"
                }}</strong><span v-else>{{ room.players.length }} /
                {{ room.settings.capacity }} 명</span>
            </div>
            <div v-if="room.phase === 'ended'" class="result" :class="room.winner">
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
                <article v-for="p in room.players" :key="p.id" class="result-role">
                  <img :src="roleImage(p.role)" :alt="names[p.role] + ' 역할 초상화'" width="1024" height="1536"
                    loading="lazy" />
                  <div>
                    <strong>{{ p.name }}</strong>
                    <p>{{ names[p.role] }}</p>
                  </div>
                </article>
              </div>
              <button class="gold" @click="run(leave)">로비로 돌아가기</button>
            </div>
            <template v-else>
              <div class="quest-track">
                <div v-for="(_, i) in 5" :key="i" :class="{
                  success: room.quests[i]?.success,
                  fail: room.quests[i] && !room.quests[i].success,
                  current: i === room.round - 1,
                }">
                  <span>{{
                    room.quests[i]
                      ? room.quests[i].success
                        ? "✓"
                        : "✕"
                      : i + 1
                  }}</span><small>{{ i + 1 }}차 원정</small><small v-if="i === 3 && room.players.length >= 7">실패 2장
                    필요</small>
                </div>
              </div>
              <div class="table-area">
                <div class="table-center">
                  <p class="eyebrow">THE ROUND TABLE</p>
                  <h2>
                    {{
                      room.phase === "lobby"
                        ? "기사들을 기다리는 중"
                        : playerName(room.leader) + "의 원정"
                    }}
                  </h2>
                  <p>
                    {{
                      room.phase === "lobby"
                        ? "모두 준비하면 방장이 시작합니다."
                        : `원정대 ${room.required}명 · 연속 부결 ${room.rejected}/5`
                    }}
                  </p>
                </div>
                <div class="seats">
                  <button v-for="(p, i) in room.players" :key="p.id" class="seat" :class="{
                    selected: selected.includes(p.id),
                    nominated: room.team.includes(p.id),
                    offline: !p.connected,
                  }" @click="select(p.id)" :aria-pressed="selected.includes(p.id)">
                    <span class="seat-top">{{
                      p.id === room.leader && room.phase !== "lobby"
                        ? "♛ 원정대장"
                        : p.id === room.host
                          ? "♜ 방장"
                          : `SEAT ${i + 1}`
                    }}</span><img src="/assets/knight.webp" alt="" /><b>{{ p.name }} {{ p.id === room.me.id ? "(나)" :
                      "" }}</b><small>{{
                        !p.connected
                          ? "접속 대기"
                          : room.phase === "lobby"
                            ? p.ready
                              ? "준비 완료"
                              : "준비 중"
                            : room.submitted.includes(p.id)
                              ? "제출 완료"
                              : room.team.includes(p.id)
                                ? "원정대원"
                                : "회의 참여"
                      }}</small><small v-if="room.settings.lady && p.id === room.lady">♧ 호수의 여인</small>
                  </button>
                </div>
              </div>
              <section class="actions" v-if="!room.paused">
                <template v-if="room.phase === 'lobby'"><button class="gold"
                    @click="send('ready', { ready: !myPlayer?.ready })">
                    {{ myPlayer?.ready ? "준비 취소" : "준비 완료" }}</button><button v-if="host" class="blue" :disabled="room.players.length < 5 ||
                      room.players.some((p) => !p.ready || !p.connected)
                      " @click="send('start')">
                    ⚔ 원정 시작
                  </button>
                  <p>최소 5명 · 모든 기사 준비 필요</p>
                </template>
                <template v-else-if="room.phase === 'proposal'">
                  <p>
                    {{
                      canSelect
                        ? "아래 원정에 함께할 기사를 선택하세요."
                        : "원정대장이 팀을 구성하고 있습니다. 채팅으로 의견을 나누세요."
                    }}
                  </p>
                  <button v-if="canSelect" class="gold" :disabled="selected.length !== room.required"
                    @click="send('propose', { team: selected })">
                    원정대 제안 · {{ selected.length }} / {{ room.required }}
                  </button>
                </template>
                <template v-else-if="room.phase === 'vote'">
                  <h3>이 원정대를 신뢰하십니까?</h3>
                  <p>{{ room.team.map(playerName).join(" · ") }}</p>
                  <template v-if="!submitted"><button class="blue" @click="send('vote', { approve: true })">
                      찬성 · APPROVE</button><button class="red" @click="send('vote', { approve: false })">
                      반대 · REJECT
                    </button></template>
                  <p v-else>투표 완료 · 다른 기사들을 기다립니다.</p>
                </template>
                <template v-else-if="room.phase === 'quest'">
                  <h3>원정 카드 제출</h3>
                  <p>카드 작성자는 공개되지 않습니다.</p>
                  <template v-if="room.team.includes(room.me.id) && !submitted"><button class="blue"
                      @click="send('quest', { success: true })">
                      원정 성공</button><button v-if="room.me.evil" class="red" @click="send('quest', { success: false })">
                      원정 실패
                    </button></template>
                  <p v-else>
                    {{
                      submitted
                        ? "카드를 제출했습니다."
                        : "원정대의 귀환을 기다립니다."
                    }}
                  </p>
                </template>
                <template v-else-if="room.phase === 'assassination'">
                  <p>
                    선 진영의 원정이 세 번 성공했습니다. 암살자가 멀린을 찾으면
                    악 진영의 승리입니다.
                  </p>
                  <button v-if="canSelect" class="red" :disabled="selected.length !== 1"
                    @click="send('assassinate', { target: selected[0] })">
                    {{
                      selected.length
                        ? playerName(selected[0]) + " 암살 확정"
                        : "암살 대상을 선택하세요"
                    }}
                  </button>
                </template>
                <template v-else-if="room.phase === 'lady'">
                  <p>
                    {{ playerName(room.lady) }} 님이 한 명의 진영을 비공개로
                    조사합니다. 이전 보유자는 선택할 수 없습니다.
                  </p>
                  <button v-if="canSelect" class="gold" :disabled="selected.length !== 1 ||
                    room.lady_used.includes(selected[0])
                    " @click="send('lady', { target: selected[0] })">
                    진영 조사
                  </button>
                </template>
              </section>
            </template>
            <section v-if="room.me.role && room.phase !== 'ended'" class="identity panel">
              <div>
                <span class="eyebrow">YOUR SECRET IDENTITY</span>
                <h3>
                  {{
                    reveal
                      ? names[room.me.role]
                      : "당신의 정체는 봉인되어 있습니다"
                  }}
                </h3>
              </div>
              <button @click="reveal = !reveal">
                {{ reveal ? "정체 숨기기" : "나의 역할 확인" }}
              </button>
              <div v-if="reveal" class="secret">
                <img class="secret-portrait" :src="roleImage(room.me.role)" :alt="names[room.me.role] + ' 역할 초상화'"
                  width="1024" height="1536" />
                <div class="secret-description">
                  <p>{{ descriptions[room.me.role] }}</p>
                  <p v-for="k in room.me.knowledge" :key="k.id">
                    {{ k.name }} · {{ k.label }}
                  </p>
                  <p v-for="(k, i) in room.me.inspections" :key="i">
                    조사 결과: {{ k.name }} · {{ k.evil ? "악" : "선" }} 진영
                  </p>
                </div>
              </div>
            </section>
            <section v-if="room.phase === 'lobby'" class="panel">
              <h3>
                원탁 설정
                <small>{{
                  host
                    ? "설정 변경 시 모두 준비가 해제됩니다"
                    : "방장이 변경할 수 있습니다"
                }}</small>
              </h3>
              <div class="settings-grid">
                <label>최대 인원<select v-model.number="settings.capacity" :disabled="!host">
                    <option v-for="n in [5, 6, 7, 8, 9, 10]">{{ n }}</option>
                  </select></label><label>토론·구성 시간 (초)<input type="number" v-model.number="settings.discussion_seconds"
                    min="30" max="600" :disabled="!host" /></label><label>투표·행동 시간 (초)<input type="number"
                    v-model.number="settings.vote_seconds" min="15" max="180" :disabled="!host" /></label><label>재접속 유예
                  (초)<input type="number" v-model.number="settings.reconnect_seconds" min="0" max="120"
                    :disabled="!host" /></label>
              </div>
              <div class="checks">
                <label v-for="r in ['percival', 'morgana', 'mordred', 'oberon']"><input type="checkbox"
                    v-model="settings.roles" :value="r" :disabled="!host" />{{ names[r] }}</label><label><input
                    type="checkbox" v-model="settings.lady" :disabled="!host" />호수의 여인</label>
              </div>
              <button v-if="host" @click="run(saveSettings)">설정 저장</button>
            </section>
          </section>
          <aside class="discourse panel">
            <div class="tabs">
              <button :class="{ active: tab === 'chat' }" @click="tab = 'chat'">
                원탁의 대화</button><button :class="{ active: tab === 'history' }" @click="tab = 'history'">
                원정 기록
              </button>
            </div>
            <div v-if="tab === 'chat'" ref="chatBox" class="messages chat-messages" role="log" aria-label="원탁 채팅"
              aria-live="polite" @scroll="scrollChat">
              <p class="system">
                정체는 숨기고, 의견은 나누세요.<br />모든 참가자에게 보이는
                대화입니다.
              </p>
              <article v-for="(m, i) in room.chat" :key="m.id || i" class="chat-message" :class="{ mine: isMine(m) }">
                <b>{{ isMine(m) ? "나" : m.name }}</b>
                <div class="bubble-row">
                  <p class="bubble">{{ m.message }}</p>
                  <time :datetime="new Date(m.at * 1000).toISOString()">{{
                    chatTime(m)
                    }}</time>
                </div>
              </article>
              <p v-if="!room.chat.length" class="muted">
                첫 대화를 시작해보세요.
              </p>
            </div>
            <div v-else class="messages">
              <article v-for="(q, i) in room.quests" :key="'q' + i">
                <b>{{ i + 1 }}차 원정 · {{ q.success ? "성공" : "실패" }}</b>
                <p>실패 카드 {{ q.fails }}장</p>
              </article>
              <article v-for="(h, i) in room.history" :key="i">
                <b>{{ h.round }}차 원정 · {{ h.approved ? "승인" : "부결" }}</b>
                <p>팀: {{ h.team.map(playerName).join(", ") }}</p>
                <p v-for="(v, id) in h.votes">
                  {{ playerName(id) }} · {{ v ? "찬성" : "반대" }}
                </p>
              </article>
              <p v-if="!room.history.length" class="muted">
                아직 기록이 없습니다.
              </p>
            </div>
            <button v-if="unread && tab === 'chat'" class="new-message" @click="bottom">
              새 메시지 ↓
            </button>
            <form @submit.prevent="submitChat" class="chat-form">
              <input v-model="message" maxlength="300" placeholder="원탁에 전할 말…" aria-label="채팅 메시지" /><button
                class="gold" :disabled="!message.trim()">전송</button>
            </form>
          </aside>
        </div>
      </template>
    </template>
    <template v-if="page === 'rules'">
      <section class="page-heading">
        <p class="eyebrow">THE CHRONICLES OF AVALON</p>
        <h1>게임 방법 — 신뢰와 의심 사이</h1>
        <p>5–10명 · 선과 악의 정체를 숨긴 원정</p>
      </section>
      <div class="rules-grid">
        <section class="panel" v-for="(r, i) in [
          [
            '역할 확인',
            '멀린·암살자는 항상 포함됩니다. 선과 악의 인원은 참여 인원에 따라 자동 배분하며, 특수 역할은 방장이 선택합니다.',
          ],
          [
            '원정대 구성',
            '원정대장이 정해진 인원만큼 기사를 선택합니다. 모두 함께 토론한 뒤 팀을 제안합니다.',
          ],
          [
            '승인 투표',
            '모든 참가자가 찬성 또는 반대합니다. 과반 찬성이 필요하며 동수는 부결입니다. 부결 시 다음 사람이 대장이 됩니다. 5회 연속 부결되면 악이 승리합니다.',
          ],
          [
            '원정 수행',
            '원정대원만 비공개 카드를 제출합니다. 선은 성공만, 악은 성공 또는 실패를 낼 수 있습니다. 7명 이상 게임의 4차 원정은 실패 카드 2장, 나머지는 1장이면 실패합니다.',
          ],
          [
            '최후의 암살',
            '원정 3회 실패 시 악이 승리합니다. 3회 성공 시 암살자가 선 진영 한 명을 지목하며, 멀린을 맞히면 악이, 틀리면 선이 승리합니다.',
          ],
          [
            '호수의 여인 · 선택 규칙',
            '2·3·4차 원정이 끝나고 게임이 계속될 때 보유자가 한 명의 진영을 조사하고 토큰을 넘깁니다. 이전 보유자는 조사할 수 없습니다. 진영만 본인에게 공개됩니다.',
          ],
          [
            '연결 중단과 제한시간',
            '연결이 끊기면 진행을 멈추고 복귀를 확인합니다. 유예시간 초과·명시적 퇴장·필수 행동 시간 초과·서버 재시작은 승패 없는 무효 종료입니다. 0초 설정 시 연결 중단 확인 즉시 종료합니다.',
          ],
        ]" :key="i">
          <span class="eyebrow">0{{ i + 1 }}</span>
          <h2>{{ r[0] }}</h2>
          <p>{{ r[1] }}</p>
        </section>
      </div>
      <section class="panel">
        <h2>인원별 원정 구성</h2>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>참가자</th>
                <th>선 / 악</th>
                <th v-for="n in 5">{{ n }}차</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in [
                [5, '3 / 2', 2, 3, 2, 3, 3],
                [6, '4 / 2', 2, 3, 4, 3, 4],
                [7, '4 / 3', 2, 3, 3, 4, 4],
                [8, '5 / 3', 3, 4, 4, 5, 5],
                [9, '6 / 3', 3, 4, 4, 5, 5],
                [10, '6 / 4', 3, 4, 4, 5, 5],
              ]">
                <td v-for="v in r">{{ v }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
    <template v-if="page === 'roles'">
      <section class="page-heading">
        <p class="eyebrow">SECRET ALLEGIANCES</p>
        <h1>빛의 서약, 어둠의 속삭임</h1>
        <p>역할의 능력을 익히고 당신만의 전략을 세우세요.</p>
      </section>
      <div class="roles-grid">
        <article v-for="(name, key) in names" :key="key" class="role-card">
          <img :src="roleImage(key)" :alt="name + ' 역할 초상화'" width="1024" height="1536" loading="lazy"
            decoding="async" />
          <div>
            <span class="eyebrow">{{
              ["merlin", "percival", "servant"].includes(key)
                ? "ARTHUR · 선 진영"
                : "MORDRED · 악 진영"
            }}</span>
            <h2>{{ name }}</h2>
            <p>{{ descriptions[key] }}</p>
          </div>
        </article>
      </div>
    </template>
  </main>
  <footer>
    ♜ Court of Camelot · Avalon <span>비공식 팬 제작 웹 게임</span>
  </footer>
  <div v-if="showCreate || joinCode" class="modal-backdrop" @click.self="
    showCreate = false;
  joinCode = '';
  " @keydown.esc="
      showCreate = false;
    joinCode = '';
    " role="dialog" aria-modal="true" :aria-label="showCreate ? '원탁 만들기' : '원탁 참여'">
    <form class="modal panel" @submit.prevent="
      run(showCreate ? create : () => join(joinCode.trim().toUpperCase()))
      ">
      <button type="button" class="close" @click="
        showCreate = false;
      joinCode = '';
      " aria-label="닫기">
        ×
      </button>
      <p class="eyebrow">JOIN THE COUNCIL</p>
      <h2>{{ showCreate ? "새로운 원탁 만들기" : "초대받은 원탁에 참여" }}</h2>
      <label v-if="!user">닉네임<input v-model="nickname" required maxlength="16" autofocus /></label><label
        v-if="showCreate">방 이름<input v-model="title" required maxlength="40" /></label><label v-else>초대 코드<input
          v-model="joinCode" required maxlength="6" /></label><label>방 비밀번호 {{ showCreate ? "(선택)" : ""
          }}<input type="password" v-model="password" maxlength="64" autocomplete="off" /></label>
      <p v-if="showCreate" class="muted">
        인원·역할·시간은 생성 후 대기실에서 설정할 수 있습니다.
      </p>
      <p v-if="error" class="error">{{ error }}</p>
      <button class="gold wide" :disabled="busy">
        {{ busy ? "처리 중…" : showCreate ? "원탁 만들기" : "원탁에 입장" }}
      </button>
    </form>
  </div>
</template>
