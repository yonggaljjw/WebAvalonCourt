import { onMounted, onUnmounted, ref, watch } from "vue";
import { AvalonAudio, transitionCue } from "../audio.js";

export function useAudio(room, connection, error) {
  const sound = new AvalonAudio();
  const soundOn = ref(false);
  const musicVolume = ref(25);
  const effectVolume = ref(50);
  let suppressNextStateCue = true;

  try {
    const saved = JSON.parse(localStorage.getItem("avalon_audio") || "{}");
    musicVolume.value = saved.music ?? 25;
    effectVolume.value = saved.effects ?? 50;
  } catch {}

  function updateVolume() {
    sound.volumes(musicVolume.value / 100, effectVolume.value / 100);
    try {
      localStorage.setItem(
        "avalon_audio",
        JSON.stringify({
          music: musicVolume.value,
          effects: effectVolume.value,
        }),
      );
    } catch {}
  }

  async function toggleSound() {
    try {
      if (soundOn.value) {
        sound.disable();
        soundOn.value = false;
      } else {
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

  watch(connection, (value) => {
    if (value === "연결 중") suppressNextStateCue = true;
    if (value === "연결 끊김" && room.value) {
      sound.scene({ ...room.value, paused: true });
    }
  });

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
