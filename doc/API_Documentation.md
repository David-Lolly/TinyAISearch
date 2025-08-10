# TinyAISearch 后端 API 文档

## 概述

TinyAISearch 是一个基于 AI 的智能搜索系统，本文档详细描述了后端 API 的使用方法。

**基础信息**
- 基础 URL: `http://localhost:5000`
- 支持的内容类型: `application/json`
- 响应格式: JSON
- 认证方式: 会话认证

---

## 目录

1. [系统配置 API](#系统配置-api)
2. [连接测试 API](#连接测试-api)
3. [搜索相关 API](#搜索相关-api)
4. [会话管理 API](#会话管理-api)
5. [用户认证 API](#用户认证-api)
6. [数据模型](#数据模型)
7. [错误码说明](#错误码说明)

---

## 系统配置 API

### 获取系统配置状态

获取系统当前的配置状态，用于判断系统是否已完成初始化配置。

**请求信息**
```
GET /api/status
```

**请求参数**
无

**响应参数**
| 字段名 | 类型 | 说明 |
|--------|------|------|
| configured | boolean | 系统是否已配置完成 |

**示例**

请求：
```bash
curl -X GET http://localhost:5000/api/status
```

响应：
```json
{
  "configured": true
}
```

---

### 获取系统设置

获取系统的详细配置信息。

**请求信息**
```
GET /api/settings
```

**请求参数**
无

**响应参数**
返回系统所有配置项的键值对。

**示例**

请求：
```bash
curl -X GET http://localhost:5000/api/settings
```

响应：
```json
{
  "llm_model": "gpt-3.5-turbo",
  "llm_base_url": "https://api.openai.com/v1/chat/completions",
  "llm_api_key": "sk-***",
  "embedding_model": "text-embedding-ada-002",
  "embedding_base_url": "https://api.openai.com/v1/embeddings",
  "retrieval_version": "v2"
}
```

---

### 保存系统设置

保存或更新系统配置信息。

**请求信息**
```
POST /api/settings
```

**请求参数**
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| settings | object | 是 | 配置项对象 |

**请求体示例**
```json
{
  "settings": {
    "llm_model": "gpt-4",
    "llm_base_url": "https://api.openai.com/v1/chat/completions",
    "llm_api_key": "sk-your-api-key",
    "embedding_model": "text-embedding-ada-002",
    "embedding_base_url": "https://api.openai.com/v1/embeddings",
    "embedding_api_key": "sk-your-api-key",
    "rerank_model": "bge-reranker-large",
    "rerank_base_url": "http://localhost:8001/rerank",
    "rerank_api_key": "your-rerank-key",
    "google_api_key": "your-google-api-key",
    "google_cse_id": "your-cse-id",
    "retrieval_version": "v2"
  }
}
```

**响应参数**
| 字段名 | 类型 | 说明 |
|--------|------|------|
| status | string | 操作状态 (success/error) |
| message | string | 操作结果消息 |
| configured | boolean | 保存后系统是否配置完成 |

**示例**

响应：
```json
{
  "status": "success",
  "message": "设置保存成功。",
  "configured": true
}
```

---

## 连接测试 API

### 测试 LLM 连接

测试大语言模型的连接是否正常。

**请求信息**
```
POST /api/test/llm
```

**请求参数**
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model_name | string | 是 | 模型名称 |
| base_url | string | 是 | API 基础 URL |
| api_key | string | 是 | API 密钥 |

**请求体示例**
```json
{
  "model_name": "gpt-3.5-turbo",
  "base_url": "https://api.openai.com/v1/chat/completions",
  "api_key": "sk-your-api-key"
}
```

**响应参数**
| 字段名 | 类型 | 说明 |
|--------|------|------|
| success | boolean | 连接是否成功 |
| message | string | 连接结果消息 |

**示例**

成功响应：
```json
{
  "success": true,
  "message": "LLM连接成功"
}
```

失败响应：
```json
{
  "success": false,
  "message": "连接失败: Invalid API key"
}
```

---

### 测试 Embedding 模型连接

测试词嵌入模型的连接是否正常。

**请求信息**
```
POST /api/test/embedding
```

**请求参数**
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model_name | string | 是 | 模型名称 |
| base_url | string | 是 | API 基础 URL |
| api_key | string | 是 | API 密钥 |

**示例**

请求：
```json
{
  "model_name": "text-embedding-ada-002",
  "base_url": "https://api.openai.com/v1/embeddings",
  "api_key": "sk-your-api-key"
}
```

响应：
```json
{
  "success": true,
  "message": "Embedding模型连接成功"
}
```

---

### 测试 Rerank 模型连接

测试重排序模型的连接是否正常。

**请求信息**
```
POST /api/test/rerank
```

**请求参数**
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model_name | string | 是 | 模型名称 |
| base_url | string | 是 | API 基础 URL |
| api_key | string | 是 | API 密钥 |

**示例**

请求：
```json
{
  "model_name": "bge-reranker-large",
  "base_url": "http://localhost:8001/rerank",
  "api_key": "your-rerank-key"
}
```

响应：
```json
{
  "success": true,
  "message": "Rerank模型连接成功"
}
```

---

### 测试 Google Search 连接

测试 Google 自定义搜索的连接是否正常。

**请求信息**
```
POST /api/test/google
```

**请求参数**
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| api_key | string | 是 | Google API 密钥 |
| cse_id | string | 是 | 自定义搜索引擎 ID |

**示例**

请求：
```json
{
  "api_key": "your-google-api-key",
  "cse_id": "your-cse-id"
}
```

响应：
```json
{
  "success": true,
  "message": "Google Search连接成功"
}
```

---

## 搜索相关 API

### 执行搜索

执行 AI 增强的搜索查询，支持流式响应。

**请求信息**
```
POST /search
```

**请求参数**
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| query | string | 是 | 搜索查询内容 |
| user_id | string | 是 | 用户 ID |
| session_id | string | 否 | 会话 ID，不提供则创建新会话 |
| use_web | boolean | 否 | 是否使用网络搜索，默认 true |

**请求体示例**
```json
{
  "query": "什么是量子计算？",
  "user_id": "user123",
  "session_id": "session456",
  "use_web": true
}
```

**响应格式**
流式响应，Content-Type: `application/x-json-stream`

每行包含一个 JSON 对象：

**流式响应类型**
| 类型 | 说明 | payload 内容 |
|------|------|---------------|
| process | 处理进度信息 | string: 进度描述 |
| answer_chunk | 答案片段 | string: 文本片段 |
| reference | 参考来源 | array: 引用链接列表 |
| error | 错误信息 | string: 错误描述 |

**示例**

请求：
```bash
curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是量子计算？",
    "user_id": "user123",
    "use_web": true
  }'
```

流式响应：
```json
{"type": "process", "payload": "正在分析问题..."}
{"type": "process", "payload": "搜索关键词: ['量子计算', '量子比特']"}
{"type": "process", "payload": "搜索完成. 找到 15 个网页."}
{"type": "answer_chunk", "payload": "量子计算是一种"}
{"type": "answer_chunk", "payload": "利用量子力学现象"}
{"type": "answer_chunk", "payload": "进行信息处理的技术..."}
{"type": "reference", "payload": [{"百度百科": "https://baike.baidu.com/item/量子计算"}]}
```

---

## 会话管理 API

### 获取用户会话列表

获取指定用户的所有会话列表。

**请求信息**
```
GET /sessions?user_id={user_id}
```

**请求参数**
| 字段名 | 类型 | 必填 | 位置 | 说明 |
|--------|------|------|------|------|
| user_id | string | 是 | query | 用户 ID |

**响应参数**
返回会话对象数组：
| 字段名 | 类型 | 说明 |
|--------|------|------|
| session_id | string | 会话 ID |
| title | string | 会话标题 |
| created_at | string | 创建时间 |

**示例**

请求：
```bash
curl -X GET "http://localhost:5000/sessions?user_id=user123"
```

响应：
```json
[
  {
    "session_id": "session456",
    "title": "量子计算相关问题",
    "created_at": "2024-01-15 10:30:00"
  },
  {
    "session_id": "session789",
    "title": "人工智能发展",
    "created_at": "2024-01-14 15:20:00"
  }
]
```

---

### 获取会话消息

获取指定会话的所有消息记录。

**请求信息**
```
GET /sessions/{session_id}/messages
```

**路径参数**
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| session_id | string | 是 | 会话 ID |

**响应参数**
返回消息对象数组：
| 字段名 | 类型 | 说明 |
|--------|------|------|
| role | string | 消息角色 (user/assistant) |
| content | string | 消息内容 |
| timestamp | string | 消息时间戳 |

**示例**

请求：
```bash
curl -X GET http://localhost:5000/sessions/session456/messages
```

响应：
```json
[
  {
    "role": "user",
    "content": "什么是量子计算？",
    "timestamp": "2024-01-15 10:31:00"
  },
  {
    "role": "assistant",
    "content": "{\"text\": \"量子计算是一种利用量子力学现象...\", \"references\": [...]}",
    "timestamp": "2024-01-15 10:31:30"
  }
]
```

---

### 创建新会话

为用户创建一个新的对话会话。

**请求信息**
```
POST /session
```

**请求参数**
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_id | string | 是 | 用户 ID |
| title | string | 否 | 会话标题，不提供则自动生成 |

**请求体示例**
```json
{
  "user_id": "user123",
  "title": "新的对话会话"
}
```

**响应参数**
| 字段名 | 类型 | 说明 |
|--------|------|------|
| session_id | string | 创建的会话 ID |
| title | string | 会话标题 |

**示例**

响应：
```json
{
  "session_id": "session101112",
  "title": "新的对话会话"
}
```

---

## 用户认证 API

### 用户登录

验证用户凭据并建立会话。

**请求信息**
```
POST /login
```

**请求参数**
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_id | string | 是 | 用户 ID |
| password | string | 是 | 用户密码 |

**请求体示例**
```json
{
  "user_id": "user123",
  "password": "your_password"
}
```

**响应参数**
| 字段名 | 类型 | 说明 |
|--------|------|------|
| message | string | 登录结果消息 |
| user_id | string | 用户 ID |

**示例**

成功响应：
```json
{
  "message": "登录成功",
  "user_id": "user123"
}
```

---

### 用户注册

注册新用户账户。

**请求信息**
```
POST /register
```

**请求参数**
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_id | string | 是 | 用户 ID |
| password | string | 是 | 用户密码 |

**请求体示例**
```json
{
  "user_id": "newuser456",
  "password": "secure_password"
}
```

**响应参数**
| 字段名 | 类型 | 说明 |
|--------|------|------|
| message | string | 注册结果消息 |
| user_id | string | 用户 ID |

**示例**

成功响应：
```json
{
  "message": "注册成功",
  "user_id": "newuser456"
}
```

---

## 数据模型

### SearchRequest
```typescript
interface SearchRequest {
  query: string;           // 搜索查询内容
  user_id: string;         // 用户 ID
  session_id?: string;     // 会话 ID (可选)
  use_web?: boolean;       // 是否使用网络搜索 (默认 true)
}
```

### SessionRequest
```typescript
interface SessionRequest {
  user_id: string;         // 用户 ID
  title?: string;          // 会话标题 (可选)
}
```

### LoginRequest
```typescript
interface LoginRequest {
  user_id: string;         // 用户 ID
  password: string;        // 用户密码
}
```

### RegisterRequest
```typescript
interface RegisterRequest {
  user_id: string;         // 用户 ID
  password: string;        // 用户密码
}
```

### TestRequest
```typescript
interface TestRequest {
  model_name?: string;     // 模型名称
  base_url?: string;       // API 基础 URL
  api_key?: string;        // API 密钥
  cse_id?: string;         // Google 自定义搜索引擎 ID
}
```

---

## 错误码说明

### HTTP 状态码

| 状态码 | 说明 | 常见情况 |
|--------|------|----------|
| 200 | 请求成功 | 正常响应 |
| 201 | 创建成功 | 成功创建会话 |
| 400 | 请求错误 | 参数缺失或格式错误 |
| 401 | 认证失败 | 用户名或密码错误 |
| 409 | 冲突 | 用户已存在 |
| 500 | 服务器错误 | 内部服务错误 |

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误示例

**400 Bad Request**
```json
{
  "detail": "用户ID和密码为必填项"
}
```

**401 Unauthorized**
```json
{
  "detail": "无效的凭据或用户不存在"
}
```

**409 Conflict**
```json
{
  "detail": "用户已存在"
}
```

**500 Internal Server Error**
```json
{
  "detail": "注册用户失败"
}
```

---

## 使用示例

### 完整的搜索流程

```javascript
// 1. 用户登录
const loginResponse = await fetch('http://localhost:5000/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user123',
    password: 'password123'
  })
});

// 2. 创建新会话
const sessionResponse = await fetch('http://localhost:5000/session', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user123',
    title: '关于AI的讨论'
  })
});
const { session_id } = await sessionResponse.json();

// 3. 执行搜索
const searchResponse = await fetch('http://localhost:5000/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: '人工智能的发展历史',
    user_id: 'user123',
    session_id: session_id,
    use_web: true
  })
});

// 4. 处理流式响应
const reader = searchResponse.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value, { stream: true });
  const lines = chunk.split('\n').filter(line => line.trim());
  
  for (const line of lines) {
    try {
      const data = JSON.parse(line);
      switch (data.type) {
        case 'process':
          console.log('进度:', data.payload);
          break;
        case 'answer_chunk':
          console.log('答案片段:', data.payload);
          break;
        case 'reference':
          console.log('参考来源:', data.payload);
          break;
        case 'error':
          console.error('错误:', data.payload);
          break;
      }
    } catch (e) {
      console.warn('解析响应失败:', e);
    }
  }
}
```

---

## 注意事项

1. **系统配置**: 在使用搜索功能前，请确保系统已通过 `/api/settings` 完成配置。

2. **流式响应**: `/search` 接口使用流式响应，需要按行解析 JSON 数据。

3. **会话管理**: 建议为每个用户对话创建独立会话，以便更好地管理对话历史。

4. **错误处理**: 请妥善处理各种 HTTP 状态码和错误响应。

5. **API 限制**: 部分功能依赖外部服务（如 OpenAI、Google Search），请确保相关服务配置正确。

---

*文档版本: v1.0*  
*最后更新: 2024-01-15* 