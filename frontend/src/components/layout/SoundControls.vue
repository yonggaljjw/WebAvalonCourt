<script setup>
defineProps({
  soundOn: { type: Boolean, required: true },
  musicVolume: { type: Number, required: true },
  effectVolume: { type: Number, required: true },
});
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
