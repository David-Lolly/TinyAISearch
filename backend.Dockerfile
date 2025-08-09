# 使用官方的 Python 3.10 slim 镜像作为基础
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 更换 pip 镜像源为阿里云源（更稳定），增加超时时间和重试次数
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
RUN pip config set global.timeout 300
RUN pip config set global.retries 5

# 复制依赖文件并安装
# 单独复制 requirements.txt 是为了利用Docker的层缓存机制
# 只有当 requirements.txt 文件改变时，才会重新执行 pip install
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 300 --retries 5 -r requirements.txt

# 复制项目所有文件到工作目录
COPY . .

# 声明服务运行的端口（需要和您应用实际监听的端口一致）
# 假设您的 AISearchServer.py 监听 8000 端口
EXPOSE 8000

# 容器启动时执行的命令
# 这里使用 uvicorn 启动，请根据您的项目实际情况修改
# 例如 gunicorn -w 4 -k uvicorn.workers.UvicornWorker AISearchServer:app -b 0.0.0.0:8000
CMD ["uvicorn", "AISearchServer:app", "--host", "0.0.0.0", "--port", "8000"]
