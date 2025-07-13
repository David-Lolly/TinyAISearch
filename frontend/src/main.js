import { createApp } from 'vue'
import './style.css' 
import App from './App.vue'
import { createRouter, createWebHistory } from 'vue-router'
import ChatView from './views/ChatView.vue'
import ConfigView from './views/ConfigView.vue'
import LoginView from './views/LoginView.vue'
import api from './services/api'

const routes = [
  { path: '/', name: 'Chat', component: ChatView },
  { path: '/login', name: 'Login', component: LoginView },
  { path: '/config', name: 'Config', component: ConfigView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})








router.beforeEach(async (to, from, next) => {
  const userId = sessionStorage.getItem('userId');

  
  console.log(`[DEBUG] Navigating from '${from.fullPath}' to '${to.fullPath}'. userId=${userId}`);

  
  if (!userId && to.name !== 'Login') {
    console.log('[DEBUG] 未检测到 userId，跳转至 Login');
    return next({ name: 'Login' });
  }

  
  if (userId && to.name === 'Login') {
    return next({ name: 'Chat' });
  }

  
  
  if (to.name === 'Config' || to.name === 'Login') {
    return next();
  }

  try {
    const response = await api.get('/api/status');
    const configured = response.data?.configured;
    console.log(`[DEBUG] /api/status configured=${configured}`);
    if (!configured) {
      console.log('[DEBUG] 系统未配置，跳转至 Config');
      return next({ name: 'Config' });
    }
  } catch (error) {
    console.error('[DEBUG] 获取 /api/status 失败，假定未配置', error);
    return next({ name: 'Config' });
  }

  
  return next();
});

const app = createApp(App)
app.use(router)
app.mount('#app')