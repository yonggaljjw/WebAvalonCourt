<script setup>
import {
  roleDescriptions,
  roleImage,
  roleNames,
} from "../constants/game.js";
</script>

<template>
  <section class="page-heading">
    <p class="eyebrow">SECRET ALLEGIANCES</p>
    <h1>빛의 서약, 어둠의 속삭임</h1>
    <p>역할의 능력을 익히고 당신만의 전략을 세우세요.</p>
  </section>
  <div class="roles-grid">
    <article v-for="(name, key) in roleNames" :key="key" class="role-card">
      <img
        :src="roleImage(key)"
        :alt="name + ' 역할 초상화'"
        width="1024"
        height="1536"
        loading="lazy"
        decoding="async"
      />
      <div>
        <span class="eyebrow">
          {{ ["merlin", "percival", "servant"].includes(key) ? "ARTHUR · 선 진영" : "MORDRED · 악 진영" }}
        </span>
        <h2>{{ name }}</h2>
        <p>{{ roleDescriptions[key] }}</p>
      </div>
    </article>
  </div>
</template>
