// 아발론 프론트엔드의 핵심 상태/통신 로직을 모은 Vue Composable입니다.
// 화면 컴포넌트가 REST, WebSocket, 재접속 세부 구현을 몰라도 되도록 한곳에 캡슐화합니다.

import { computed, onMounted, onUnmounted, ref } from "vue";
import { api } from "../services/api.js";

export function useAvalon() {
  // ---------------------------------------------------------------------------
  // 1. 화면에서 직접 사용하는 반응형 상태(ref)
  // ---------------------------------------------------------------------------
  // ref의 값은 JavaScript 안에서는 `.value`로 읽고 쓰지만,
  // Vue 템플릿에서는 자동으로 언래핑되어 `page`처럼 바로 사용할 수 있습니다.
  const page = ref("lobby");
  const user = ref(null);
  const nickname = ref("");
  const rooms = ref([]);
  const room = ref(null);
  const error = ref("");
  const busy = ref(false);
  const connection = ref("");
  const filter = ref("");

  // 서버의 deadline과 브라우저 시간을 비교하기 위한 시간 관련 상태입니다.
  const now = ref(Date.now() / 1000);
  const offset = ref(0);

  // 방 생성/입장 모달에서 쓰는 입력값입니다.
  const showCreate = ref(false);
  const joinCode = ref("");
  const password = ref("");
  const title = ref("원탁의 기사들");

  // 새 방을 만들 때 사용할 기본 게임 설정입니다.
  const settings = ref({
    capacity: 10,
    roles: ["percival", "morgana"],
    lady: false,
    discussion_seconds: 180,
    vote_seconds: 60,
    reconnect_seconds: 30,
  });

  // ---------------------------------------------------------------------------
  // 2. 화면 반응성은 필요 없지만 연결을 관리하는 내부 변수
  // ---------------------------------------------------------------------------
  let socket;
  let heartbeat;
  let polling;
  let clock;
  let reconnect;
  let stopped = false;

  // ---------------------------------------------------------------------------
  // 3. 다른 상태로부터 자동 계산되는 computed 값
  // ---------------------------------------------------------------------------
  // 검색어가 바뀌거나 rooms가 갱신되면 자동으로 필터링 결과가 다시 계산됩니다.
  const filtered = computed(() =>
    rooms.value.filter(
      (entry) =>
        entry.title.includes(filter.value) ||
        entry.code.includes(filter.value.toUpperCase()),
    ),
  );

  // 현재 방 상태에서 '나'에 해당하는 공개 플레이어 정보를 찾습니다.
  const myPlayer = computed(() =>
    room.value?.players.find((player) => player.id === room.value.me.id),
  );

  // 서버가 알려준 host ID와 내 ID가 같으면 현재 사용자가 방장입니다.
  const host = computed(() => room.value?.host === room.value?.me.id);

  // 서버와 브라우저의 시계 차이(offset)를 보정해 남은 초를 계산합니다.
  const seconds = computed(() =>
    Math.max(
      0,
      Math.ceil((room.value?.deadline || 0) - now.value - offset.value),
    ),
  );

  // ---------------------------------------------------------------------------
  // 4. 공통 비동기 작업 래퍼
  // ---------------------------------------------------------------------------
  async function run(fn) {
    // 버튼 연타로 동일 요청이 중복 실행되는 것을 막습니다.
    if (busy.value) return;

    busy.value = true;
    error.value = "";
    try {
      await fn();
    } catch (e) {
      // api()나 기타 비동기 함수에서 발생한 오류를 전역 배너에 보여줍니다.
      error.value = e.message;
    } finally {
      busy.value = false;
    }
  }

  // ---------------------------------------------------------------------------
  // 5. REST API: 로비/세션/방 관리
  // ---------------------------------------------------------------------------
  async function refresh() {
    try {
      rooms.value = await api("/rooms");
    } catch {
      error.value = "서버에 연결할 수 없습니다. 잠시 후 새로고침해주세요.";
    }
  }

  async function guest() {
    // 닉네임으로 익명 세션을 생성하면 서버가 HttpOnly 쿠키를 설정합니다.
    user.value = await api("/guest", "POST", { name: nickname.value });
  }

  async function create() {
    // 아직 익명 세션이 없다면 방 생성 전에 먼저 게스트 세션을 만듭니다.
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
    // 명시적으로 나간 상태가 아니므로 자동 재접속을 허용합니다.
    stopped = false;

    // 새로고침 후에도 같은 방으로 복귀할 수 있도록 방 코드를 브라우저에 저장합니다.
    localStorage.setItem("avalon_room", code);
    page.value = "game";
    connect(code);
  }

  // ---------------------------------------------------------------------------
  // 6. WebSocket: 실시간 게임 연결
  // ---------------------------------------------------------------------------
  function connect(code) {
    connection.value = "연결 중";

    // 현재 페이지가 HTTPS면 wss, HTTP면 ws 프로토콜을 사용합니다.
    socket = new WebSocket(
      `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/${code}`,
    );

    socket.onopen = () => {
      connection.value = "실시간 연결";

      // 이전 heartbeat가 남아 있다면 먼저 정리합니다.
      clearInterval(heartbeat);

      // 4초마다 ping을 보내 서버가 이 브라우저가 살아 있음을 확인하게 합니다.
      heartbeat = setInterval(() => {
        if (socket?.readyState === 1) {
          socket.send(JSON.stringify({ action: "ping" }));
        }
      }, 4000);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      // 서버의 RuleError 등은 상태와 분리된 error 메시지로 옵니다.
      if (data.type === "error") {
        error.value = data.message;
        return;
      }
      if (data.type !== "state") return;

      // 방장이 설정을 바꿨는지 확인해 로컬 설정 폼도 맞춰줍니다.
      const changed =
        JSON.stringify(room.value?.settings) !==
        JSON.stringify(data.room.settings);

      room.value = data.room;

      // 서버 시간 - 브라우저 시간 값을 저장하여 타이머의 시계 차이를 보정합니다.
      offset.value = data.room.server_time - Date.now() / 1000;

      if (changed) {
        // structuredClone으로 서버 객체와 폼 입력 객체가 같은 참조를 공유하지 않게 합니다.
        settings.value = structuredClone(data.room.settings);
      }
    };

    socket.onclose = (event) => {
      clearInterval(heartbeat);
      connection.value = "연결 끊김";

      // 서버가 4001로 닫으면 동일 세션이 다른 탭에서 접속한 경우입니다.
      if (event.code === 4001) {
        stopped = true;
        error.value = "다른 창에서 접속했습니다. 한 창에서만 플레이해주세요.";
      }

      // 1008은 Origin/세션/방 참가 정보 등이 유효하지 않은 정책 위반 연결입니다.
      if (event.code === 1008) {
        stopped = true;
        error.value =
          "입장 정보를 확인할 수 없습니다. 로비로 돌아가 다시 입장해주세요.";
      }

      // 단순 네트워크 끊김이라면 2초 뒤 같은 방으로 자동 재접속합니다.
      if (!stopped) reconnect = setTimeout(() => connect(code), 2000);
    };
  }

  function send(action, data = {}) {
    error.value = "";

    // WebSocket.OPEN의 숫자 값이 1입니다.
    if (socket?.readyState !== 1) {
      error.value = "서버에 재연결 중입니다.";
      return;
    }

    // {action: "vote", approve: true} 같은 하나의 JSON 메시지로 전송합니다.
    socket.send(JSON.stringify({ action, ...data }));
  }

  // ---------------------------------------------------------------------------
  // 7. 방 퇴장/연결 종료와 기타 UI 기능
  // ---------------------------------------------------------------------------
  async function leave() {
    // 정상 참가 상태라면 서버에도 명시적으로 퇴장 요청을 보냅니다.
    if (room.value && !stopped) {
      try {
        await api("/rooms/" + room.value.code + "/leave", "POST");
      } catch (e) {
        // 이미 서버 쪽에서 방/참가 상태가 사라진 경우는 로비 복귀를 계속 진행해도 됩니다.
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
    // stopped=true이면 onclose가 실행되어도 자동 재접속하지 않습니다.
    stopped = true;
    clearTimeout(reconnect);
    clearInterval(heartbeat);
    socket?.close();
  }

  async function saveSettings(nextSettings = settings.value) {
    // 자식 설정 컴포넌트가 넘긴 초안으로 로컬 상태를 먼저 갱신합니다.
    settings.value = structuredClone(nextSettings);

    await api(
      "/rooms/" + room.value.code + "/settings",
      "PUT",
      settings.value,
    );
  }

  async function copyInvite() {
    try {
      // 초대 링크는 query string의 room 파라미터에 방 코드를 담습니다.
      await navigator.clipboard.writeText(
        location.origin + "/?room=" + room.value.code,
      );
    } catch {
      // 클립보드 권한이 없으면 최소한 방 코드라도 오류 배너에 보여줍니다.
      error.value = "초대 코드: " + room.value.code;
    }
  }

  function backToLobbyFromConnection() {
    // 서버 퇴장 API를 호출하지 않고 연결 화면에서 로비 UI로만 돌아가는 경로입니다.
    disconnect();
    room.value = null;
    page.value = "lobby";
    localStorage.removeItem("avalon_room");
  }

  // ---------------------------------------------------------------------------
  // 8. Vue 생명주기: 컴포넌트가 붙을 때 초기화하고 사라질 때 정리
  // ---------------------------------------------------------------------------
  onMounted(async () => {
    // 기존 HttpOnly 세션 쿠키가 유효하면 /me로 사용자 정보를 복구합니다.
    try {
      user.value = await api("/me");
    } catch {
      // 최초 방문/만료 세션은 정상 상황이므로 별도 오류를 띄우지 않습니다.
    }

    await refresh();

    // 초대 링크가 있으면 입장 모달에 코드를 채우고,
    // 아니면 이전에 플레이하던 방 코드가 있을 때 자동 복귀를 시도합니다.
    const invite = new URLSearchParams(location.search).get("room");
    if (invite) {
      joinCode.value = invite.toUpperCase();
    } else {
      const code = localStorage.getItem("avalon_room");
      if (code && user.value) openRoom(code);
    }

    // 게임방에 들어가 있지 않을 때만 5초마다 로비 방 목록을 갱신합니다.
    polling = setInterval(() => {
      if (!room.value) refresh();
    }, 5000);

    // 화면의 남은 시간 표시가 매초 다시 계산되도록 브라우저 현재 시각을 갱신합니다.
    clock = setInterval(() => (now.value = Date.now() / 1000), 1000);
  });

  onUnmounted(() => {
    // SPA 컴포넌트가 제거될 때 타이머와 소켓을 정리해 메모리 누수를 막습니다.
    disconnect();
    clearInterval(polling);
    clearInterval(clock);
  });

  // App.vue와 하위 페이지에서 사용할 상태/함수만 외부에 공개합니다.
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
