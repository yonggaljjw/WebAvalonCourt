# 역할 초상화 이미지

`merlin.png`, `assassin.png`처럼 서버/프론트에서 사용하는 역할 코드와 파일명을 맞춰 두었습니다.
`frontend/src/constants/game.js`의 `roleImage(role)`가 `/assets/roles/{role}.png` 형태로 경로를 만들기 때문에 새 역할을 추가할 때는 역할 코드와 이미지 파일명을 함께 맞추는 것이 좋습니다.
