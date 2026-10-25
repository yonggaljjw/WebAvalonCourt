<script setup>
import { onUnmounted, ref, watch } from "vue";
import { presentationEvent } from "../../presentation.js";
const props = defineProps({ room: Object, connection: String });
const current = ref(null);
let timer;
let suppress = true;
let serial = 0;
function clear() {
  clearTimeout(timer);
  current.value = null;
}
watch(
  () => props.connection,
  (value) => {
    if (value !== "실시간 연결") {
      suppress = true;
      clear();
    }
  },
);
watch(
  () => props.room,
  (after, before) => {
    if (!after || props.connection !== "실시간 연결") {
      suppress = true;
      clear();
      return;
    }
    if (suppress || !before || before.code !== after.code) {
      suppress = false;
      clear();
      return;
    }
    const event = presentationEvent(before, after);
    if (!event) return;
    clear();
    current.value = { ...event, serial: ++serial };
    timer = setTimeout(clear, 2400);
  },
  { immediate: true },
);
onUnmounted(clear);
</script>
<template>
  <Transition name="event">
    <aside
      v-if="current"
      :key="current.serial"
      class="event-overlay"
      :class="current.tone"
      role="status"
      aria-live="polite"
    >
      <img
        :src="`/assets/remaster/${current.icon}.webp`"
        alt=""
        width="96"
        height="96"
      />
      <div>
        <p class="eyebrow">CHRONICLES OF CAMELOT</p>
        <strong>{{ current.title }}</strong>
        <p>{{ current.detail }}</p>
      </div>
    </aside>
  </Transition>
</template>
