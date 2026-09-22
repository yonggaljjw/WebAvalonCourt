import { computed, onMounted, onUnmounted, ref } from "vue";
import { api } from "../services/api.js";

export function useAvalon() {
  const page = ref("lobby");
  const user = ref(null);
  const nickname = ref("");
  const rooms = ref([]);
  const room = ref(null);
  const error = ref("");
  const busy = ref(false);
  const connection = ref("");
  const filter = ref("");
  const now = ref(Date.now() / 1000);
  const offset = ref(0);
  const showCreate = ref(false);
  const joinCode = ref("");
  const password = ref("");
  const title = ref("원탁의 기사들");
  const settings = ref({
    capacity: 10,
    roles: ["percival", "morgana"],
    lady: false,
    discussion_seconds: 180,
    vote_seconds: 60,
    reconnect_seconds: 30,
  });

  let socket;
  let heartbeat;
  let polling;
  let clock;
  let reconnect;
  let stopped = false;

  const filtered = computed(() =>
    rooms.value.filter(
      (entry) =>
        entry.title.includes(filter.value) ||
        entry.code.includes(filter.value.toUpperCase()),
    ),
  );
  const myPlayer = computed(() =>
    room.value?.players.find((player) => player.id === room.value.me.id),
  );
  const host = computed(() => room.value?.host === room.value?.me.id);
  const seconds = computed(() =>
    Math.max(
      0,
      Math.ceil((room.value?.deadline || 0) - now.value - offset.value),
    ),
  );

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
    } catch {
      error.value = "서버에 연결할 수 없습니다. 잠시 후 새로고침해주세요.";
    }
  }

  async function guest() {
    user.value = await api("/guest", "POST", { name: nickname.value });
  }

  async function create() {
    if (!user.value) await guest();
    const created = await api("/rooms", "POST", {
      title: title.value,
      password: password.value,
      settings: settings.value,
    });
    showCreate.value = false;
    openRoom(created.code);
  }

  async function join(code) {
    if (!user.value) await guest();
    await api("/rooms/" + code + "/join", "POST", {
      password: password.value,
    });
    openRoom(code);
    joinCode.value = "";
  }

  function openRoom(code) {
    stopped = false;
    localStorage.setItem("avalon_room", code);
    page.value = "game";
    connect(code);
  }

  function connect(code) {
    connection.value = "연결 중";
    socket = new WebSocket(
      `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/${code}`,
    );

    socket.onopen = () => {
      connection.value = "실시간 연결";
      clearInterval(heartbeat);
      heartbeat = setInterval(() => {
        if (socket?.readyState === 1) {
          socket.send(JSON.stringify({ action: "ping" }));
        }
      }, 4000);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "error") {
        error.value = data.message;
        return;
      }
      if (data.type !== "state") return;

      const changed =
        JSON.stringify(room.value?.settings) !==
        JSON.stringify(data.room.settings);
      room.value = data.room;
      offset.value = data.room.server_time - Date.now() / 1000;
      if (changed) settings.value = structuredClone(data.room.settings);
    };

    socket.onclose = (event) => {
      clearInterval(heartbeat);
      connection.value = "연결 끊김";
      if (event.code === 4001) {
        stopped = true;
        error.value = "다른 창에서 접속했습니다. 한 창에서만 플레이해주세요.";
      }
      if (event.code === 1008) {
        stopped = true;
        error.value =
          "입장 정보를 확인할 수 없습니다. 로비로 돌아가 다시 입장해주세요.";
      }
      if (!stopped) reconnect = setTimeout(() => connect(code), 2000);
    };
  }

  function send(action, data = {}) {
    error.value = "";
    if (socket?.readyState !== 1) {
      error.value = "서버에 재연결 중입니다.";
      return;
    }
    socket.send(JSON.stringify({ action, ...data }));
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
        ) {
          throw e;
        }
      }
    }
    disconnect();
    room.value = null;
    page.value = "lobby";
    localStorage.removeItem("avalon_room");
    await refresh();
  }

  function disconnect() {
    stopped = true;
    clearTimeout(reconnect);
    clearInterval(heartbeat);
    socket?.close();
  }

  async function saveSettings(nextSettings = settings.value) {
    settings.value = structuredClone(nextSettings);
    await api(
      "/rooms/" + room.value.code + "/settings",
      "PUT",
      settings.value,
    );
  }

  async function copyInvite() {
    try {
      await navigator.clipboard.writeText(
        location.origin + "/?room=" + room.value.code,
      );
    } catch {
      error.value = "초대 코드: " + room.value.code;
    }
  }

  function backToLobbyFromConnection() {
    disconnect();
    room.value = null;
    page.value = "lobby";
    localStorage.removeItem("avalon_room");
  }

  onMounted(async () => {
    try {
      user.value = await api("/me");
    } catch {}
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
    clearInterval(polling);
    clearInterval(clock);
  });

  return {
    page,
    user,
    nickname,
    rooms,
    room,
    error,
    busy,
    connection,
    filter,
    showCreate,
    joinCode,
    password,
    title,
    settings,
    filtered,
    myPlayer,
    host,
    seconds,
    run,
    refresh,
    create,
    join,
    send,
    leave,
    disconnect,
    saveSettings,
    copyInvite,
    backToLobbyFromConnection,
  };
}
