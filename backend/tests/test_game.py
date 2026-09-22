"""아발론 도메인 규칙 단위 테스트.

FastAPI나 DB 없이 Room/Player만 만들어 게임 규칙이 원하는 상태 전이를 만드는지 검증합니다.
테스트 이름 자체를 '요구사항 문장'처럼 읽으면 구현 규칙을 이해하기 쉽습니다.
"""

import time
import pytest
from app.domain.game import Room, Player, RuleError, TEAMS, EVIL_COUNT, EVIL


# 반복되는 테스트용 방/플레이어 생성을 줄이는 fixture 성격의 helper입니다.
def make(n=5,roles=None,lady=False):
    r=Room('TEST','테스트','p0',{'capacity':10,'roles':roles or [],'lady':lady,'discussion_seconds':180,'vote_seconds':60,'reconnect_seconds':30})
    r.players=[Player(f'p{i}',f'기사{i}',ready=True,connected=True) for i in range(n)]
    r.start('p0');return r

# 현재 라운드에 필요한 인원만큼 앞쪽 플레이어를 골라 팀 제안을 실행합니다.
def proposal(r):
    team=[p.id for p in r.players[:TEAMS[len(r.players)][r.round]]]
    r.action(r.players[r.leader].id,'propose',{'team':team})
    return team

# 모든 참가자가 같은 방향으로 투표하는 반복 코드를 helper로 묶었습니다.
def vote(r,yes=True):
    for p in r.players:r.action(p.id,'vote',{'approve':yes})

@pytest.mark.parametrize('n',range(5,11))
def test_role_balance(n):
    r=make(n);assert sum(p.role in EVIL for p in r.players)==EVIL_COUNT[n]
    assert [p.role for p in r.players].count('merlin')==1
    assert [p.role for p in r.players].count('assassin')==1

@pytest.mark.parametrize('n',range(5,11))
def test_all_quest_team_sizes(n):
    r=make(n)
    for i in range(5):
        r.round=i;r.enter_phase('proposal');proposal(r)
        assert len(r.team)==TEAMS[n][i]

def test_private_views():
    r=make(10,['percival','morgana','mordred','oberon'])
    for p in r.players:
        v=r.view(p.id)
        assert all('role' not in x for x in v['players'])
        k={x['id'] for x in v['me']['knowledge']}
        if p.role=='merlin':assert k=={x.id for x in r.players if x.role in EVIL and x.role!='mordred'}
        if p.role=='percival':assert k=={x.id for x in r.players if x.role in ('merlin','morgana')}
        if p.role=='oberon':assert not k
        if p.role in EVIL-{'oberon'}:assert k=={x.id for x in r.players if x.role in EVIL-{'oberon'} and x.id!=p.id}

def test_only_leader_and_correct_team():
    r=make();pid=next(p.id for p in r.players if p.id!=r.players[r.leader].id)
    with pytest.raises(RuleError):r.action(pid,'propose',{'team':['p0','p1']})
    with pytest.raises(RuleError):r.action(r.players[r.leader].id,'propose',{'team':['p0','p0']})
    with pytest.raises(RuleError):r.action(r.players[r.leader].id,'propose',{'team':['p0','intruder']})

def test_duplicate_vote_and_hidden_ballots():
    r=make();proposal(r);r.action('p0','vote',{'approve':True})
    assert 'votes' not in r.view('p1')
    with pytest.raises(RuleError):r.action('p0','vote',{'approve':False})

def test_tie_rejects():
    r=make(6);proposal(r)
    for i,p in enumerate(r.players):r.action(p.id,'vote',{'approve':i<3})
    assert r.rejected==1 and r.phase=='proposal'

def test_five_rejections():
    r=make()
    for _ in range(5):proposal(r);vote(r,False)
    assert r.winner=='evil'

def test_approval_resets_rejections():
    r=make();proposal(r);vote(r,False);proposal(r);vote(r)
    assert r.rejected==0 and r.phase=='quest'

def test_good_cannot_fail_and_nonmember_cannot_play():
    r=make();r.players[0].role='servant';proposal(r);vote(r)
    with pytest.raises(RuleError):r.action('p0','quest',{'success':False})
    with pytest.raises(RuleError):r.action('p4','quest',{'success':True})
    r.action('p0','quest',{'success':True})
    with pytest.raises(RuleError):r.action('p0','quest',{'success':True})

@pytest.mark.parametrize('n,fails,success',[(6,1,False),(7,1,True),(7,2,False),(10,1,True)])
def test_fourth_quest_threshold(n,fails,success):
    r=make(n);r.round=3
    for p in r.players:p.role='minion'
    team=proposal(r);vote(r)
    for i,pid in enumerate(team):r.action(pid,'quest',{'success':i>=fails})
    assert r.quests[-1]['success']==success
    assert not r.cards
    assert 'cards' not in r.view('p0')

@pytest.mark.parametrize('hit',[True,False])
def test_assassination_outcome(hit):
    r=make();r.quests=[{'success':True},{'success':True}];team=proposal(r);vote(r)
    for pid in team:r.action(pid,'quest',{'success':True})
    assert r.phase=='assassination'
    assassin=next(p for p in r.players if p.role=='assassin')
    target=next(p for p in r.players if p.role==('merlin' if hit else 'servant'))
    r.action(assassin.id,'assassinate',{'target':target.id});assert r.winner==('evil' if hit else 'good')

def test_three_failures():
    r=make();r.quests=[{'success':False},{'success':False}];r.players[0].role='minion';team=proposal(r);vote(r)
    for i,pid in enumerate(team):r.action(pid,'quest',{'success':i!=0})
    assert r.winner=='evil'

def test_lady_privacy_and_transfer():
    r=make(7,lady=True);r.round=1;holder=r.lady;team=proposal(r);vote(r)
    for pid in team:r.action(pid,'quest',{'success':True})
    assert r.phase=='lady'
    with pytest.raises(RuleError):r.action(holder,'lady',{'target':holder})
    target=next(p.id for p in r.players if p.id!=holder)
    r.action(holder,'lady',{'target':target})
    assert r.lady==target and len(r.view(holder)['me']['inspections'])==1
    assert not r.view(target)['me']['inspections']

def test_disconnect_resume_and_expiry():
    r=make();t=time.time();deadline=r.deadline;r.players[0].connected=False;r.players[0].seen=t;r.tick(t)
    assert r.pause_since
    with pytest.raises(RuleError):proposal(r)
    r.players[0].connected=True;r.tick(t+8)
    assert not r.pause_since and r.deadline==pytest.approx(deadline+8)
    r.players[0].connected=False;r.players[0].seen=t+8;r.tick(t+40)
    assert r.winner=='aborted'

def test_immediate_disconnect():
    r=make();r.settings['reconnect_seconds']=0;r.players[0].connected=False;r.tick(time.time())
    assert r.winner=='aborted'

def test_timeout():
    r=make();r.tick(r.deadline+1);assert r.winner=='aborted'

def test_start_requires_readiness_host_and_balance():
    r=make();r.phase='lobby';r.players[0].ready=False
    with pytest.raises(RuleError):r.start('p0')
    r.players[0].ready=True
    with pytest.raises(RuleError):r.start('p1')
    r.settings['roles']=['morgana','mordred']
    with pytest.raises(RuleError):r.start('p0')
