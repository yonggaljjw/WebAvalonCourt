# audio — 파일 기반 사운드

| BGM 파일 | 공개 게임 장면 |
|---|---|
| bgm/camelot.ogg | 메인·로비 |
| bgm/council.ogg | 원정대 구성·호수 조사 |
| bgm/suspicion.ogg | 투표·원정 |
| bgm/last-shadow.ogg | 암살 |
| bgm/dawn.ogg | 선 진영 종료 |
| bgm/fallen-crown.ogg | 악 진영 종료 |

효과음은 `sfx/`의 WAV 11개입니다. 하나의 파일을 여러 이벤트가 공유할 수 있으며 실제 매핑은 `src/audio.js`의 SFX 객체를 따릅니다. 찬반·원정 카드의 개인 선택에 따라 공개 음악을 바꾸지 않습니다.

`useAudio.js`가 Vue의 room 변경을 관찰하고 `AvalonAudio`에 scene/cue를 전달합니다. 엔진은 fetch·decodeAudioData·재생·페이드·개별 음량·정리를 담당합니다. 파일 실패 시 기본 합성음을 사용하며 안내를 소리 설정에 표시합니다. 사용자 클릭 전에는 재생하지 않습니다.

`CREDITS.txt`는 소리 설정의 출처 링크가 여는 파일입니다. 음악 이용 정보는 루트 LICENSES_REMASTER.md와 같은 내용입니다.
