<script setup>
defineProps({
  page: { type: String, required: true },
  room: { type: Object, default: null },
  user: { type: Object, default: null },
});
const emit = defineEmits(["navigate"]);
</script>

<template>
  <header class="top">
    <a
      href="#"
      class="brand"
      @click.prevent="emit('navigate', room ? 'game' : 'lobby')"
    >
      <img src="/assets/crest.webp" alt="아발론 문장" />
      <span>AVALON <small>THE RESISTANCE</small></span>
    </a>
    <nav>
      <button
        :class="{ active: page === 'lobby' || page === 'game' }"
        @click="emit('navigate', room ? 'game' : 'lobby')"
      >
        {{ room ? "원탁 회의" : "게임 로비" }}
      </button>
      <button
        :class="{ active: page === 'rules' }"
        @click="emit('navigate', 'rules')"
      >
        게임 방법
      </button>
      <button
        :class="{ active: page === 'roles' }"
        @click="emit('navigate', 'roles')"
      >
        역할 도감
      </button>
    </nav>
    <span class="profile">{{ user?.name || "이름 없는 기사" }}</span>
  </header>
</template>
