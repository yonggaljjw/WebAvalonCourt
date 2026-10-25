// 서버 공개 상태만 읽는 연출 선택기. 역할·개인 표·카드·조사 정보는 읽지 않습니다.
export function presentationEvent(before, after) {
  if (!before || !after || before.code !== after.code) return null;
  if (before.phase !== "ended" && after.phase === "ended") {
    if (after.winner === "aborted")
      return {
        title: "원정 무효 종료",
        detail: "승패 없이 원탁을 마칩니다",
        tone: "neutral",
        icon: "emblems/royal-crest",
      };
    return {
      title:
        after.winner === "good"
          ? "빛의 서약이 지켜졌습니다"
          : "어둠이 왕관을 차지했습니다",
      detail: "최후의 판결",
      tone: after.winner === "good" ? "blue" : "red",
      icon:
        after.winner === "good"
          ? "tokens/quest-success"
          : "tokens/quest-failure",
    };
  }
  if (!before.paused && after.paused)
    return {
      title: "기사를 기다립니다",
      detail: "재접속 확인 중 · 진행 일시 정지",
      tone: "neutral",
      icon: "emblems/royal-crest",
    };
  if (before.paused && !after.paused)
    return {
      title: "원탁의 회의가 재개됩니다",
      detail: "연결 복구",
      tone: "neutral",
      icon: "emblems/royal-crest",
    };
  if (after.quests.length > before.quests.length) {
    const q = after.quests.at(-1);
    return {
      title: q.success ? "원정 성공" : "원정 실패",
      detail: `실패 카드 ${q.fails}장 · 원정 기록에 새겨졌습니다`,
      tone: q.success ? "blue" : "red",
      icon: `tokens/quest-${q.success ? "success" : "failure"}`,
    };
  }
  if (after.history.length > before.history.length) {
    const v = after.history.at(-1);
    return {
      title: v.approved ? "원정대 승인" : "원정대 부결",
      detail: `찬성 ${v.approve_count}명 · 반대 ${v.reject_count}명`,
      tone: v.approved ? "blue" : "red",
      icon: `tokens/${v.approved ? "approve" : "reject"}`,
    };
  }
  if (before.phase === "lobby" && after.phase === "proposal")
    return {
      title: "원탁의 서약",
      detail: "원정이 시작됩니다 · 나의 역할을 확인하세요",
      tone: "gold",
      icon: "emblems/royal-crest",
    };
  if (before.phase !== after.phase && after.phase === "assassination")
    return {
      title: "최후의 그림자",
      detail: "암살자가 멀린을 찾습니다",
      tone: "red",
      icon: "tokens/reject",
    };
  if (before.phase !== after.phase && after.phase === "lady")
    return {
      title: "호수의 속삭임",
      detail: "호수의 여인이 진영을 조사합니다",
      tone: "blue",
      icon: "tokens/quest-success",
    };
  if (before.leader !== after.leader && after.phase === "proposal")
    return {
      title: "새로운 원정대장",
      detail: "다음 서약을 이끌 기사가 정해졌습니다",
      tone: "gold",
      icon: "emblems/royal-crest",
    };
  return null;
}
