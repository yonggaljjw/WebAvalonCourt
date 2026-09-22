<!-- 학습용 주석: 앱 상단의 로고/내비게이션을 담당하는 공통 레이아웃 컴포넌트입니다. -->
<script setup>
// props: 부모 컴포넌트가 이 컴포넌트에 내려주는 입력값입니다.
defineProps({
  page: { type: String, required: true },
  room: { type: Object, default: null },
  user: { type: Object, default: null },
});
// emit: 자식이 직접 부모 상태를 바꾸지 않고 사용자 행동을 이벤트로 알립니다.
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
