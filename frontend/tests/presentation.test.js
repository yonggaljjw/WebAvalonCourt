import test from "node:test";
import assert from "node:assert/strict";
import { presentationEvent } from "../src/presentation.js";
const state = (extra = {}) => ({
  code: "ABCDEF",
  phase: "proposal",
  leader: "p0",
  round: 1,
  paused: false,
  quests: [],
  history: [],
  winner: "",
  ...extra,
});
test("초기/다른 방/동일 상태는 연출하지 않는다", () => {
  assert.equal(presentationEvent(null, state()), null);
  assert.equal(presentationEvent(state(), state({ code: "OTHER" })), null);
  assert.equal(presentationEvent(state(), state()), null);
});
test("비밀 역할/투표/카드/개인 조사 변경은 공개 연출에 영향을 주지 않는다", () => {
  const before = state({
    me: { role: "servant", evil: false },
    cards: {},
    votes: {},
  });
  const after = state({
    me: {
      role: "assassin",
      evil: true,
      inspections: [{ name: "secret", evil: true }],
    },
    cards: { p0: false },
    votes: { p0: false },
  });
  assert.equal(presentationEvent(before, after), null);
});
test("원정 결과와 다음 phase가 함께 오면 원정 결과를 우선한다", () => {
  const e = presentationEvent(
    state({ phase: "quest" }),
    state({ phase: "lady", quests: [{ success: false, fails: 1 }] }),
  );
  assert.equal(e.title, "원정 실패");
  assert.match(e.detail, /1장/);
});
test("투표 공개 후 합계만 사용하며 개인 표를 연출하지 않는다", () => {
  const e = presentationEvent(
    state({ phase: "vote" }),
    state({
      phase: "quest",
      history: [
        {
          approved: true,
          approve_count: 3,
          reject_count: 2,
          ballots: { p0: false },
        },
      ],
    }),
  );
  assert.equal(e.title, "원정대 승인");
  assert.equal(e.detail, "찬성 3명 · 반대 2명");
  assert.doesNotMatch(JSON.stringify(e), /p0|ballots/);
});
test("마지막 원정과 종료가 함께 오면 종료를 우선하고 무효 종료를 구별한다", () => {
  const before = state({ phase: "quest" });
  const e = presentationEvent(
    before,
    state({
      phase: "ended",
      winner: "evil",
      quests: [{ success: false, fails: 1 }],
    }),
  );
  assert.equal(e.title, "어둠이 왕관을 차지했습니다");
  assert.equal(
    presentationEvent(before, state({ phase: "ended", winner: "aborted" }))
      .tone,
    "neutral",
  );
});
test("공개 연결 일시정지/복귀 및 시작/암살 이벤트를 구별한다", () => {
  assert.match(
    presentationEvent(state(), state({ paused: true })).detail,
    /일시 정지/,
  );
  assert.match(
    presentationEvent(state({ paused: true }), state()).detail,
    /연결 복구/,
  );
  assert.equal(
    presentationEvent(state({ phase: "lobby" }), state()).title,
    "원탁의 서약",
  );
  assert.equal(
    presentationEvent(state(), state({ phase: "assassination" })).tone,
    "red",
  );
});
