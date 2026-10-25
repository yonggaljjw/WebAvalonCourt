<script setup>
import { ref, watch } from "vue";
import { roleImage, roleNames } from "../../constants/game.js";
const props = defineProps({
  role: String,
  loading: { type: String, default: "lazy" },
  sizes: { type: String, default: "(max-width: 767px) 42vw, 240px" },
});
const failed = ref(false);
watch(
  () => props.role,
  () => (failed.value = false),
);
</script>
<template>
  <div class="portrait-frame">
    <img
      v-if="!failed"
      class="role-portrait"
      :src="roleImage(role)"
      :srcset="`${roleImage(role, true)} 256w, ${roleImage(role)} 1024w`"
      :sizes="sizes"
      :alt="roleNames[role] + ' 역할 초상화'"
      width="1024"
      height="1536"
      :loading="loading"
      decoding="async"
      @error="failed = true"
    />
    <span v-else class="portrait-fallback">초상화를 불러올 수 없습니다</span>
    <img
      class="portrait-border"
      src="/assets/remaster/ui/card-frame.webp"
      alt=""
      width="768"
      height="1152"
      :loading="loading"
    />
  </div>
</template>
