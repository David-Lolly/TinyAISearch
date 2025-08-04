# ---- 第一阶段：构建阶段 ----
# 使用 Node.js 官方镜像作为构建环境
FROM node:18-alpine AS build-stage

# 设置工作目录
WORKDIR /app

# 复制 package.json 和 package-lock.json
COPY package*.json ./

# 设置 npm 使用国内淘宝镜像源
RUN npm config set registry https://registry.npmmirror.com

# 安装项目依赖
RUN npm install

# 复制所有前端代码到工作目录
COPY . .

# 执行构建命令
RUN npm run build

# ---- 第二阶段：生产阶段 ----
# 使用轻量的 Nginx 镜像作为最终的运行环境
FROM nginx:stable-alpine

# 从构建阶段（build-stage）复制编译好的静态文件到 Nginx 的默认网站根目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制自定义的 Nginx 配置文件（我们稍后会创建它）
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露 80 端口
EXPOSE 80

# Nginx 默认会启动，这里可以用 CMD 保持容器前台运行
CMD ["nginx", "-g", "daemon off;"]
