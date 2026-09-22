"""별도 SQLite DB로 HTTP/WS 통합을 검증합니다. 배포 DB는 MySQL입니다."""
import os
import tempfile
import time
from contextlib import ExitStack
os.environ['APP_SECRET']='integration-test-secret-not-for-production'
os.environ['DATABASE_URL']='sqlite:///'+tempfile.mktemp(suffix='.db')
from fastapi.testclient import TestClient
from app.main import app
from app.state import rooms, connections
ORIGIN={'origin':'http://localhost:8080'}

def test_http_websocket_game_and_leave():
    rooms.clear();connections.clear()
    with TestClient(app) as c:
        cookies=[]
        for i in range(5):
            c.cookies.clear()
            response=c.post('/api/guest',json={'name':f'기사{i}'},headers=ORIGIN)
            assert response.status_code==200
            cookies.append({'cookie':'avalon_session='+response.cookies['avalon_session'],**ORIGIN})
        c.cookies.clear()
        assert c.post('/api/rooms',json={'title':'차단'},headers={'origin':'https://evil.example'}).status_code==403
        response=c.post('/api/rooms',json={'title':'통합 테스트','password':'secret'},headers=cookies[0])
        assert response.status_code==200;code=response.json()['code']
        assert c.post(f'/api/rooms/{code}/join',json={'password':'wrong'},headers=cookies[1]).status_code==400
        for headers in cookies[1:]:assert c.post(f'/api/rooms/{code}/join',json={'password':'secret'},headers=headers).status_code==200
        assert 'password_hash' not in c.get('/api/rooms').json()[0]
        assert c.put(f'/api/rooms/{code}/settings',json={},headers=cookies[1]).status_code==400
        with ExitStack() as stack:
            sockets=[stack.enter_context(c.websocket_connect('/ws/'+code,headers=h)) for h in cookies]
            for ws in sockets:ws.send_json({'action':'ready','ready':True})
            # 수신 큐를 처리하며 실제 준비 완료 상태를 기다립니다.
            def until(ws,predicate):
                for _ in range(60):
                    data=ws.receive_json()
                    if data['type']=='state' and predicate(data['room']):return data['room']
                raise AssertionError('원하는 상태를 수신하지 못했습니다.')
            state=until(sockets[0],lambda r:all(p['ready'] for p in r['players']))
            time.sleep(.17);sockets[0].send_json({'action':'start'})
            state=until(sockets[0],lambda r:r['phase']=='proposal')
            assert state['me']['role'] and all('role' not in p for p in state['players'])
            time.sleep(.17)
            sockets[0].send_json({'action':'chat','message':'내 말풍선 확인','sender_id':'forged-user'})
            state=until(sockets[1],lambda r:bool(r['chat']))
            entry=state['chat'][-1]
            assert entry['sender_id']==state['players'][0]['id']
            assert entry['sender_id']!=state['me']['id'] and entry['id']
            assert entry['message']=='내 말풍선 확인'
            assert c.post(f'/api/rooms/{code}/leave',headers=cookies[4]).status_code==200
            state=until(sockets[0],lambda r:r['phase']=='ended')
            assert state['winner']=='aborted'
        # 종료 후 나간 사람은 새 게임을 만들 수 있어야 합니다.
        assert c.post('/api/rooms',json={'title':'다음 게임'},headers=cookies[4]).status_code==200
