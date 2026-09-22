// 저수준 Web Audio 구현(audio.js)을 Vue의 반응형 상태와 연결하는 Composable입니다.

import { onMounted, onUnmounted, ref, watch } from "vue";
import { AvalonAudio, transitionCue } from "../audio.js";

export function useAudio(room, connection, error) {
  // 실제 오실레이터/게인 노드 생성은 AvalonAudio 클래스가 담당합니다.
  const sound = new AvalonAudio();

  // 화면의 사운드 컨트롤과 양방향으로 연결되는 반응형 상태입니다.
  const soundOn = ref(false);
  const musicVolume = ref(25);
  const effectVolume = ref(50);

  // 최초 서버 상태를 받자마자 과거 단계의 효과음이 재생되는 것을 막는 플래그입니다.
  let suppressNextStateCue = true;

  // 사용자가 이전에 저장한 볼륨이 있으면 localStorage에서 복구합니다.
  try {
    const saved = JSON.parse(localStorage.getItem("avalon_audio") || "{}");
    musicVolume.value = saved.music ?? 25;
    effectVolume.value = saved.effects ?? 50;
  } catch {
    // localStorage가 차단되거나 JSON이 깨진 경우 기본값을 그대로 사용합니다.
  }

  function updateVolume() {
    // UI는 0~100, 오디오 엔진은 0~1 범위를 사용하므로 100으로 나눕니다.
    sound.volumes(musicVolume.value / 100, effectVolume.value / 100);

    try {
      localStorage.setItem(
        "avalon_audio",
        JSON.stringify({
          music: musicVolume.value,
          effects: effectVolume.value,
        }),
      );
    } catch {
      // 볼륨 저장 실패가 게임 진행을 막아서는 안 되므로 무시합니다.
    }
  }

  async function toggleSound() {
    try {
      if (soundOn.value) {
        sound.disable();
        soundOn.value = false;
      } else {
        // 브라우저 자동재생 정책 때문에 반드시 사용자의 클릭 안에서 AudioContext를 시작합니다.
        updateVolume();
        sound.scene(room.value);
        await sound.enable();
        soundOn.value = true;
        sound.cue("resume");
      }
    } catch (e) {
      error.value = e.message;
    }
  }

  // 연결 상태가 바뀌면 재접속 시 과거 효과음을 억제하고, 끊김 상태의 음악을 반영합니다.
  watch(connection, (value) => {
    if (value === "연결 중") suppressNextStateCue = true;
    if (value === "연결 끊김" && room.value) {
      sound.scene({ ...room.value, paused: true });
    }
  });

  // 서버에서 새 Room 상태를 받을 때 BGM 장면과 단계 전환 효과음을 갱신합니다.
  watch(room, (after, before) => {
    sound.scene(after);
    if (!after) return;

    if (suppressNextStateCue) {
      suppressNextStateCue = false;
      return;
    }

    const cue = transitionCue(before, after);
    if (cue) sound.cue(cue);
  });

  function visibility() {
    // 탭이 숨겨지거나 다시 보일 때 오디오 스케줄링을 정리합니다.
    sound.visibility();
  }

  onMounted(() => document.addEventListener("visibilitychange", visibility));

  onUnmounted(() => {
    document.removeEventListener("visibilitychange", visibility);
    sound.close();
  });

  return {
    soundOn,
    musicVolume,
    effectVolume,
    updateVolume,
    toggleSound,
  };
}
