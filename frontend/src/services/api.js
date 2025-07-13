import axios from 'axios';

// The base URL should be a relative path so that the Vite proxy can catch it.
// All requests to /api/... will be proxied to http://localhost:5000/api/...
const API_BASE_URL = '';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2分钟超时
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url, config.data);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

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
api.searchStream = async (payload, onChunk, onComplete, onError) => {
  try {
    const response = await fetch(`${API_BASE_URL}/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
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
        onChunk(chunk);
      }
    }

    onComplete();
  } catch (error) {
    console.error('Stream search error:', error);
    onError(error);
  }
};

export default api;