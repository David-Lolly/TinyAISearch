import axios from 'axios';

// The base URL should be a relative path so that the Vite proxy can catch it.
// All requests to /api/... will be proxied to http://localhost:5000/api/...
const API_BASE_URL = '/backend';
// const API_BASE_URL = '';
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2分钟超时
});



// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.data);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// --- Custom Methods ---

// 获取用户会话列表
api.getSessions = (userId) => {
  return api.get('/sessions', {
    params: { user_id: userId }
  });
};

// 获取指定会话的消息列表
api.getMessages = (sessionId) => {
  return api.get(`/sessions/${sessionId}/messages`);
};

// 创建新会话
api.createSession = (userId, title) => {
  return api.post('/session', {
    user_id: userId,
    title: title
  });
};

// 用户注册
api.register = (userId, password) => {
  return api.post('/register', {
    user_id: userId,
    password: password
  });
};

// 用户登录
api.login = (userId, password) => {
  return api.post('/login', {
    user_id: userId,
    password: password
  });
};

// 流式搜索 - 使用 fetch API 而不是 axios，因为axios对流式响应支持不够好
api.searchStream = async (payload, onChunk, onComplete, onError, signal) => {
  try {
    const response = await fetch(`${API_BASE_URL}/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/x-json-stream',
        'Cache-Control': 'no-cache',
      },
      body: JSON.stringify(payload),
      signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      if (chunk) {
        onChunk && onChunk(chunk);
      }
    }

    onComplete && onComplete();
  } catch (error) {
    onError && onError(error);
  }
};

export default api;