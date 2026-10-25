import test from "node:test";
import assert from "node:assert/strict";
import { AvalonAudio, musicFor } from "../src/audio.js";

// Deferred network responses make lifecycle races reproducible without real timers.
class Param {
  value = 1;
  setValueAtTime(v) {
    this.value = v;
  }
  setTargetAtTime(v) {
    this.value = v;
  }
  linearRampToValueAtTime(v) {
    this.value = v;
  }
  exponentialRampToValueAtTime(v) { this.value = v; }
  cancelAndHoldAtTime() {}
  cancelScheduledValues() {}
}
class Context {
  state = "running";
  currentTime = 0;
  destination = {};
  started = [];
  async resume() {
    this.state = "running";
  }
  async close() {
    this.state = "closed";
  }
  createGain() {
    return { gain: new Param(), connect() {}, disconnect() {} };
  }
  createOscillator() {
    return {
      frequency: { value: 440 },
      connect() {},
      disconnect() {},
      start() {},
      stop() {},
    };
  }
  createBufferSource() {
    const context = this;
    return {
      connect() {},
      disconnect() {},
      start() {
        context.started.push(this);
      },
      stop(at) {
        if (at === undefined) this.onended?.();
      },
    };
  }
  async decodeAudioData() {
    return { duration: 0.01 };
  }
}
function setup() {
  globalThis.document = { hidden: false };
  globalThis.AudioContext = Context;
  const requests = [];
  globalThis.fetch = (url) =>
    new Promise((resolve) => requests.push({ url, resolve }));
  return {
    requests,
    reply(i = 0) {
      requests[i].resolve({
        ok: true,
        arrayBuffer: async () => new ArrayBuffer(8),
      });
    },
  };
}
const flush = () => new Promise((resolve) => setImmediate(resolve));

test("late BGM decode cannot restart music after mute", async () => {
  const env = setup(),
    a = new AvalonAudio();
  await a.enable();
  assert.equal(env.requests.length, 1);
  a.disable();
  env.reply();
  await flush();
  assert.equal(a.ctx.started.length, 0);
  assert.equal(a.tracks.size, 0);
  a.close();
});
test("new scene wins when previous response arrives last", async () => {
  const env = setup(),
    a = new AvalonAudio();
  await a.enable();
  a.scene({ code: "A", phase: "vote" });
  env.reply(1);
  await flush();
  assert.equal(a.active, "suspicion");
  env.reply(0);
  await flush();
  assert.equal(a.active, "suspicion");
  assert.equal(a.ctx.started.length, 1);
  a.close();
});
test("a room change cancels pending private local effects", async () => {
  const env = setup(),
    a = new AvalonAudio();
  await a.enable();
  a.scene({ code: "A", phase: "lobby" });
  env.reply();
  await flush();
  const cue = a.cue("lady");
  a.scene({ code: "B", phase: "lobby" });
  env.reply(1);
  await cue;
  assert.equal(a.voices.size, 0);
  assert.equal(a.ctx.started.length, 1);
  a.close();
});
test("rapid cached switches keep only two music sources", async () => {
  const env = setup(),
    a = new AvalonAudio();
  await a.enable();
  env.reply();
  await flush();
  for (const key of ["camelot", "council", "suspicion", "last-shadow"])
    a.cache.set(`bgm/${key}.ogg`, { duration: 60 });
  for (let i = 0; i < 60; i++) {
    a.scene({ phase: ["lobby", "proposal", "vote", "assassination"][i % 4] });
    await flush();
    assert.ok(a.tracks.size <= 2);
  }
  a.close();
  assert.equal(a.tracks.size, 0);
  assert.equal(a.cache.size, 0);
});
test("music is identical across private roles and submitted card values", () => {
  for (const phase of [
    "lobby",
    "proposal",
    "vote",
    "quest",
    "lady",
    "assassination",
  ]) {
    const base = { phase, round: 3 };
    const expected = musicFor(base);
    for (const role of [
      "merlin",
      "percival",
      "loyal",
      "morgana",
      "mordred",
      "oberon",
      "assassin",
      "minion",
    ]) {
      assert.equal(
        musicFor({
          ...base,
          me: { role, evil: true },
          vote: false,
          success: false,
        }),
        expected,
      );
    }
  }
  assert.equal(musicFor({ phase: "ended", winner: "aborted" }), null);
  assert.equal(musicFor({ phase: "vote", paused: true }), null);
});

test("close releases synth nodes even when onended will never fire", async () => {
  const env = setup(),
    a = new AvalonAudio();
  await a.enable();
  env.reply();
  await flush();
  a.note(60, 0, 0.7, 0.2, a.effects);
  assert.equal(a.nodes.size, 1);
  a.close();
  assert.equal(a.nodes.size, 0);
  assert.equal(a.tracks.size, 0);
});
