"""아발론의 핵심 게임 규칙을 담당하는 순수 도메인 모듈.

이 파일은 FastAPI, WebSocket, DB에 의존하지 않습니다.
즉, 네트워크 요청을 몰라도 `Room` 객체에 행동을 전달하면 게임 상태가 바뀌도록 만들었습니다.
그래서 `backend/tests/test_game.py`에서 서버를 띄우지 않고도 규칙만 빠르게 테스트할 수 있습니다.
"""

import random
import time
from dataclasses import dataclass, field

# 인원수별 1~5차 원정에 필요한 원정대 인원 수입니다.
TEAMS = {
    5: [2, 3, 2, 3, 3],
    6: [2, 3, 4, 3, 4],
    7: [2, 3, 3, 4, 4],
    8: [3, 4, 4, 5, 5],
    9: [3, 4, 4, 5, 5],
    10: [3, 4, 4, 5, 5],
}

# 전체 인원수에 따라 악 진영이 몇 명이어야 하는지 정의합니다.
EVIL_COUNT = {5: 2, 6: 2, 7: 3, 8: 3, 9: 3, 10: 4}

# 역할 코드 중 악 진영에 속하는 역할 모음입니다.
EVIL = {"assassin", "morgana", "mordred", "oberon", "minion"}

# 서버 로그/디버깅 등에서 사용할 수 있는 역할 한글 이름입니다.
ROLE_NAMES = {
    "merlin": "멀린",
    "percival": "퍼시벌",
    "servant": "충성스러운 신하",
    "assassin": "암살자",
    "morgana": "모르가나",
    "mordred": "모드레드",
    "oberon": "오베론",
    "minion": "악의 하수인",
}


class RuleError(Exception):
    """게임 규칙을 위반한 요청을 표현하는 전용 예외입니다."""


def require(condition, message):
    """조건이 거짓이면 RuleError를 발생시키는 간단한 검증 도우미입니다."""
    if not condition:
        raise RuleError(message)


@dataclass
class Player:
    """게임 참가자 한 명의 서버 상태입니다."""

    # 브라우저 세션에 연결되는 내부 사용자 ID입니다.
    id: str
    # 화면에 표시할 닉네임입니다.
    name: str
    # 게임이 시작되기 전에는 빈 문자열이고 시작 시 실제 역할 코드가 들어갑니다.
    role: str = ""
    # 대기실의 준비 여부입니다.
    ready: bool = False
    # 현재 WebSocket이 정상 연결되어 있는지 나타냅니다.
    connected: bool = False
    # 진행 중/종료 후 명시적으로 방을 나간 플레이어인지 표시합니다.
    departed: bool = False
    # 마지막으로 서버가 이 사용자의 활동을 확인한 시각(Unix timestamp)입니다.
    seen: float = field(default_factory=time.time)


@dataclass
class Room:
    """한 아발론 방의 모든 게임 상태를 보관하고 규칙을 실행합니다."""

    # ---- 방의 기본 정보 ----
    code: str
    title: str
    host: str
    settings: dict
    password_hash: str = ""
    players: list = field(default_factory=list)

    # ---- 게임 진행 상태 ----
    # lobby -> proposal -> vote -> quest -> ... -> ended 형태로 이동합니다.
    phase: str = "lobby"
    # 내부에서는 0부터 시작합니다. 클라이언트에는 view()에서 +1 하여 보여줍니다.
    round: int = 0
    # 현재 원정대장의 players 리스트 인덱스입니다.
    leader: int = 0
    # 연속으로 원정대 승인이 부결된 횟수입니다.
    rejected: int = 0

    # ---- 현재 단계에서만 사용하는 임시 상태 ----
    team: list = field(default_factory=list)
    votes: dict = field(default_factory=dict)
    cards: dict = field(default_factory=dict)

    # ---- 누적 기록 ----
    quests: list = field(default_factory=list)
    history: list = field(default_factory=list)
    chat: list = field(default_factory=list)

    # ---- 종료/시간 관리 ----
    winner: str = ""
    reason: str = ""
    deadline: float = 0
    pause_since: float = 0

    # ---- 호수의 여인 및 개인 비밀정보 ----
    lady: str = ""
    lady_used: list = field(default_factory=list)
    private: dict = field(default_factory=dict)

    # 방이 마지막으로 변경된 시각입니다. 오래된 방 정리에 사용합니다.
    updated: float = field(default_factory=time.time)

    def player(self, pid):
        """플레이어 ID로 참가자를 찾고, 없으면 규칙 오류를 발생시킵니다."""
        player = next((player for player in self.players if player.id == pid), None)
        require(player is not None, "이 방의 참가자가 아닙니다.")
        return player

    def enter_phase(self, phase):
        """게임 단계를 바꾸고 해당 단계의 제한시간을 새로 계산합니다."""
        self.phase = phase

        # 팀을 고르는 proposal 단계는 토론 시간을 사용하고,
        # 그 외 행동 단계는 vote_seconds를 공통 제한시간으로 사용합니다.
        key = "discussion_seconds" if phase == "proposal" else "vote_seconds"
        self.deadline = time.time() + self.settings[key]

    def finish(self, winner, reason):
        """게임을 종료하고 종료 사유를 기록합니다."""
        self.phase = "ended"
        self.winner = winner
        self.reason = reason
        self.deadline = 0
        self.pause_since = 0

    def start(self, pid):
        """대기실 상태를 검증하고 역할을 배정한 뒤 첫 원정을 시작합니다."""
        require(
            pid == self.host and self.phase == "lobby",
            "방장만 대기실에서 시작할 수 있습니다.",
        )

        player_count = len(self.players)
        require(player_count in TEAMS, "5~10명이 필요합니다.")
        require(
            all(player.ready and player.connected for player in self.players),
            "모두 접속하여 준비해야 합니다.",
        )

        # 멀린과 암살자는 항상 포함하고, 방장이 선택한 특수 역할을 추가합니다.
        roles = ["merlin", "assassin"] + self.settings["roles"]
        evil_count = sum(role in EVIL for role in roles)
        good_count = len(roles) - evil_count

        # 선택한 특수 역할만으로 진영 정원을 초과하면 게임을 시작할 수 없습니다.
        require(
            evil_count <= EVIL_COUNT[player_count]
            and good_count <= player_count - EVIL_COUNT[player_count],
            "현재 인원에 비해 특수 역할이 많습니다.",
        )

        # 남는 악/선 자리는 각각 일반 하수인과 충성스러운 신하로 채웁니다.
        roles += ["minion"] * (EVIL_COUNT[player_count] - evil_count)
        roles += ["servant"] * (
            player_count - EVIL_COUNT[player_count] - good_count
        )

        # 보안용 난수 생성기를 사용해 역할 배정 순서를 섞습니다.
        random.SystemRandom().shuffle(roles)
        for player, role in zip(self.players, roles):
            player.role = role

        # 첫 원정대장을 무작위로 정합니다.
        self.leader = random.SystemRandom().randrange(player_count)

        # 호수의 여인 토큰은 첫 대장의 바로 이전 순서 플레이어에게 줍니다.
        self.lady = self.players[(self.leader - 1) % player_count].id
        self.lady_used = [self.lady]

        self.enter_phase("proposal")

    def next_leader(self):
        """대장 순서를 한 칸 넘기고 다음 원정대 구성 단계로 이동합니다."""
        self.leader = (self.leader + 1) % len(self.players)

        # 이전 제안/투표/원정 카드의 임시값은 다음 제안 전에 비웁니다.
        self.team = []
        self.votes = {}
        self.cards = {}
        self.enter_phase("proposal")

    def action(self, pid, action, data):
        """클라이언트가 보낸 게임 행동 하나를 규칙에 따라 처리합니다.

        `action` 문자열에 따라 준비, 시작, 제안, 투표, 원정, 암살,
        호수의 여인 조사를 분기합니다. 잘못된 단계나 입력은 RuleError로 막습니다.
        """
        player = self.player(pid)

        # 누군가 연결이 끊겨 일시정지된 동안에는 게임 행동을 받지 않습니다.
        require(not self.pause_since, "재접속 확인 중입니다.")

        # 1) 대기실 준비 상태 변경
        if action == "ready":
            require(self.phase == "lobby", "대기실에서만 변경할 수 있습니다.")
            require(type(data.get("ready")) is bool, "준비 값을 확인해주세요.")
            player.ready = data["ready"]
            return

        # 2) 방장이 게임 시작
        if action == "start":
            self.start(pid)
            return

        # 3) 원정대장이 이번 원정에 참가할 팀을 제안
        if action == "propose":
            require(
                self.phase == "proposal"
                and pid == self.players[self.leader].id,
                "원정대장만 제안할 수 있습니다.",
            )
            team = data.get("team", [])
            require(
                isinstance(team, list)
                and all(isinstance(member_id, str) for member_id in team),
                "원정대 선택이 올바르지 않습니다.",
            )
            require(
                len(team) == TEAMS[len(self.players)][self.round]
                and len(set(team)) == len(team),
                "정확한 원정 인원을 선택해주세요.",
            )
            require(
                set(team) <= {member.id for member in self.players},
                "존재하지 않는 참가자입니다.",
            )

            self.team = team
            self.votes = {}
            self.enter_phase("vote")
            return

        # 4) 모든 플레이어가 제안된 원정대를 승인/반대
        if action == "vote":
            require(
                self.phase == "vote" and pid not in self.votes,
                "지금 투표할 수 없거나 이미 투표했습니다.",
            )
            require(
                type(data.get("approve")) is bool,
                "찬성 또는 반대를 선택해주세요.",
            )
            self.votes[pid] = data["approve"]

            # 모든 참가자가 투표한 뒤에만 결과를 계산합니다.
            if len(self.votes) == len(self.players):

                # True(찬성)는 1, False(반대)는 0으로 계산되므로
                # 전체 값을 더하면 찬성표 수를 구할 수 있습니다.
                approve_count = sum(self.votes.values())

                # 전체 투표 수에서 찬성표를 제외하면 반대표 수입니다.
                reject_count = len(self.votes) - approve_count

                # 과반수 초과만 승인되므로 동수는 부결됩니다.
                approved = approve_count > len(self.players) / 2

                # 개인별 투표 결과는 공개 기록(history)에 저장하지 않습니다.
                # 찬성/반대 인원수와 최종 승인 여부만 남깁니다.
                self.history.append(
                    {
                        "type": "vote",
                        "round": self.round + 1,
                        "team": self.team[:],
                        "approve_count": approve_count,
                        "reject_count": reject_count,
                        "approved": approved,
                    }
                )

                if approved:
                    self.rejected = 0
                    self.cards = {}
                    self.enter_phase("quest")
                else:
                    self.rejected += 1
                    if self.rejected == 5:
                        self.finish(
                            "evil",
                            "원정대 구성이 5회 연속 부결되었습니다.",
                        )
                    else:
                        self.next_leader()
            return

        # 5) 승인된 원정대원들이 성공/실패 카드를 비공개 제출
        if action == "quest":
            require(
                self.phase == "quest"
                and pid in self.team
                and pid not in self.cards,
                "원정대원만 한 번 제출할 수 있습니다.",
            )
            require(type(data.get("success")) is bool, "카드를 선택해주세요.")

            # 선 진영은 규칙상 실패 카드를 낼 수 없습니다.
            require(
                player.role in EVIL or data["success"],
                "선 진영은 성공만 제출할 수 있습니다.",
            )
            self.cards[pid] = data["success"]

            # 모든 원정대원이 카드를 낸 뒤에 결과를 계산합니다.
            if len(self.cards) == len(self.team):
                fail_count = sum(not card for card in self.cards.values())

                # 7명 이상 게임의 4차 원정(내부 round=3)은 실패 2장이 필요합니다.
                threshold = (
                    2 if len(self.players) >= 7 and self.round == 3 else 1
                )
                self.quests.append(
                    {
                        "success": fail_count < threshold,
                        "fails": fail_count,
                        "team": self.team[:],
                    }
                )

                # 누가 어떤 카드를 냈는지는 공개하면 안 되므로 즉시 제거합니다.
                self.cards = {}

                failed_quests = sum(not quest["success"] for quest in self.quests)
                successful_quests = sum(quest["success"] for quest in self.quests)

                if failed_quests == 3:
                    self.finish("evil", "원정이 3회 실패했습니다.")
                elif successful_quests == 3:
                    self.enter_phase("assassination")
                elif self.settings["lady"] and self.round in (1, 2, 3):
                    self.enter_phase("lady")
                else:
                    self.round += 1
                    self.next_leader()
            return

        # 6) 선 진영이 원정 3회 성공한 뒤 암살자가 멀린 후보를 선택
        if action == "assassinate":
            require(
                self.phase == "assassination" and player.role == "assassin",
                "암살 단계에서 암살자만 선택할 수 있습니다.",
            )
            target = self.player(data.get("target"))
            require(
                target.role not in EVIL,
                "선 진영에서 암살 대상을 선택해주세요.",
            )

            hit = target.role == "merlin"
            self.finish(
                "evil" if hit else "good",
                f"{target.name} 암살: "
                + ("멀린을 찾아냈습니다." if hit else "멀린이 살아남았습니다."),
            )
            return

        # 7) 호수의 여인 소유자가 아직 토큰을 가져본 적 없는 사람을 조사
        if action == "lady":
            require(
                self.phase == "lady" and pid == self.lady,
                "호수의 여인 소유자만 조사할 수 있습니다.",
            )
            target = self.player(data.get("target"))
            require(
                target.id not in self.lady_used,
                "이미 호수의 여인을 보유한 사람은 조사할 수 없습니다.",
            )

            # 조사 결과는 조사자 개인에게만 보이도록 private에 저장합니다.
            self.private.setdefault(pid, []).append(
                {"name": target.name, "evil": target.role in EVIL}
            )

            # 조사 대상에게 토큰이 넘어가고 다음 라운드로 진행합니다.
            self.lady = target.id
            self.lady_used.append(target.id)
            self.round += 1
            self.next_leader()
            return

        raise RuleError("알 수 없는 행동입니다.")

    def tick(self, now):
        """1초 주기의 서버 시계에서 호출되어 연결 끊김/시간초과를 처리합니다."""
        # 로비와 종료 상태는 게임 제한시간을 검사할 필요가 없습니다.
        if self.phase in ("lobby", "ended"):
            return

        missing = [player for player in self.players if not player.connected]

        if missing:
            # 첫 연결 중단 시각을 기록하여 게임 시간을 일시정지합니다.
            if not self.pause_since:
                self.pause_since = now

            # 한 명이라도 재접속 유예시간을 넘기면 게임을 무효 종료합니다.
            if any(
                now - player.seen >= self.settings["reconnect_seconds"]
                for player in missing
            ):
                self.finish(
                    "aborted",
                    "재접속 확인에 실패하여 게임을 무효 종료했습니다.",
                )
        elif self.pause_since:
            # 모두 돌아오면 멈춰 있던 시간만큼 deadline도 뒤로 미룹니다.
            self.deadline += now - self.pause_since
            self.pause_since = 0
        elif now >= self.deadline:
            # 필요한 행동을 제한시간 안에 끝내지 못한 경우 자동 선택 대신 무효 종료합니다.
            self.finish(
                "aborted",
                "제한시간 내 필수 행동이 완료되지 않아 무효 종료했습니다.",
            )

    def view(self, pid):
        """특정 플레이어에게 전송해도 되는 상태만 골라 JSON 형태로 만듭니다.

        서버 내부에는 모든 역할이 들어 있지만, 게임 중에 전체 역할을 브라우저로 보내면
        개발자 도구로 상대 역할을 볼 수 있습니다. 따라서 플레이어별로 허용된 정보만 구성합니다.
        """
        me = self.player(pid)

        # 역할별로 게임 시작 시 알 수 있는 상대 정보를 계산합니다.
        knowledge = []
        for player in self.players:
            label = None

            # 멀린: 모드레드를 제외한 악을 봅니다.
            if me.role == "merlin" and player.role in EVIL and player.role != "mordred":
                label = "악 진영"
            # 퍼시벌: 멀린/모르가나 두 후보를 같은 표시로 봅니다.
            elif me.role == "percival" and player.role in ("merlin", "morgana"):
                label = "멀린 또는 모르가나"
            # 오베론이 아닌 악: 오베론을 제외한 다른 악 동료를 봅니다.
            elif (
                me.role in EVIL - {"oberon"}
                and player.role in EVIL - {"oberon"}
                and player.id != pid
            ):
                label = "악의 동료"

            if label:
                knowledge.append(
                    {"id": player.id, "name": player.name, "label": label}
                )

        # 투표 상세와 원정 카드 제출자의 정체 등 비밀 상태는 의도적으로 포함하지 않습니다.
        return {
            "code": self.code,
            "title": self.title,
            "host": self.host,
            "settings": self.settings,
            "phase": self.phase,
            "round": self.round + 1,
            "leader": self.players[self.leader].id if self.players else "",
            "rejected": self.rejected,
            "team": self.team,
            "quests": self.quests,
            "history": self.history,
            "chat": self.chat,
            "winner": self.winner,
            "reason": self.reason,
            "deadline": self.deadline,
            "server_time": time.time(),
            "paused": bool(self.pause_since),
            "lady": self.lady,
            "lady_used": self.lady_used,
            "required": TEAMS.get(len(self.players), [0] * 5)[min(self.round, 4)],
            # 현재 행동을 이미 제출한 사람만 알려주고, 제출 내용 자체는 숨깁니다.
            "submitted": list(self.cards if self.phase == "quest" else self.votes),
            "players": [
                {
                    "id": player.id,
                    "name": player.name,
                    "ready": player.ready,
                    "connected": player.connected,
                    # 게임이 끝난 뒤에만 전체 역할을 공개합니다.
                    **({"role": player.role} if self.phase == "ended" else {}),
                }
                for player in self.players
            ],
            "me": {
                "id": pid,
                "role": me.role,
                "evil": me.role in EVIL,
                "knowledge": knowledge,
                "inspections": self.private.get(pid, []),
            },
        }
