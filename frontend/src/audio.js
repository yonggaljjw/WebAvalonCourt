// 외부 음원/API 없이 직접 작곡한 패턴을 Web Audio로 합성합니다.
// 브라우저의 자동재생 정책에 맞춰 사용자가 소리 켜기를 눌렀을 때만 시작합니다.
export function transitionCue(before, after) {
  if (!before || before.code !== after.code) return null // 최초 접속/복귀 시 과거 효과음 재생 금지
  if (before.phase !== 'ended' && after.phase === 'ended') return after.winner === 'aborted' ? 'abort' : after.winner === 'good' ? 'victory' : 'defeat'
  if (!before.paused && after.paused) return 'pause'
  if (before.paused && !after.paused) return 'resume'
  if (after.quests.length > before.quests.length) return after.quests.at(-1).success ? 'success' : 'failure'
  if (after.history.length > before.history.length && !after.history.at(-1).approved) return 'reject'
  if (before.phase !== after.phase || before.round !== after.round) return after.phase
  return null
}
export class AvalonAudio {
  constructor() { this.enabled=false; this.musicVolume=.25; this.effectVolume=.5; this.mode='lobby'; this.round=1; this.nodes=new Set() }
  async enable() {
    const Context=globalThis.AudioContext || globalThis.webkitAudioContext
    if (!Context) throw Error('이 브라우저에서는 소리를 지원하지 않습니다.')
    if (!this.ctx) {
      this.ctx=new Context(); this.master=this.ctx.createGain(); this.master.connect(this.ctx.destination)
      this.music=this.ctx.createGain(); this.music.connect(this.master)
      this.effects=this.ctx.createGain(); this.effects.connect(this.master)
    }
    await this.ctx.resume()
    if(this.ctx.state!=='running') throw Error('소리 켜기를 다시 눌러주세요.')
    this.enabled=true; this.master.gain.setTargetAtTime(.7,this.ctx.currentTime,.05)
    this.volumes(this.musicVolume,this.effectVolume); this.startMusic()
  }
  volumes(music,effects) {
    this.musicVolume=Math.max(0,Math.min(1,Number(music)||0)); this.effectVolume=Math.max(0,Math.min(1,Number(effects)||0))
    if(this.ctx){this.music.gain.setTargetAtTime(this.musicVolume,this.ctx.currentTime,.05);this.effects.gain.setTargetAtTime(this.effectVolume,this.ctx.currentTime,.05)}
  }
  // 음이 끝나면 오디오 노드를 해제하여 반복 재생 중 메모리가 쌓이지 않게 합니다.
  note(midi,start,duration,volume,bus,type='sine') {
    const o=this.ctx.createOscillator(),g=this.ctx.createGain();o.type=type;o.frequency.value=440*2**((midi-69)/12)
    o.connect(g);g.connect(bus);g.gain.setValueAtTime(0,start);g.gain.linearRampToValueAtTime(volume,start+.025);g.gain.exponentialRampToValueAtTime(.0001,start+duration)
    const node={o,g,bus};this.nodes.add(node);o.onended=()=>{o.disconnect();g.disconnect();this.nodes.delete(node)};o.start(start);o.stop(start+duration+.03)
  }
  stopMusic() {clearInterval(this.timer);this.timer=null;for(const n of this.nodes)if(n.bus===this.music){try{n.o.stop()}catch{}}}
  startMusic() {
    this.stopMusic(); if(!this.enabled||['paused','ended'].includes(this.mode)||document.hidden)return
    this.step=0;this.next=this.ctx.currentTime+.08
    const schedule=()=>{
      if(!this.enabled||this.ctx.state!=='running')return
      if(this.next<this.ctx.currentTime)this.next=this.ctx.currentTime+.06
      // 한 번에 0.4초만 예약하여 음소거·단계 변경에 빠르게 반응합니다.
      while(this.next<this.ctx.currentTime+.4){
        const tense=['vote','quest','assassination'].includes(this.mode), beat=tense?.48:.68
        const roots=tense?[45,41,43,40]:[50,46,48,45], root=roots[Math.floor(this.step/8)%4]
        const motif=[12,19,15,22,19,15,24,19], pitch=root+motif[(this.step+this.round-1)%8]
        this.note(pitch,this.next,1.1,.085,this.music,'triangle')
        if(this.step%8===0){this.note(root,this.next,beat*8,.14,this.music);this.note(root+7,this.next,beat*7,.065,this.music)}
        this.next+=beat;this.step++
      }
    }
    schedule();this.timer=setInterval(schedule,100)
  }
  scene(room) {const mode=room?.paused?'paused':room?.phase||'lobby',round=room?.round||1;if(mode!==this.mode||round!==this.round){this.mode=mode;this.round=round;this.startMusic()}}
  cue(name) {
    if(!this.enabled||!this.ctx||this.ctx.state!=='running'||document.hidden)return
    const scores={proposal:[62,69,74],vote:[64,64,71],quest:[50,57,62],lady:[74,81,86],assassination:[45,46,45],success:[62,66,69,74],failure:[50,49,45],reject:[57,53],victory:[62,66,69,74,78],defeat:[50,45,41,38],abort:[55,50],pause:[60,55],resume:[55,60]}
    const notes=scores[name];if(!notes)return
    notes.forEach((n,i)=>this.note(n,this.ctx.currentTime+.02+i*.18,.7,.18,this.effects,name==='failure'||name==='defeat'?'triangle':'sine'))
  }
  disable(){this.enabled=false;this.stopMusic();if(this.ctx){this.master.gain.setValueAtTime(0,this.ctx.currentTime);for(const n of this.nodes){try{n.o.stop()}catch{}}}}
  visibility(){if(document.hidden)this.stopMusic();else this.startMusic()}
  close(){this.disable();this.ctx?.close().catch(()=>{})}
}
