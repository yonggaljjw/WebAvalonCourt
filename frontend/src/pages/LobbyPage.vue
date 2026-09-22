<script setup>
import { phases, roleNames } from "../constants/game.js";

defineProps({
  user: { type: Object, default: null },
  nickname: { type: String, required: true },
  filter: { type: String, required: true },
  rooms: { type: Array, required: true },
});
const emit = defineEmits([
  "refresh",
  "create",
  "join",
  "rules",
  "update:nickname",
  "update:filter",
]);
</script>

<template>
  <section class="intro">
    <div>
      <p class="eyebrow">THE COUNCIL OF CAMELOT</p>
      <h1>충성과 배신 사이,<br />원탁에 앉으십시오.</h1>
      <p>
        누가 아서의 편이고, 누가 어둠의 하수인인가.<br />5–10명의 기사들과 펼치는 실시간 추리 게임.
      </p>
      <div class="tags">
        <span>회원가입 없이</span><span>실시간 멀티플레이</span><span>5–10인</span>
      </div>
    </div>
    <img src="/assets/knight.webp" alt="어두운 갑옷을 입은 원탁의 기사" />
  </section>

  <div class="lobby-layout">
    <section>
      <div class="section-title">
        <h2>열려 있는 원탁 <small>{{ rooms.length }} ROOMS</small></h2>
        <button @click="emit('refresh')">새로고침 ↻</button>
      </div>
      <input
        :value="filter"
        aria-label="방 검색"
        placeholder="방 이름 또는 초대 코드로 검색"
        class="search"
        @input="emit('update:filter', $event.target.value)"
      />
      <div class="room-list">
        <article v-for="room in rooms" :key="room.code" class="room-card">
          <div class="room-mark">{{ room.locked ? "♜" : "⚔" }}</div>
          <div class="grow">
            <span class="eyebrow">{{ room.code }} · {{ phases[room.phase] }}</span>
            <h3>{{ room.title }}</h3>
            <small>
              {{ room.roles.map((role) => roleNames[role]).join(" · ") || "기본 역할" }}
              · {{ room.count }} / {{ room.capacity }}명
            </small>
          </div>
          <button
            :disabled="room.phase !== 'lobby' || room.count >= room.capacity"
            @click="emit('join', room.code)"
          >
            입장 →
          </button>
        </article>
        <div v-if="!rooms.length" class="empty">
          <span>⚔</span>
          <h3>아직 모인 원탁이 없습니다.</h3>
          <p>첫 번째 방을 열고 동료들을 초대하세요.</p>
          <button class="gold" @click="emit('create')">새로운 원탁 만들기</button>
        </div>
      </div>
    </section>

    <aside>
      <section class="panel">
        <p class="eyebrow">YOUR NAME AT THE TABLE</p>
        <h2>원탁으로 입장</h2>
        <label v-if="!user">
          닉네임
          <input
            :value="nickname"
            maxlength="16"
            placeholder="기사의 이름을 입력하세요"
            @input="emit('update:nickname', $event.target.value)"
          />
        </label>
        <p v-else>{{ user.name }} 님, 원정이 기다립니다.</p>
        <button class="gold wide" @click="emit('create')">＋ 원탁 만들기</button>
        <button class="wide" @click="emit('join', ' ')">초대 코드로 참여</button>
      </section>
      <section class="panel hint">
        <h3>처음 오셨나요?</h3>
        <p>
          선 진영은 원정 3회 성공을,<br />악 진영은 원정 3회 실패를 노립니다.<br />하지만 멀린이 발각되면 모든 것이 뒤집힙니다.
        </p>
        <button class="link" @click="emit('rules')">게임 방법 알아보기 →</button>
      </section>
    </aside>
  </div>
</template>
