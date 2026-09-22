// 학습용 주석: transitionCue()를 UI 없이 순수 상태 객체만으로 검증하는 Node.js 단위 테스트입니다.

import test from "node:test";
import assert from "node:assert/strict";
import { transitionCue } from "../src/audio.js";
// 각 테스트에서 필요한 속성만 덮어쓸 수 있도록 기본 게임 상태 생성 helper를 둡니다.
const state = (extra = {}) => ({
  code: "ABC",
  phase: "proposal",
  round: 1,
  paused: false,
  quests: [],
  history: [],
  ...extra,
});
test("최초 접속과 다른 방은 과거 효과음을 재생하지 않는다", () => {
  assert.equal(transitionCue(null, state()), null);
  assert.equal(transitionCue(state(), state({ code: "XYZ" })), null);
});
test("채팅 등 동일 상태 재전송으로 효과음이 반복되지 않는다", () =>
  assert.equal(transitionCue(state(), state()), null));
test("새 라운드와 투표 단계 진입 효과음", () => {
  assert.equal(transitionCue(state(), state({ round: 2 })), "proposal");
  assert.equal(transitionCue(state(), state({ phase: "vote" })), "vote");
});
test("원정 결과는 다음 단계 효과음보다 우선한다", () => {
  assert.equal(
    transitionCue(
      state({ phase: "quest" }),
      state({ round: 2, quests: [{ success: true }] }),
    ),
    "success",
  );
  assert.equal(
    transitionCue(
      state({ phase: "quest" }),
      state({ round: 2, quests: [{ success: false }] }),
    ),
    "failure",
  );
});
test("부결, 일시 정지, 복귀 효과음", () => {
  assert.equal(
    transitionCue(state(), state({ history: [{ approved: false }] })),
    "reject",
  );
  assert.equal(transitionCue(state(), state({ paused: true })), "pause");
  assert.equal(transitionCue(state({ paused: true }), state()), "resume");
});
test("종료는 진영/무효 결과로 구별하며 반복되지 않는다", () => {
  for (const [winner, cue] of [
    ["good", "victory"],
    ["evil", "defeat"],
    ["aborted", "abort"],
  ]) {
    const ended = state({ phase: "ended", winner });
    assert.equal(transitionCue(state(), ended), cue);
    assert.equal(transitionCue(ended, ended), null);
  }
});
