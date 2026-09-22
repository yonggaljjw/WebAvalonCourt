<!-- 학습용 주석: 게임 규칙 페이지. 정적 규칙/원정대 표 데이터를 화면에 표시합니다. -->
<script setup>
import { questTeams, rules } from "../constants/game.js";
</script>

<template>
  <section class="page-heading">
    <p class="eyebrow">THE CHRONICLES OF AVALON</p>
    <h1>게임 방법 — 신뢰와 의심 사이</h1>
    <p>5–10명 · 선과 악의 정체를 숨긴 원정</p>
  </section>
  <div class="rules-grid">
    <section v-for="(rule, index) in rules" :key="index" class="panel">
      <span class="eyebrow">0{{ index + 1 }}</span>
      <h2>{{ rule[0] }}</h2>
      <p>{{ rule[1] }}</p>
    </section>
  </div>
  <section class="panel">
    <h2>인원별 원정 구성</h2>
    <div class="table-scroll">
      <table>
        <thead>
          <tr>
            <th>참가자</th>
            <th>선 / 악</th>
            <th v-for="number in 5" :key="number">{{ number }}차</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in questTeams" :key="index">
            <td v-for="(value, column) in row" :key="column">{{ value }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
