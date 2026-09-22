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

const {
  soundOn,
  musicVolume,
  effectVolume,
  updateVolume,
  toggleSound,
} = useAudio(room, connection, error);

function openCreate() {
  showCreate.value = true;
  password.value = "";
}

function openJoin(code) {
  joinCode.value = code;
  password.value = "";
}

function closeModal() {
  showCreate.value = false;
  joinCode.value = "";
}

function submitModal() {
  const action = showCreate.value
    ? create
    : () => join(joinCode.value.trim().toUpperCase());
  run(action);
}
</script>

<template>
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
