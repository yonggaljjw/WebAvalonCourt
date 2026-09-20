"""HTTP는 방 관리, WebSocket은 실시간 행동에 사용합니다. 단일 worker로 실행하세요."""
import asyncio
import hashlib
import hmac
import json
import os
import secrets
import time
from contextlib import asynccontextmanager, suppress
from dataclasses import asdict
from urllib.parse import quote_plus
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import create_engine, text
from .game import Room, Player, RuleError, require

SECRET = os.environ['APP_SECRET']
url = os.getenv('DATABASE_URL') or ('mysql+pymysql://'+quote_plus(os.environ['MYSQL_USER'])+':'+quote_plus(os.environ['MYSQL_PASSWORD'])+'@db/'+quote_plus(os.environ['MYSQL_DATABASE'])+'?charset=utf8mb4')
engine = create_engine(url, pool_pre_ping=True)
rooms = {}
connections = {}
lock = asyncio.Lock()
origins = set(os.getenv('ALLOWED_ORIGINS','http://localhost:8080,http://127.0.0.1:8080').split(','))

def digest(value):
    return hmac.new(SECRET.encode(),value.encode(),hashlib.sha256).hexdigest()

def save():
    # 한 트랜잭션으로 저장하며 원정 카드가 담긴 스냅샷은 외부 API로 제공하지 않습니다.
    with engine.begin() as c:
        c.execute(text('DELETE FROM room_state'))
        for room in rooms.values():
            c.execute(text('INSERT INTO room_state (code, payload) VALUES (:code,:payload)'),{'code':room.code,'payload':json.dumps(asdict(room),ensure_ascii=False)})

def session(token):
    require(bool(token), '닉네임으로 먼저 입장해주세요.')
    with engine.connect() as c:
        row=c.execute(text('SELECT pid,name,expires FROM sessions WHERE token=:token'),{'token':digest(token)}).mappings().first()
    require(row is not None and row['expires']>time.time(),'입장 정보가 만료되었습니다. 다시 입장해주세요.')
    return dict(row)

async def broadcast(room):
    for p in room.players:
        ws=connections.get((room.code,p.id))
        if ws:
            try: await asyncio.wait_for(ws.send_json({'type':'state','room':room.view(p.id)}),2)
            except Exception: p.connected=False

async def clock():
    while True:
        await asyncio.sleep(1)
        async with lock:
            changed=False
            for room in list(rooms.values()):
                before=(room.phase,room.pause_since)
                for p in room.players:
                    if p.connected and time.time()-p.seen>15: p.connected=False
                if room.phase=='lobby':
                    retained=[p for p in room.players if p.connected or time.time()-p.seen<max(15,room.settings['reconnect_seconds'])]
                    if len(retained)!=len(room.players):
                        room.players=retained;room.leader=0;changed=True
                        if not retained:
                            del rooms[room.code];continue
                        if room.host not in {p.id for p in retained}:room.host=retained[0].id
                        await broadcast(room)
                room.tick(time.time())
                if before!=(room.phase,room.pause_since):
                    changed=True; await broadcast(room)
                if time.time()-room.updated>86400 and room.phase in ('lobby','ended') and not any(p.connected for p in room.players):
                    del rooms[room.code]; changed=True
            if changed: save()

@asynccontextmanager
async def lifespan(app):
    with engine.begin() as c:
        c.execute(text('CREATE TABLE IF NOT EXISTS room_state (code VARCHAR(12) PRIMARY KEY, payload LONGTEXT NOT NULL)'))
        c.execute(text('CREATE TABLE IF NOT EXISTS sessions (token VARCHAR(64) PRIMARY KEY, pid VARCHAR(32) NOT NULL, name VARCHAR(48) NOT NULL, expires DOUBLE NOT NULL)'))
        c.execute(text('DELETE FROM sessions WHERE expires < :now'),{'now':time.time()})
        for row in c.execute(text('SELECT payload FROM room_state')):
            data=json.loads(row[0]);data['players']=[Player(**p) for p in data['players']]
            room=Room(**data)
            for p in room.players: p.connected=False
            if room.phase not in ('lobby','ended'): room.finish('aborted','서버가 재시작되어 게임을 무효 종료했습니다.')
            rooms[room.code]=room
    save()
    task=asyncio.create_task(clock())
    yield
    task.cancel()
    with suppress(asyncio.CancelledError): await task
    engine.dispose()

app=FastAPI(title='Avalon Court',lifespan=lifespan,docs_url=None,redoc_url=None)

@app.exception_handler(RuleError)
async def rule_error(request,exc): return JSONResponse({'detail':str(exc)},status_code=400)

@app.middleware('http')
async def protect(request,call_next):
    if request.method in ('POST','PUT','DELETE','PATCH') and request.headers.get('origin') not in origins:
        return JSONResponse({'detail':'허용되지 않은 출처입니다. ALLOWED_ORIGINS를 확인해주세요.'},status_code=403)
    response=await call_next(request)
    response.headers['Cache-Control']='no-store'
    response.headers['X-Content-Type-Options']='nosniff'
    return response

class Guest(BaseModel):
    name: str = Field(min_length=1,max_length=16)
class Settings(BaseModel):
    model_config=ConfigDict(extra='forbid')
    capacity: int = Field(default=10,ge=5,le=10)
    roles: list[str] = Field(default_factory=lambda:['percival','morgana'])
    lady: bool = False
    discussion_seconds: int = Field(default=180,ge=30,le=600)
    vote_seconds: int = Field(default=60,ge=15,le=180)
    reconnect_seconds: int = Field(default=30,ge=0,le=120)
class Create(BaseModel):
    title: str = Field(min_length=1,max_length=40)
    password: str = Field(default='',max_length=64)
    settings: Settings = Field(default_factory=Settings)
class Join(BaseModel):
    password: str = Field(default='',max_length=64)

def valid_settings(s):
    require(len(s.roles)==len(set(s.roles)) and set(s.roles)<={'percival','morgana','mordred','oberon'},'특수 역할 설정이 올바르지 않습니다.')
    from .game import EVIL_COUNT,EVIL
    require(1+sum(r in EVIL for r in s.roles)<=EVIL_COUNT[s.capacity],'정원보다 악의 특수 역할이 많습니다.')
    return s.model_dump()

def current(request): return session(request.cookies.get('avalon_session'))
def get_room(code):
    require(code in rooms,'방을 찾을 수 없습니다.')
    return rooms[code]

@app.get('/api/health')
def health():
    with engine.connect() as c: c.execute(text('SELECT 1'))
    return {'status':'ok'}

@app.get('/api/me')
def me(request:Request): return current(request)

@app.post('/api/guest')
async def guest(body:Guest,response:Response,request:Request):
    name=body.name.strip(); require(name,'닉네임을 입력해주세요.')
    old=None
    try: old=current(request)
    except RuleError: pass
    if old:
        require(not any(any(p.id==old['pid'] and not p.departed for p in r.players) for r in rooms.values()),'방에서 먼저 나가주세요.')
    token=secrets.token_urlsafe(32);pid=secrets.token_hex(12)
    with engine.begin() as c:
        c.execute(text('INSERT INTO sessions (token,pid,name,expires) VALUES (:token,:pid,:name,:expires)'),{'token':digest(token),'pid':pid,'name':name,'expires':time.time()+7*86400})
    response.set_cookie('avalon_session',token,httponly=True,samesite='strict',secure=os.getenv('COOKIE_SECURE','false')=='true',max_age=7*86400)
    return {'pid':pid,'name':name}

@app.get('/api/rooms')
async def list_rooms():
    return [{'code':r.code,'title':r.title,'count':len(r.players),'capacity':r.settings['capacity'],'phase':r.phase,'locked':bool(r.password_hash),'roles':r.settings['roles']} for r in rooms.values()]

@app.post('/api/rooms')
async def create(body:Create,request:Request):
    user=current(request)
    async with lock:
        require(len(rooms)<200,'방 개수 한도에 도달했습니다.')
        require(not any(any(p.id==user['pid'] and not p.departed for p in r.players) for r in rooms.values()),'기존 방에서 먼저 나가주세요.')
        code=secrets.token_hex(3).upper()
        while code in rooms: code=secrets.token_hex(3).upper()
        room=Room(code,body.title.strip() or '원탁의 기사들',user['pid'],valid_settings(body.settings),digest(body.password) if body.password else '')
        room.players.append(Player(user['pid'],user['name']));rooms[code]=room;save()
        return {'code':code}

@app.post('/api/rooms/{code}/join')
async def join(code:str,body:Join,request:Request):
    user=current(request)
    async with lock:
        room=get_room(code)
        if any(p.id==user['pid'] and not p.departed for p in room.players): return {'code':code}
        require(room.phase=='lobby','진행 중이거나 종료된 방입니다.')
        require(not room.password_hash or hmac.compare_digest(room.password_hash,digest(body.password)),'방 비밀번호가 틀립니다.')
        require(len(room.players)<room.settings['capacity'],'방이 가득 찼습니다.')
        require(not any(any(p.id==user['pid'] and not p.departed for p in r.players) for r in rooms.values()),'기존 방에서 먼저 나가주세요.')
        require(not any(p.name==user['name'] for p in room.players),'이 방에 같은 닉네임이 있습니다.')
        room.players.append(Player(user['pid'],user['name']));room.updated=time.time();save();await broadcast(room)
    return {'code':code}

@app.put('/api/rooms/{code}/settings')
async def settings(code:str,body:Settings,request:Request):
    user=current(request)
    async with lock:
        room=get_room(code); require(room.host==user['pid'] and room.phase=='lobby','방장만 대기실에서 설정할 수 있습니다.')
        require(body.capacity>=len(room.players),'현재 인원보다 작은 정원은 설정할 수 없습니다.')
        room.settings=valid_settings(body)
        for p in room.players:p.ready=False
        save();await broadcast(room)
    return {'ok':True}

@app.post('/api/rooms/{code}/leave')
async def leave(code:str,request:Request):
    user=current(request)
    async with lock:
        room=get_room(code);require(not room.player(user['pid']).departed,'이미 퇴장한 방입니다.')
        if room.phase not in ('lobby','ended'): room.finish('aborted',f'{user["name"]} 님이 퇴장하여 게임을 무효 종료했습니다.')
        await broadcast(room)
        ws=connections.pop((code,user['pid']),None)
        if ws: await ws.close()
        if room.phase=='lobby':
            room.players=[p for p in room.players if p.id!=user['pid']]
            room.leader=0
        else:
            # 종료 결과에는 전체 역할을 보존하되 퇴장자는 다른 방에 참여할 수 있도록 분리합니다.
            p=room.player(user['pid']);p.departed=True;p.connected=False
        if not any(not p.departed for p in room.players):del rooms[code]
        elif room.host==user['pid']:room.host=next(p.id for p in room.players if not p.departed)
        save()
        if code in rooms:await broadcast(room)
    return {'ok':True}

@app.websocket('/ws/{code}')
async def websocket(ws:WebSocket,code:str):
    if ws.headers.get('origin') not in origins: await ws.close(code=1008);return
    try: user=session(ws.cookies.get('avalon_session')); room=get_room(code);p=room.player(user['pid']);require(not p.departed,'이미 퇴장한 방입니다.')
    except RuleError: await ws.close(code=1008);return
    await ws.accept(); key=(code,p.id)
    async with lock:
        old=connections.get(key);connections[key]=ws
        if old: await old.close(code=4001)
        p.connected=True;p.seen=time.time();room.tick(time.time());await broadcast(room)
    last_action=0
    try:
        while True:
            raw=await ws.receive_text()
            require(len(raw)<=4096,'메시지가 너무 큽니다.')
            try:
                data=json.loads(raw);require(isinstance(data,dict),'잘못된 요청입니다.')
                async with lock:
                    require(connections.get(key) is ws,'다른 창에서 접속했습니다.')
                    p.seen=time.time()
                    if data.get('action')=='ping':
                        p.connected=True;room.tick(time.time());await ws.send_json({'type':'pong'});continue
                    require(time.time()-last_action>=0.15,'너무 빠른 요청입니다.');last_action=time.time()
                    room.tick(time.time())
                    if data.get('action')=='chat':
                        msg=data.get('message','');require(isinstance(msg,str) and 0<len(msg.strip())<=300,'채팅은 1~300자로 입력해주세요.')
                        room.chat.append({'id':secrets.token_hex(12),'sender_id':p.id,'name':p.name,'message':msg.strip(),'at':time.time()});room.chat=room.chat[-100:]
                    else: room.action(p.id,data.get('action'),data)
                    room.updated=time.time();save();await broadcast(room)
            except (RuleError,ValueError,TypeError) as exc:
                await ws.send_json({'type':'error','message':str(exc) if isinstance(exc,RuleError) else '요청 형식을 확인해주세요.'})
    except (WebSocketDisconnect,RuleError): pass
    finally:
        async with lock:
            if connections.get(key) is ws:
                connections.pop(key,None);p.connected=False;p.seen=time.time();room.tick(time.time());save();await broadcast(room)
