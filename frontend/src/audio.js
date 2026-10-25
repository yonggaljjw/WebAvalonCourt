// 실제 음원 파일을 우선 재생하고, 파일을 읽지 못했을 때 기존 합성음을 사용합니다.
// SynthAudio는 외부 리소스 실패 시 사용하는 독립적인 대체음 엔진입니다.
// 브라우저의 자동재생 정책에 맞춰 사용자가 소리 켜기를 눌렀을 때만 시작합니다.
// 이전/이후 게임 상태를 비교해 딱 한 번 재생할 효과음 종류를 결정하는 순수 함수입니다.
export function transitionCue(before, after) {
  if (!before || before.code !== after.code) return null; // 최초 접속/복귀 시 과거 효과음 재생 금지
  if (before.phase !== "ended" && after.phase === "ended")
    return after.winner === "aborted"
      ? "abort"
      : after.winner === "good"
        ? "victory"
        : "defeat";
  if (!before.paused && after.paused) return "pause";
  if (before.paused && !after.paused) return "resume";
  if (after.quests.length > before.quests.length)
    return after.quests.at(-1).success ? "success" : "failure";
  if (
    after.history.length > before.history.length &&
    !after.history.at(-1).approved
  )
    return "reject";
  if (before.phase !== after.phase || before.round !== after.round)
    return after.phase;
  return null;
}
// AudioContext와 음악 스케줄링을 캡슐화한 클래스입니다.
class SynthAudio {
  // 객체 생성 시에는 AudioContext를 만들지 않습니다. 사용자 클릭 전 자동재생 제한을 피하기 위해서입니다.
  constructor() {
    this.enabled = false;
    this.musicVolume = 0.25;
    this.effectVolume = 0.5;
    this.mode = "lobby";
    this.round = 1;
    this.nodes = new Set();
  }
  // 사용자가 소리 켜기를 눌렀을 때 AudioContext와 Gain 노드를 준비합니다.
  async enable() {
    const Context = globalThis.AudioContext || globalThis.webkitAudioContext;
    if (!Context) throw Error("이 브라우저에서는 소리를 지원하지 않습니다.");
    if (!this.ctx) {
      this.ctx = new Context();
      this.master = this.ctx.createGain();
      this.master.connect(this.ctx.destination);
      this.music = this.ctx.createGain();
      this.music.connect(this.master);
      this.effects = this.ctx.createGain();
      this.effects.connect(this.master);
    }
    await this.ctx.resume();
    if (this.ctx.state !== "running")
      throw Error("소리 켜기를 다시 눌러주세요.");
    this.enabled = true;
    this.master.gain.setTargetAtTime(0.7, this.ctx.currentTime, 0.05);
    this.volumes(this.musicVolume, this.effectVolume);
    this.startMusic();
  }
  // BGM과 효과음 볼륨을 0~1 범위로 보정해 GainNode에 반영합니다.
  volumes(music, effects) {
    this.musicVolume = Math.max(0, Math.min(1, Number(music) || 0));
    this.effectVolume = Math.max(0, Math.min(1, Number(effects) || 0));
    if (this.ctx) {
      this.music.gain.setTargetAtTime(
        this.musicVolume,
        this.ctx.currentTime,
        0.05,
      );
      this.effects.gain.setTargetAtTime(
        this.effectVolume,
        this.ctx.currentTime,
        0.05,
      );
    }
  }
  // 음이 끝나면 오디오 노드를 해제하여 반복 재생 중 메모리가 쌓이지 않게 합니다.
  note(midi, start, duration, volume, bus, type = "sine") {
    const o = this.ctx.createOscillator(),
      g = this.ctx.createGain();
    o.type = type;
    o.frequency.value = 440 * 2 ** ((midi - 69) / 12);
    o.connect(g);
    g.connect(bus);
    g.gain.setValueAtTime(0, start);
    g.gain.linearRampToValueAtTime(volume, start + 0.025);
    g.gain.exponentialRampToValueAtTime(0.0001, start + duration);
    const node = { o, g, bus };
    this.nodes.add(node);
    o.onended = () => {
      o.disconnect();
      g.disconnect();
      this.nodes.delete(node);
    };
    o.start(start);
    o.stop(start + duration + 0.03);
  }
  // 반복 스케줄러를 멈추고 현재 예약된 BGM 노드를 중단합니다.
  stopMusic() {
    clearInterval(this.timer);
    this.timer = null;
    for (const n of this.nodes)
      if (n.bus === this.music) {
        try {
          n.o.stop();
        } catch {}
      }
  }
  // 현재 게임 장면에 맞는 짧은 음 패턴을 조금씩 선예약하는 방식으로 BGM을 만듭니다.
  startMusic() {
    this.stopMusic();
    if (
      !this.enabled ||
      ["paused", "ended"].includes(this.mode) ||
      document.hidden
    )
      return;
    this.step = 0;
    this.next = this.ctx.currentTime + 0.08;
    const schedule = () => {
      if (!this.enabled || this.ctx.state !== "running") return;
      if (this.next < this.ctx.currentTime)
        this.next = this.ctx.currentTime + 0.06;
      // 한 번에 0.4초만 예약하여 음소거·단계 변경에 빠르게 반응합니다.
      while (this.next < this.ctx.currentTime + 0.4) {
        const tense = ["vote", "quest", "assassination"].includes(this.mode),
          beat = tense ? 0.48 : 0.68;
        const roots = tense ? [45, 41, 43, 40] : [50, 46, 48, 45],
          root = roots[Math.floor(this.step / 8) % 4];
        const motif = [12, 19, 15, 22, 19, 15, 24, 19],
          pitch = root + motif[(this.step + this.round - 1) % 8];
        this.note(pitch, this.next, 1.1, 0.085, this.music, "triangle");
        if (this.step % 8 === 0) {
          this.note(root, this.next, beat * 8, 0.14, this.music);
          this.note(root + 7, this.next, beat * 7, 0.065, this.music);
        }
        this.next += beat;
        this.step++;
      }
    };
    schedule();
    this.timer = setInterval(schedule, 100);
  }
  // Room의 phase/paused/round가 바뀌었을 때 BGM 분위기를 다시 선택합니다.
  scene(room) {
    const mode = room?.paused ? "paused" : room?.phase || "lobby",
      round = room?.round || 1;
    if (mode !== this.mode || round !== this.round) {
      this.mode = mode;
      this.round = round;
      this.startMusic();
    }
  }
  // 특정 이벤트 이름에 대응하는 짧은 효과음 음계를 재생합니다.
  cue(name) {
    if (
      !this.enabled ||
      !this.ctx ||
      this.ctx.state !== "running" ||
      document.hidden
    )
      return;
    const scores = {
      proposal: [62, 69, 74],
      vote: [64, 64, 71],
      quest: [50, 57, 62],
      lady: [74, 81, 86],
      assassination: [45, 46, 45],
      success: [62, 66, 69, 74],
      failure: [50, 49, 45],
      reject: [57, 53],
      victory: [62, 66, 69, 74, 78],
      defeat: [50, 45, 41, 38],
      abort: [55, 50],
      pause: [60, 55],
      resume: [55, 60],
    };
    const notes = scores[name];
    if (!notes) return;
    notes.forEach((n, i) =>
      this.note(
        n,
        this.ctx.currentTime + 0.02 + i * 0.18,
        0.7,
        0.18,
        this.effects,
        name === "failure" || name === "defeat" ? "triangle" : "sine",
      ),
    );
  }
  // 사운드를 끄되 AudioContext 객체는 재사용할 수 있게 유지합니다.
  disable() {
    this.enabled = false;
    this.stopMusic();
    if (this.ctx) {
      this.master.gain.setValueAtTime(0, this.ctx.currentTime);
      for (const n of this.nodes) {
        try {
          n.o.stop();
        } catch {}
      }
    }
  }
  // 백그라운드 탭에서는 음악 예약을 멈추고 복귀 시 다시 시작합니다.
  visibility() {
    if (document.hidden) this.stopMusic();
    else this.startMusic();
  }
  // 컴포넌트가 사라질 때 오디오 리소스를 완전히 정리합니다.
  close() {
    this.disable();
    this.ctx?.close().catch(() => {});
  }
}

// All paths below refer to bundled, verified files; no streaming dependency.
export const BGM = {
  lobby: "camelot",
  proposal: "council",
  lady: "council",
  vote: "suspicion",
  quest: "suspicion",
  assassination: "last-shadow",
};
export function musicFor(room) {
  if (room?.paused) return null;
  if (room?.phase === "ended")
    return { good: "dawn", evil: "fallen-crown" }[room.winner] || null;
  return BGM[room?.phase || "lobby"] || "camelot";
}
export const SFX = {
  click: "click",
  proposal: "start",
  vote: "seal",
  quest: "approved",
  lady: "reveal",
  assassination: "blade",
  success: "success",
  failure: "failure",
  reject: "reject",
  victory: "success",
  defeat: "failure",
  abort: "neutral",
  pause: "neutral",
  resume: "ready",
};
export class AvalonAudio extends SynthAudio {
  constructor() {
    super();
    this.cache = new Map();
    this.pending = new Map();
    this.failed = new Set();
    this.tracks = new Set();
    this.voices = new Set();
    this.lastCue = new Map();
    this.generation = 0;
    this.selected = "camelot";
    this.closed = false;
    this.onWarning = () => {};
  }
  async load(path) {
    if (this.cache.has(path)) return this.cache.get(path);
    if (this.failed.has(path)) throw Error("Unavailable audio");
    if (this.pending.has(path)) return this.pending.get(path);
    const task = (async () => {
      try {
        const response = await fetch(
          `${import.meta.env?.BASE_URL || "/"}audio/${path}`,
          { signal: this.abort.signal },
        );
        if (!response.ok) throw Error(`HTTP ${response.status}`);
        const buffer = await this.ctx.decodeAudioData(
          await response.arrayBuffer(),
        );
        if (this.closed) throw Error("Closed");
        this.cache.set(path, buffer);
        const music = [...this.cache.keys()].filter((x) =>
          x.startsWith("bgm/"),
        );
        if (music.length > 2) this.cache.delete(music[0]);
        return buffer;
      } catch (e) {
        if (!this.closed) this.failed.add(path);
        throw e;
      } finally {
        this.pending.delete(path);
      }
    })();
    this.pending.set(path, task);
    return task;
  }
  async enable() {
    if (!this.abort) this.abort = new AbortController();
    await super.enable();
    if (!this.duck) {
      this.duck = this.ctx.createGain();
      this.music.disconnect();
      this.music.connect(this.duck);
      this.duck.connect(this.master);
    }
  }
  stopMusic() {
    this.generation = (this.generation || 0) + 1;
    super.stopMusic();
    for (const track of this.tracks || []) {
      try {
        track.source.stop();
        track.source.disconnect();
        track.gain.disconnect();
      } catch {}
    }
    this.tracks?.clear();
    this.currentTrack = null;
    this.active = null;
  }
  async startMusic() {
    if (
      !this.enabled ||
      !this.ctx ||
      this.closed ||
      document.hidden ||
      !this.selected
    ) {
      this.stopMusic();
      return;
    }
    if (this.active === this.selected) return;
    const token = ++this.generation,
      selected = this.selected;
    try {
      const buffer = await this.load(`bgm/${selected}.ogg`);
      if (token !== this.generation || !this.enabled || document.hidden) return;
      // Stop a possible synth fallback before switching to a decoded music file.
      clearInterval(this.timer);
      this.timer = null;
      for (const n of this.nodes)
        if (n.bus === this.music) {
          try {
            n.o.stop();
          } catch {}
        }
      const now = this.ctx.currentTime,
        fade = 1;
      // A rapid third switch must not keep extending a retired source's stop time.
      // Retain only the current outgoing track; crossfades use at most two sources.
      for (const retired of [...this.tracks]) {
        if (retired !== this.currentTrack) {
          try {
            retired.source.stop();
          } catch {}
          this.tracks.delete(retired);
        }
      }
      for (const old of this.tracks) {
        old.gain.gain.cancelAndHoldAtTime(now);
        old.gain.gain.linearRampToValueAtTime(0, now + fade);
        try {
          old.source.stop(now + fade);
        } catch {}
      }
      const source = this.ctx.createBufferSource(),
        gain = this.ctx.createGain();
      source.buffer = buffer;
      source.loop = !["dawn", "fallen-crown"].includes(selected);
      source.connect(gain);
      gain.connect(this.music);
      gain.gain.setValueAtTime(0, now);
      gain.gain.linearRampToValueAtTime(1, now + fade);
      const track = { source, gain };
      this.tracks.add(track);
      this.currentTrack = track;
      this.active = selected;
      source.onended = () => {
        source.disconnect();
        gain.disconnect();
        this.tracks.delete(track);
      };
      source.start();
    } catch (e) {
      if (token !== this.generation || this.closed) return;
      this.onWarning("음악 파일을 불러오지 못해 기본 합성음으로 재생합니다.");
      if (this.mode === "ended") {
        this.stopMusic();
        super.cue(selected === "dawn" ? "victory" : "defeat");
      } else {
        super.startMusic();
      }
      this.active = selected;
    }
  }
  scene(room) {
    const selected = musicFor(room);
    this.mode = room?.paused ? "paused" : room?.phase || "lobby";
    this.round = room?.round || 1;
    const code = room?.code || null;
    if (code !== this.roomCode) {
      this.roomCode = code;
      this.silenceEffects();
    }
    this.selected = selected;
    if (room?.paused) this.silenceEffects();
    this.startMusic();
  }
  async cue(name) {
    if (
      !this.enabled ||
      this.closed ||
      document.hidden ||
      this.ctx?.state !== "running"
    )
      return;
    // Result music already carries the fanfare; never double it with an SFX.
    if (["victory", "defeat"].includes(name)) return;
    const id = SFX[name];
    if (!id) return;
    const now = performance.now();
    if (now - (this.lastCue.get(id) ?? -Infinity) < 100) return;
    this.lastCue.set(id, now);
    const generation = this.effectGeneration || 0;
    try {
      const buffer = await this.load(`sfx/${id}.wav`);
      if (
        !this.enabled ||
        this.closed ||
        document.hidden ||
        generation !== (this.effectGeneration || 0)
      )
        return;
      const priority = name === "click" ? 0 : 1;
      if (this.voices.size >= 6) {
        const victim = [...this.voices].find((x) => x.priority <= priority);
        if (!victim) return;
        clearTimeout(victim.timer);
        victim.source.stop();
        this.voices.delete(victim);
      }
      const source = this.ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(this.effects);
      if (priority && this.duck) {
        const t = this.ctx.currentTime;
        this.duck.gain.cancelAndHoldAtTime(t);
        this.duck.gain.setTargetAtTime(0.6, t, 0.04);
        clearTimeout(this.duckTimer);
        this.duckTimer = setTimeout(() => {
          if (!this.closed)
            this.duck.gain.setTargetAtTime(1, this.ctx.currentTime, 0.25);
        }, buffer.duration * 1000);
      }
      const voice = { source, priority };
      this.voices.add(voice);
      source.onended = () => {
        source.disconnect();
        this.voices.delete(voice);
      };
      source.start();
    } catch {
      if (
        this.enabled &&
        !this.closed &&
        generation === (this.effectGeneration || 0)
      ) {
        // Failed SFX decoding must obey the same cap as normal playback.
        if (this.voices.size < 6) {
          const marker = { priority: 1, source: { stop() {} } };
          this.voices.add(marker);
          super.cue(name);
          marker.timer = setTimeout(() => this.voices.delete(marker), 1800);
        }
        this.onWarning("일부 효과음을 불러오지 못해 기본 합성음을 사용합니다.");
      }
    }
  }
  silenceEffects() {
    this.effectGeneration = (this.effectGeneration || 0) + 1;
    for (const v of this.voices) {
      clearTimeout(v.timer);
      try {
        v.source.stop();
      } catch {}
    }
    for (const n of this.nodes)
      if (n.bus === this.effects) {
        try {
          n.o.stop();
        } catch {}
      }
    clearTimeout(this.duckTimer);
    if (this.duck) {
      this.duck.gain.cancelScheduledValues(this.ctx.currentTime);
      this.duck.gain.setValueAtTime(1, this.ctx.currentTime);
    }
    this.voices.clear();
  }
  disable() {
    this.silenceEffects();
    super.disable();
  }
  visibility() {
    if (document.hidden) {
      this.silenceEffects();
      this.stopMusic();
    } else this.startMusic();
  }
  close() {
    this.closed = true;
    clearTimeout(this.duckTimer);
    this.abort?.abort();
    super.close();
    // Closing a context can prevent queued onended callbacks from firing.
    for (const n of this.nodes) {
      n.o.disconnect();
      n.g.disconnect();
    }
    this.nodes.clear();
    this.cache.clear();
  }
}
