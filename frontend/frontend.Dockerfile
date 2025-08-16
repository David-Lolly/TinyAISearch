
FROM node:18-alpine AS build-stage

WORKDIR /app

COPY package*.json ./

RUN npm config set registry https://registry.npmmirror.com && npm install

COPY . .

RUN chmod +x ./node_modules/.bin/vite

RUN npm run build


FROM nginx:stable-alpine

COPY --from=build-stage /app/dist /usr/share/nginx/html

COPY spa-nginx.conf /etc/nginx/conf.d/default.conf

# 暴露 80 端口
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
