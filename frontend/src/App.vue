<!-- 학습용 주석: 최상위 Vue 컴포넌트. 페이지 전환과 전역 상태/이벤트를 조립하고 실제 로직은 composable과 하위 컴포넌트에 위임합니다. -->
<script setup>
import AppHeader from "./components/layout/AppHeader.vue";
import ErrorBanner from "./components/layout/ErrorBanner.vue";
import SoundControls from "./components/layout/SoundControls.vue";
import RoomModal from "./components/lobby/RoomModal.vue";
import { useAudio } from "./composables/useAudio.js";
import { useAvalon } from "./composables/useAvalon.js";
import GamePage from "./pages/GamePage.vue";
import LobbyPage from "./pages/LobbyPage.vue";
import RolesPage from "./pages/RolesPage.vue";
import RulesPage from "./pages/RulesPage.vue";

// useAvalon()에서 게임/통신 상태와 함수를 꺼냅니다. App.vue는 세부 구현을 직접 가지지 않습니다.
const {
  page,
  user,
  nickname,
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
  saveSettings,
  copyInvite,
  backToLobbyFromConnection,
} = useAvalon();

// 오디오 관련 상태와 동작은 별도의 composable로 분리했습니다.
const {
  soundOn,
  musicVolume,
  effectVolume,
  updateVolume,
  toggleSound,
} = useAudio(room, connection, error);

// 방 만들기 모달을 열면서 이전 비밀번호 입력값을 비웁니다.
function openCreate() {
  showCreate.value = true;
  password.value = "";
}

// 특정 방 카드 또는 초대 코드 입장에서 공통으로 사용하는 모달 초기화입니다.
function openJoin(code) {
  joinCode.value = code;
  password.value = "";
}

function closeModal() {
  showCreate.value = false;
  joinCode.value = "";
}

// 현재 모달이 생성 모드인지 입장 모드인지에 따라 실행할 함수를 선택합니다.
function submitModal() {
  const action = showCreate.value
    ? create
    : () => join(joinCode.value.trim().toUpperCase());
  run(action);
}
</script>

<template>
  <!-- 공통 헤더: 현재 페이지와 방 정보를 내려주고 navigate 이벤트를 받습니다. -->
  <AppHeader
    :page="page"
    :room="room"
    :user="user"
    @navigate="page = $event"
  />

  <main>
    <SoundControls
      v-model:musicVolume="musicVolume"
      v-model:effectVolume="effectVolume"
      :sound-on="soundOn"
      @toggle="toggleSound"
      @volume-change="updateVolume"
    />
    <ErrorBanner :message="error" @close="error = ''" />

    <!-- page 상태에 따라 큰 화면 컴포넌트를 조건부 렌더링합니다. -->
    <LobbyPage
      v-if="page === 'lobby'"
      v-model:nickname="nickname"
      v-model:filter="filter"
      :user="user"
      :rooms="filtered"
      @refresh="refresh"
      @create="openCreate"
      @join="openJoin"
      @rules="page = 'rules'"
    />

    <GamePage
      v-else-if="page === 'game'"
      :room="room"
      :connection="connection"
      :seconds="seconds"
      :host="host"
      :my-player="myPlayer"
      :settings="settings"
      @back="backToLobbyFromConnection"
      @copy="copyInvite"
      @leave="run(leave)"
      @send="send"
      @save-settings="(value) => run(() => saveSettings(value))"
    />

    <RulesPage v-else-if="page === 'rules'" />
    <RolesPage v-else-if="page === 'roles'" />
  </main>

  <footer>
    ♜ Court of Camelot · Avalon <span>비공식 팬 제작 웹 게임</span>
  </footer>

  <!-- 방 생성/입장 모달은 페이지와 독립적으로 최상위에 한 번만 둡니다. -->
  <RoomModal
    v-model:nickname="nickname"
    v-model:title="title"
    v-model:joinCode="joinCode"
    v-model:password="password"
    :show-create="showCreate"
    :user="user"
    :busy="busy"
    :error="error"
    @close="closeModal"
    @submit="submitModal"
  />
</template>
