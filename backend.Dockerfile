FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --timeout 60 --retries 3 -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

COPY . .

EXPOSE 8000


CMD ["uvicorn", "AISearchServer:app", "--host", "0.0.0.0", "--port", "8000"]
