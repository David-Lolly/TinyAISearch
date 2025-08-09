
# ---- 第一阶段：构建阶段 ----
FROM node:18-alpine AS build-stage

WORKDIR /app

# 复制依赖文件以利用缓存
COPY package*.json ./

# 设置npm使用国内镜像并安装依赖
RUN npm config set registry https://registry.npmmirror.com && npm install

# 复制所有前端代码
COPY . .

# 修复执行权限问题
RUN chmod +x ./node_modules/.bin/vite

# 执行构建命令
RUN npm run build

# ---- 第二阶段：生产阶段 ----
# 使用轻量的 Nginx 镜像作为最终的运行环境
FROM nginx:stable-alpine

# 从构建阶段（build-stage）复制编译好的静态文件到 Nginx 的默认网站根目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制自定义的 Nginx 配置文件，支持SPA路由
COPY spa-nginx.conf /etc/nginx/conf.d/default.conf

# 暴露 80 端口
EXPOSE 80

# Nginx 默认会启动，这里可以用 CMD 保持容器前台运行
CMD ["nginx", "-g", "daemon off;"]
