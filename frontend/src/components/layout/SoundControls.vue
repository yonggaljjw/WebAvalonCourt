<!-- 학습용 주석: BGM/효과음 활성화와 볼륨 값을 부모 상태에 연결하는 공통 UI입니다. -->
<script setup>
// props: 부모 컴포넌트가 이 컴포넌트에 내려주는 입력값입니다.
defineProps({
  soundOn: { type: Boolean, required: true },
  musicVolume: { type: Number, required: true },
  effectVolume: { type: Number, required: true },
});
// emit: 자식이 직접 부모 상태를 바꾸지 않고 사용자 행동을 이벤트로 알립니다.
const emit = defineEmits([
  "toggle",
  "update:musicVolume",
  "update:effectVolume",
  "volume-change",
]);
</script>

<template>
  <section class="sound-controls" aria-label="소리 설정">
    <button :aria-pressed="soundOn" @click="emit('toggle')">
      {{ soundOn ? "소리 끄기" : "♫ 소리 켜기" }}
    </button>
    <label>
      배경음 {{ musicVolume }}%
      <input
        type="range"
        min="0"
        max="100"
        :value="musicVolume"
        aria-label="배경음 볼륨"
        @input="emit('update:musicVolume', Number($event.target.value)); emit('volume-change')"
      />
    </label>
    <label>
      효과음 {{ effectVolume }}%
      <input
        type="range"
        min="0"
        max="100"
        :value="effectVolume"
        aria-label="효과음 볼륨"
        @input="emit('update:effectVolume', Number($event.target.value)); emit('volume-change')"
      />
    </label>
    <small v-if="!soundOn">소리 켜기를 누르면 음악이 시작됩니다.</small>
  </section>
</template>
