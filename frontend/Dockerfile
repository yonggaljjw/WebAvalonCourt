# 1단계(build): Node.js 환경에서 Vue/Vite 소스를 정적 파일로 빌드합니다.
FROM node:22-alpine AS build
WORKDIR /app

# package 파일을 먼저 복사해 npm 의존성 레이어 캐시를 활용합니다.
COPY package*.json ./
RUN npm ci

# 소스를 복사하고 /app/dist에 배포용 파일을 생성합니다.
COPY . .
RUN npm run build

# 2단계(runtime): Node.js는 버리고 가벼운 Nginx 이미지만 남깁니다.
# 이런 방식을 멀티 스테이지 빌드라고 합니다.
FROM nginx:1.28-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
