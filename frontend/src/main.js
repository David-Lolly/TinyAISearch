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

  
  // 3. 特殊页面（配置和登录）直接放行，或者识别到来自配置页的信号
  // 检查是否是从配置页保存后跳转过来的
  if (to.name === 'Config' || to.name === 'Login' || to.query.fromConfigSave === 'true' /* 或 to.meta.fromConfigSave */) {
    console.log('[DEBUG] 目标为 Config/Login 页面，或检测到来自配置保存的跳转信号，直接放行。');
    // 如果是从配置页成功保存后跳转，移除这个信号，避免后续刷新或直接访问时误判
    if (to.query.fromConfigSave === 'true' && to.name === 'Chat') {
        const newQuery = { ...to.query };
        delete newQuery.fromConfigSave;
        return next({ path: to.path, query: newQuery, replace: true }); // 使用 replace 避免在历史记录中留下带信号的路由
    }
    return next();
  }

  // 4. 系统配置状态检查 (只针对非登录/配置页面且非配置页跳转)
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
    sessionStorage.clear();
    return next({ name: 'Config' });
  }

  
  return next();
});

const app = createApp(App)
app.use(router)
app.mount('#app')