// Vue 애플리케이션의 가장 첫 진입점입니다.
// 실제 화면 구성은 App.vue에 맡기고 여기서는 앱 생성과 마운트만 수행합니다.

import { createApp } from "vue";
import App from "./App.vue";
import "./style.css";

// index.html의 <div id="app"></div> 안에 Vue 컴포넌트 트리를 붙입니다.
createApp(App).mount("#app");
