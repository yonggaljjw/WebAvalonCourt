"""아발론 순수 게임 엔진. 네트워크와 DB를 분리해 규칙을 독립적으로 검증합니다."""
import random
import time
from dataclasses import dataclass, field

TEAMS = {5:[2,3,2,3,3],6:[2,3,4,3,4],7:[2,3,3,4,4],8:[3,4,4,5,5],9:[3,4,4,5,5],10:[3,4,4,5,5]}
EVIL_COUNT = {5:2,6:2,7:3,8:3,9:3,10:4}
EVIL = {'assassin','morgana','mordred','oberon','minion'}
ROLE_NAMES = {'merlin':'멀린','percival':'퍼시벌','servant':'충성스러운 신하','assassin':'암살자','morgana':'모르가나','mordred':'모드레드','oberon':'오베론','minion':'악의 하수인'}

class RuleError(Exception):
    pass

def require(condition, message):
    if not condition:
        raise RuleError(message)

@dataclass
class Player:
    id: str
    name: str
    role: str = ''
    ready: bool = False
    connected: bool = False
    departed: bool = False
    seen: float = field(default_factory=time.time)

@dataclass
class Room:
    code: str
    title: str
    host: str
    settings: dict
    password_hash: str = ''
    players: list = field(default_factory=list)
    phase: str = 'lobby'
    round: int = 0
    leader: int = 0
    rejected: int = 0
    team: list = field(default_factory=list)
    votes: dict = field(default_factory=dict)
    cards: dict = field(default_factory=dict)
    quests: list = field(default_factory=list)
    history: list = field(default_factory=list)
    chat: list = field(default_factory=list)
    winner: str = ''
    reason: str = ''
    deadline: float = 0
    pause_since: float = 0
    lady: str = ''
    lady_used: list = field(default_factory=list)
    private: dict = field(default_factory=dict)
    updated: float = field(default_factory=time.time)

    def player(self, pid):
        p = next((p for p in self.players if p.id == pid), None)
        require(p is not None, '이 방의 참가자가 아닙니다.')
        return p

    def enter_phase(self, phase):
        self.phase = phase
        key = 'discussion_seconds' if phase == 'proposal' else 'vote_seconds'
        self.deadline = time.time() + self.settings[key]

    def finish(self, winner, reason):
        self.phase, self.winner, self.reason = 'ended', winner, reason
        self.deadline = self.pause_since = 0

    def start(self, pid):
        require(pid == self.host and self.phase == 'lobby', '방장만 대기실에서 시작할 수 있습니다.')
        n = len(self.players)
        require(n in TEAMS, '5~10명이 필요합니다.')
        require(all(p.ready and p.connected for p in self.players), '모두 접속하여 준비해야 합니다.')
        roles = ['merlin','assassin'] + self.settings['roles']
        evil = sum(r in EVIL for r in roles)
        good = len(roles)-evil
        require(evil <= EVIL_COUNT[n] and good <= n-EVIL_COUNT[n], '현재 인원에 비해 특수 역할이 많습니다.')
        roles += ['minion']*(EVIL_COUNT[n]-evil) + ['servant']*(n-EVIL_COUNT[n]-good)
        random.SystemRandom().shuffle(roles)
        for p,r in zip(self.players,roles):
            p.role = r
        self.leader = random.SystemRandom().randrange(n)
        self.lady = self.players[(self.leader-1)%n].id
        self.lady_used = [self.lady]
        self.enter_phase('proposal')

    def next_leader(self):
        self.leader = (self.leader+1)%len(self.players)
        self.team, self.votes, self.cards = [], {}, {}
        self.enter_phase('proposal')

    def action(self, pid, action, data):
        p = self.player(pid)
        require(not self.pause_since, '재접속 확인 중입니다.')
        if action == 'ready':
            require(self.phase == 'lobby', '대기실에서만 변경할 수 있습니다.')
            require(type(data.get('ready')) is bool, '준비 값을 확인해주세요.')
            p.ready = data['ready']; return
        if action == 'start':
            self.start(pid); return
        if action == 'propose':
            require(self.phase == 'proposal' and pid == self.players[self.leader].id, '원정대장만 제안할 수 있습니다.')
            team = data.get('team', [])
            require(isinstance(team,list) and all(isinstance(x,str) for x in team), '원정대 선택이 올바르지 않습니다.')
            require(len(team) == TEAMS[len(self.players)][self.round] and len(set(team)) == len(team), '정확한 원정 인원을 선택해주세요.')
            require(set(team) <= {p.id for p in self.players}, '존재하지 않는 참가자입니다.')
            self.team = team; self.votes = {}; self.enter_phase('vote')
        elif action == 'vote':
            require(self.phase == 'vote' and pid not in self.votes, '지금 투표할 수 없거나 이미 투표했습니다.')
            require(type(data.get('approve')) is bool, '찬성 또는 반대를 선택해주세요.')
            self.votes[pid] = data['approve']
            if len(self.votes) == len(self.players):
                approved = sum(self.votes.values()) > len(self.players)/2
                self.history.append({'type':'vote','round':self.round+1,'team':self.team[:],'votes':self.votes.copy(),'approved':approved})
                if approved:
                    self.rejected = 0; self.cards = {}; self.enter_phase('quest')
                else:
                    self.rejected += 1
                    if self.rejected == 5: self.finish('evil','원정대 구성이 5회 연속 부결되었습니다.')
                    else: self.next_leader()
        elif action == 'quest':
            require(self.phase == 'quest' and pid in self.team and pid not in self.cards, '원정대원만 한 번 제출할 수 있습니다.')
            require(type(data.get('success')) is bool, '카드를 선택해주세요.')
            require(p.role in EVIL or data['success'], '선 진영은 성공만 제출할 수 있습니다.')
            self.cards[pid] = data['success']
            if len(self.cards) == len(self.team):
                fails = sum(not c for c in self.cards.values())
                threshold = 2 if len(self.players)>=7 and self.round==3 else 1
                self.quests.append({'success':fails<threshold,'fails':fails,'team':self.team[:]})
                # 제출자의 카드는 공개 기록에 남기지 않고 즉시 지웁니다.
                self.cards = {}
                if sum(not q['success'] for q in self.quests)==3: self.finish('evil','원정이 3회 실패했습니다.')
                elif sum(q['success'] for q in self.quests)==3: self.enter_phase('assassination')
                elif self.settings['lady'] and self.round in (1,2,3): self.enter_phase('lady')
                else: self.round += 1; self.next_leader()
        elif action == 'assassinate':
            require(self.phase == 'assassination' and p.role == 'assassin', '암살 단계에서 암살자만 선택할 수 있습니다.')
            target = self.player(data.get('target'))
            require(target.role not in EVIL, '선 진영에서 암살 대상을 선택해주세요.')
            hit = target.role == 'merlin'
            self.finish('evil' if hit else 'good', f'{target.name} 암살: '+('멀린을 찾아냈습니다.' if hit else '멀린이 살아남았습니다.'))
        elif action == 'lady':
            require(self.phase == 'lady' and pid == self.lady, '호수의 여인 소유자만 조사할 수 있습니다.')
            target = self.player(data.get('target'))
            require(target.id not in self.lady_used, '이미 호수의 여인을 보유한 사람은 조사할 수 없습니다.')
            self.private.setdefault(pid,[]).append({'name':target.name,'evil':target.role in EVIL})
            self.lady = target.id; self.lady_used.append(target.id)
            self.round += 1; self.next_leader()
        else: raise RuleError('알 수 없는 행동입니다.')

    def tick(self, now):
        if self.phase in ('lobby','ended'): return
        missing = [p for p in self.players if not p.connected]
        if missing:
            if not self.pause_since: self.pause_since = now
            if any(now-p.seen >= self.settings['reconnect_seconds'] for p in missing):
                self.finish('aborted','재접속 확인에 실패하여 게임을 무효 종료했습니다.')
        elif self.pause_since:
            self.deadline += now-self.pause_since; self.pause_since=0
        elif now >= self.deadline:
            self.finish('aborted','제한시간 내 필수 행동이 완료되지 않아 무효 종료했습니다.')

    def view(self, pid):
        me = self.player(pid)
        # 클라이언트에 전체 역할을 전송한 뒤 숨기지 않습니다. 서버에서 허용된 정보만 구성합니다.
        knowledge = []
        for p in self.players:
            label = None
            if me.role == 'merlin' and p.role in EVIL and p.role != 'mordred': label = '악 진영'
            elif me.role == 'percival' and p.role in ('merlin','morgana'): label = '멀린 또는 모르가나'
            elif me.role in EVIL-{'oberon'} and p.role in EVIL-{'oberon'} and p.id != pid: label = '악의 동료'
            if label: knowledge.append({'id':p.id,'name':p.name,'label':label})
        return {'code':self.code,'title':self.title,'host':self.host,'settings':self.settings,'phase':self.phase,'round':self.round+1,'leader':self.players[self.leader].id if self.players else '', 'rejected':self.rejected,'team':self.team,'quests':self.quests,'history':self.history,'chat':self.chat,'winner':self.winner,'reason':self.reason,'deadline':self.deadline,'server_time':time.time(),'paused':bool(self.pause_since),'lady':self.lady,'lady_used':self.lady_used,'required':TEAMS.get(len(self.players),[0]*5)[min(self.round,4)],'submitted':list(self.cards if self.phase=='quest' else self.votes),'players':[{'id':p.id,'name':p.name,'ready':p.ready,'connected':p.connected,**({'role':p.role} if self.phase=='ended' else {})} for p in self.players], 'me':{'id':pid,'role':me.role,'evil':me.role in EVIL,'knowledge':knowledge,'inspections':self.private.get(pid,[])}}
