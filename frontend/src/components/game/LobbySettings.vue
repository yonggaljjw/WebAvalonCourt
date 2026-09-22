<script setup>
import { reactive, watch } from "vue";
import { roleNames } from "../../constants/game.js";

const props = defineProps({
  settings: { type: Object, required: true },
  host: { type: Boolean, required: true },
});
const emit = defineEmits(["save"]);

const draft = reactive({
  ...props.settings,
  roles: [...props.settings.roles],
});

watch(
  () => props.settings,
  (value) => {
    Object.assign(draft, structuredClone(value));
  },
  { deep: true },
);
</script>

<template>
  <section class="panel">
    <h3>
      원탁 설정
      <small>{{ host ? "설정 변경 시 모두 준비가 해제됩니다" : "방장이 변경할 수 있습니다" }}</small>
    </h3>
    <div class="settings-grid">
      <label>
        최대 인원
        <select v-model.number="draft.capacity" :disabled="!host">
          <option v-for="number in [5, 6, 7, 8, 9, 10]" :key="number">{{ number }}</option>
        </select>
      </label>
      <label>
        토론·구성 시간 (초)
        <input v-model.number="draft.discussion_seconds" type="number" min="30" max="600" :disabled="!host" />
      </label>
      <label>
        투표·행동 시간 (초)
        <input v-model.number="draft.vote_seconds" type="number" min="15" max="180" :disabled="!host" />
      </label>
      <label>
        재접속 유예 (초)
        <input v-model.number="draft.reconnect_seconds" type="number" min="0" max="120" :disabled="!host" />
      </label>
    </div>
    <div class="checks">
      <label v-for="role in ['percival', 'morgana', 'mordred', 'oberon']" :key="role">
        <input v-model="draft.roles" type="checkbox" :value="role" :disabled="!host" />{{ roleNames[role] }}
      </label>
      <label>
        <input v-model="draft.lady" type="checkbox" :disabled="!host" />호수의 여인
      </label>
    </div>
    <button v-if="host" @click="emit('save', structuredClone(draft))">설정 저장</button>
  </section>
</template>
