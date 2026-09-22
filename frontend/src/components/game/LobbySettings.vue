<!-- 학습용 주석: 대기실에서 방장이 수정할 게임 설정 초안을 관리하는 컴포넌트입니다. -->
<script setup>
import { reactive, watch } from "vue";
import { roleNames } from "../../constants/game.js";

// props: 부모가 내려준 값을 script에서도 여러 번 참조하므로 변수로 받아 사용합니다.
const props = defineProps({
  settings: { type: Object, required: true },
  host: { type: Boolean, required: true },
});
// emit: 자식이 직접 부모 상태를 바꾸지 않고 사용자 행동을 이벤트로 알립니다.
const emit = defineEmits(["save"]);

// props.settings를 직접 수정하지 않고 별도의 편집 초안(draft)을 둡니다.
const draft = reactive({
  ...props.settings,
  roles: [...props.settings.roles],
});

// 서버/부모 설정이 바뀌면 로컬 편집 초안도 같은 값으로 동기화합니다.
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
