// Vite 개발 서버 설정입니다. Docker 배포의 Nginx 설정과는 별개로 로컬 개발 때 사용합니다.

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  // .vue Single File Component를 해석할 수 있게 Vue 플러그인을 등록합니다.
  plugins: [vue()],

  // npm run dev로 프론트만 띄울 때 API/WebSocket 요청을 로컬 FastAPI로 전달합니다.
  // 브라우저 입장에서는 같은 Vite 주소에 요청하므로 CORS 문제를 줄일 수 있습니다.
  server: {
    proxy: {
      "/api": "http://localhost:8000",
      "/ws": { target: "ws://localhost:8000", ws: true },
    },
  },
});
