<!-- Bundled music and effects require an explicit user gesture. -->
<script setup>
defineProps({
  warning: String,
  soundOn: Boolean,
  musicVolume: Number,
  effectVolume: Number,
});
const emit = defineEmits([
  "toggle",
  "update:musicVolume",
  "update:effectVolume",
  "volume-change",
]);
function closeSettings(event) {
  event.currentTarget.open = false;
  event.currentTarget.querySelector("summary")?.focus();
}
</script>
<template>
  <details class="sound-controls" @keydown.esc="closeSettings">

    <summary>
      <span aria-hidden="true">♫</span> 소리 설정
      <small>{{ soundOn ? "켜짐" : "꺼짐" }}</small>
    </summary>
    <div class="sound-settings">
      <button :aria-pressed="soundOn" @click="emit('toggle')">
        {{ soundOn ? "전체 소리 끄기" : "♫ 소리 켜기" }}
      </button>
      <label
        >배경음 {{ musicVolume }}%<input
          type="range"
          min="0"
          max="100"
          :value="musicVolume"
          aria-label="배경음 볼륨"
          @input="
            emit('update:musicVolume', Number($event.target.value));
            emit('volume-change');
          "
      /></label>
      <label
        >효과음 {{ effectVolume }}%<input
          type="range"
          min="0"
          max="100"
          :value="effectVolume"
          aria-label="효과음 볼륨"
          @input="
            emit('update:effectVolume', Number($event.target.value));
            emit('volume-change');
          "
      /></label>
      <a href="/audio/CREDITS.txt" target="_blank" rel="noopener"
        >음악 출처·라이선스</a
      >
      <small v-if="warning" role="status">{{ warning }}</small>
      <small v-if="!soundOn">소리 켜기를 누르면 음악이 시작됩니다.</small>
    </div>
  </details>
</template>
