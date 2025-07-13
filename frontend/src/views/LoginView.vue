<template>
  <div class="min-h-screen flex flex-col justify-center items-center bg-background-main">
    
    <div class="login-card relative backdrop-blur-md bg-white/70 p-8 rounded-2xl shadow-floating border border-white/50 w-full max-w-sm overflow-hidden">
      
      <transition 
        name="fade" 
        mode="out-in"
        enter-active-class="transition ease-out duration-100" 
        leave-active-class="transition ease-in duration-75"
        enter-from-class="opacity-0 transform -translate-y-2" 
        enter-to-class="opacity-100 transform translate-y-0"
        leave-from-class="opacity-100 transform translate-y-0" 
        leave-to-class="opacity-0 transform -translate-y-2"
      >
        <h2 :key="isRegisterMode ? 'register' : 'login'" class="text-3xl font-bold mb-6 text-center text-text-primary">
          {{ isRegisterMode ? '注册' : '登录' }}
        </h2>
      </transition>
      
      
      <form @submit.prevent="handleSubmit" class="space-y-6">
        
        <div class="relative">
          <label class="block text-sm font-medium text-text-secondary mb-1.5 ml-1">用户名</label>
          <div class="relative">
            <input 
              v-model="username" 
              type="text" 
              required 
              placeholder="请输入用户名" 
              class="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl text-text-primary placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-button-active/30 focus:border-button-active transition-colors duration-100"
              @focus="focusField('username')"
            />
            <div class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
              </svg>
            </div>
          </div>
        </div>
        
        
        <div class="relative">
          <label class="block text-sm font-medium text-text-secondary mb-1.5 ml-1">密码</label>
          <div class="relative">
            <input 
              v-model="password"
              :type="showPassword ? 'text' : 'password'" 
              required
              placeholder="请输入密码" 
              class="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl text-text-primary placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-button-active/30 focus:border-button-active transition-colors duration-100"
              @focus="focusField('password')"
            />
            <div 
              class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 cursor-pointer p-2 -mr-2"
              @click="togglePasswordVisibility"
            >
              <svg v-if="!showPassword" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10 2a5 5 0 00-5 5v2a2 2 0 00-2 2v5a2 2 0 002 2h10a2 2 0 002-2v-5a2 2 0 00-2-2H7V7a3 3 0 015.905-.75 1 1 0 001.937-.5A5.002 5.002 0 0010 2z" />
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 12a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd" />
                <path fill-rule="evenodd" d="M10 3c-4.97 0-9 3.582-9 8s4.03 8 9 8 9-3.582 9-8-4.03-8-9-8zm0 2c3.866 0 7 2.686 7 6s-3.134 6-7 6-7-2.686-7-6 3.134-6 7-6z" clip-rule="evenodd" />
              </svg>
            </div>
          </div>
        </div>
        
        
        <transition 
          name="fade" 
          enter-active-class="transition-all duration-150 ease-out" 
          leave-active-class="transition-all duration-100 ease-in"
          enter-from-class="opacity-0 transform -translate-y-2" 
          enter-to-class="opacity-100 transform translate-y-0"
          leave-from-class="opacity-100 transform translate-y-0" 
          leave-to-class="opacity-0 transform -translate-y-2"
        >
          <div v-if="!isRegisterMode" class="flex items-center justify-between">
            <div class="flex items-center">
              <input 
                type="checkbox" 
                id="remember-me" 
                v-model="rememberMe"
                class="w-4 h-4 text-button-active border-gray-300 rounded focus:ring-button-active cursor-pointer"
              />
              <label for="remember-me" class="ml-2 block text-sm text-text-secondary cursor-pointer select-none">
                记住我
              </label>
            </div>
            <button type="button" class="text-sm text-button-active hover:text-red-700 hover:underline transition-colors duration-100 focus:outline-none">
              忘记密码?
            </button>
          </div>
        </transition>
        
        
        <transition 
          name="fade" 
          enter-active-class="transition-all duration-150 ease-out" 
          leave-active-class="transition-all duration-100 ease-in"
          enter-from-class="opacity-0 transform scale-95" 
          enter-to-class="opacity-100 transform scale-100"
          leave-from-class="opacity-100 transform scale-100" 
          leave-to-class="opacity-0 transform scale-95"
        >
          <div v-if="errorMessage" 
              :class="[
                'text-sm text-center px-3 py-2 rounded-md animate-pulse-once',
                isSuccessMessage ? 'text-green-700 bg-green-50 border border-green-200' : 'text-red-600 bg-red-50 border border-red-200'
              ]">
            {{ errorMessage }}
          </div>
        </transition>
        
        
        <button 
          type="submit" 
          class="w-full flex justify-center items-center px-4 py-3 bg-button-active hover:bg-red-600 text-white rounded-xl font-medium shadow-md hover:shadow-lg active:shadow-sm transform transition duration-100 ease-in-out hover:scale-[1.01] active:scale-[0.99] focus:outline-none"
          :disabled="!canSubmit"
          :class="[{'opacity-90 cursor-not-allowed': !canSubmit}]"
        >
          <span v-if="isLoading" class="flex items-center">
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            处理中...
          </span>
          <span v-else>{{ isRegisterMode ? '注册' : '登录' }}</span>
        </button>
      </form>
      
      
      <div class="mt-6 text-center text-sm">
        <span class="text-text-secondary">{{ isRegisterMode ? '已有账号?' : '还没有账号?' }} </span>
        <button 
          @click="toggleMode" 
          @mousedown="handleButtonPress"
          @mouseup="handleButtonRelease"
          @touchstart="handleButtonPress"
          @touchend="handleButtonRelease"
          class="text-button-active hover:text-red-700 hover:underline font-medium bg-transparent p-1 -m-1 border-none inline-flex items-center focus:outline-none rounded transition-all duration-75"
          :class="{'transform scale-95': isButtonPressed}"
        >
          {{ isRegisterMode ? '登录' : '注册' }}
        </button>
      </div>
      
      
      <div class="absolute -top-10 -left-10 w-40 h-40 bg-pink-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
      <div class="absolute top-0 -right-4 w-32 h-32 bg-yellow-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
      <div class="absolute -bottom-8 left-20 w-36 h-36 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import api from '../services/api';

const username = ref('');
const password = ref('');
const errorMessage = ref('');
const isRegisterMode = ref(false);
const router = useRouter();
const isLoading = ref(false);
const showPassword = ref(false);
const rememberMe = ref(false);
const isSuccessMessage = ref(false);
const isButtonPressed = ref(false); 

const canSubmit = computed(() => {
  return !isLoading.value && username.value.trim() !== '' && password.value.trim() !== '';
});


watch([username, password], () => {
  if (errorMessage.value && !isLoading.value) {
    errorMessage.value = '';
  }
});

function togglePasswordVisibility() {
  showPassword.value = !showPassword.value;
}

function toggleMode() {
  isRegisterMode.value = !isRegisterMode.value;
  errorMessage.value = '';
}

function focusField(field) {
  
  
  
}

function handleButtonPress() {
  isButtonPressed.value = true;
}

function handleButtonRelease() {
  isButtonPressed.value = false;
}

async function handleSubmit() {
  errorMessage.value = '';
  isSuccessMessage.value = false;
  
  if (!username.value || !password.value) {
    errorMessage.value = '请输入邮箱和密码';
    return;
  }
  
  isLoading.value = true;
  
  try {
    if (isRegisterMode.value) {
      
      await api.register(username.value, password.value);
      
      
      isRegisterMode.value = false;
      isSuccessMessage.value = true;
      errorMessage.value = '注册成功，请点击登录按钮进行登录';
      
      
      setTimeout(() => {
        if (errorMessage.value === '注册成功，请点击登录按钮进行登录') {
          errorMessage.value = '';
        }
      }, 3000);
      
    } else {
      
      const response = await api.login(username.value, password.value);
      sessionStorage.setItem('userId', username.value);
      
      
      if (rememberMe.value) {
        localStorage.setItem('rememberedUser', username.value);
      }

      
      try {
        const statusResp = await api.get('/api/status');
        const configured = statusResp.data?.configured;
        console.log(`[DEBUG] After login, configured=${configured}`);
        router.push(configured ? '/' : '/config');
      } catch (e) {
        console.warn('[DEBUG] 登录后检查 /api/status 失败，跳转 Config', e);
        router.push('/config');
      }
    }
  } catch (error) {
    console.error('Authentication error:', error);
    
    
    const errorDetail = error.response?.data?.detail || '';
    
    if (isRegisterMode.value) {
      if (error.response?.status === 409) {
        errorMessage.value = '注册失败，该账号已存在';
      } else {
        errorMessage.value = `注册失败: ${errorDetail || '请稍后重试'}`;
      }
    } else {
      if (error.response?.status === 401) {
        errorMessage.value = '登录失败，账号不存在或密码错误';
      } else {
        errorMessage.value = `登录失败: ${errorDetail || '请稍后重试'}`;
      }
    }
  } finally {
    isLoading.value = false;
  }
}


if (localStorage.getItem('rememberedUser')) {
  username.value = localStorage.getItem('rememberedUser');
  rememberMe.value = true;
}
</script>

<style scoped>

@keyframes blob {
  0% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -50px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.9); }
  100% { transform: translate(0, 0) scale(1); }
}

.animate-blob {
  animation: blob 7s infinite;
}

.animation-delay-2000 {
  animation-delay: 2s;
}

.animation-delay-4000 {
  animation-delay: 4s;
}

@keyframes pulse-once {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

.animate-pulse-once {
  animation: pulse-once 2s ease-in-out;
}
</style>