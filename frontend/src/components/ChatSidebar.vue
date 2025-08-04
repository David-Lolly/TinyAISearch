<template>
  <div class="sidebar-container">
    <aside
      class="sidebar-main bg-background-secondary text-text-primary transition-all duration-300 ease-in-out fixed top-0 left-0 h-full z-40 flex flex-col shadow-xl border-r border-neutral-200"
      :class="[
        'w-72',
        isOpen ? 'translate-x-0' : '-translate-x-72'
      ]"
    >
      <div class="sidebar-header p-4 flex-shrink-0">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center space-x-3">
            
            <div>
              <h1 class="text-lg font-bold text-text-primary">TinyAISearch</h1>
              <p class="text-xs text-text-secondary">智能搜索助手</p>
            </div>
          </div>

          <button
            @click="$emit('toggle')"
            class="group p-2 text-text-secondary hover:text-text-primary hover:bg-neutral-200/60 rounded-lg transition-colors duration-200"
            title="收起侧边栏"
          >
            <ChevronLeftIcon class="w-5 h-5" />
          </button>
        </div>

        <button
          @click="$emit('new-chat')"
          class="group w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg font-medium transition-colors duration-200 hover:bg-neutral-200/60 active:bg-neutral-300/80"
        >
          <div class="w-7 h-7 rounded-full flex items-center justify-center text-white" style="background-color: rgb(201, 100, 66);">
            <PlusIcon class="w-4 h-4" />
          </div>
          <span class="font-semibold" style="color: rgb(201, 100, 66);">新建对话</span>
        </button>
      </div>

      <div class="sidebar-sessions flex-1 overflow-y-auto px-4 pb-4 min-h-0 space-y-1">
        <div v-if="sessions.length === 0" class="flex flex-col items-center justify-center py-10 px-4 text-center">
          <div class="w-16 h-16 bg-neutral-200/70 rounded-full flex items-center justify-center mb-4">
            <svg class="w-8 h-8 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
               <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
            </svg>
          </div>
          <p class="text-text-secondary text-sm">开始一次新对话吧</p>
        </div>

        <div v-else class="space-y-1">
          <button
            v-for="session in sessions"
            :key="session.session_id"
            @click="$emit('session-select', session.session_id)"
            class="group w-full text-left px-3 py-2.5 rounded-lg transition-colors duration-200 text-sm"
            :class="[
              currentSessionId === session.session_id
                ? 'bg-neutral-200 text-text-primary'
                : 'text-text-secondary hover:bg-neutral-200/60 hover:text-text-primary'
            ]"
            :title="session.title || '新对话'"
          >
            <p class="font-medium truncate">
              {{ session.title || '新对话' }}
            </p>
          </button>
        </div>
      </div>

      <div class="sidebar-footer border-t border-neutral-200 p-3 flex-shrink-0">
        <div 
          class="flex items-center justify-between p-2 rounded-lg transition-colors duration-200 hover:bg-neutral-200/60 cursor-pointer"
          @click="toggleUserMenu"
          ref="userProfileRef"
        >
          <div class="flex items-center space-x-3 flex-1 min-w-0">
            <div class="w-9 h-9 bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold text-sm shadow-sm">
              {{ userId ? userId.charAt(0).toUpperCase() : 'U' }}
            </div>

            <div class="flex-1 min-w-0">
              <p class="text-sm font-semibold text-text-primary truncate">{{ userId || '匿名用户' }}</p>
            </div>
          </div>

          <button 
            class="p-1 text-text-secondary focus:outline-none"
            @click.stop="toggleUserMenu"
          >
            <ChevronUpIcon v-if="showUserMenu" class="w-5 h-5 text-text-secondary" />
            <ChevronDownIcon v-else class="w-5 h-5 text-text-secondary" />
          </button>
        </div>

        
        <transition
          enter-active-class="transition ease-out duration-100"
          enter-from-class="transform opacity-0 scale-95"
          enter-to-class="transform opacity-100 scale-100"
          leave-active-class="transition ease-in duration-75"
          leave-from-class="transform opacity-100 scale-100"
          leave-to-class="transform opacity-0 scale-95"
        >
          <div v-if="showUserMenu" class="absolute bottom-16 left-3 right-3 bg-white rounded-lg shadow-lg border border-neutral-200 overflow-hidden z-50">
            <div class="py-1">
              <button 
                @click="$emit('edit-config')" 
                class="w-full text-left px-4 py-2 text-sm text-text-primary hover:bg-neutral-100 flex items-center space-x-2"
              >
                <Cog6ToothIcon class="w-5 h-5 text-neutral-500" />
                <span>修改配置</span>
              </button>
              <button 
                @click="$emit('logout')" 
                class="w-full text-left px-4 py-2 text-sm text-red-500 hover:bg-neutral-100 flex items-center space-x-2"
              >
                <ArrowRightOnRectangleIcon class="w-5 h-5" />
                <span>退出登录</span>
              </button>
            </div>
          </div>
        </transition>
      </div>
    </aside>

    <button
      v-if="!isOpen"
      @click="$emit('toggle')"
      class="group fixed top-5 left-5 z-50 p-2.5 bg-background-card text-text-primary rounded-lg shadow-floating border border-neutral-200 hover:scale-105 transition-all duration-300"
      title="展开侧边栏"
    >
      <Bars3Icon class="w-5 h-5" />
    </button>

    <div
      v-if="isOpen"
      @click="$emit('toggle')"
      class="sidebar-overlay fixed inset-0 bg-black/30 backdrop-blur-sm z-30 md:hidden transition-opacity duration-300"
      :class="isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'"
    ></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import {
  Bars3Icon,
  ChevronLeftIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  PlusIcon,
  ArrowRightOnRectangleIcon,
  Cog6ToothIcon
} from '@heroicons/vue/24/outline'


defineProps({
  isOpen: { type: Boolean, default: true },
  sessions: { type: Array, default: () => [] },
  currentSessionId: { type: String, default: null },
  userId: { type: String, required: true }
})

defineEmits(['toggle', 'new-chat', 'session-select', 'logout', 'edit-config'])

const showUserMenu = ref(false);
const userProfileRef = ref(null);
const justOpened = ref(false);

const toggleUserMenu = () => {
  if (!showUserMenu.value) {
    
    showUserMenu.value = true;
    justOpened.value = true;
    
    nextTick(() => {
      
      setTimeout(() => {
        justOpened.value = false;
      }, 0);
    });
  } else {
    
    showUserMenu.value = false;
  }
};


const handleClickOutside = (event) => {
  if (justOpened.value) return; 
  if (userProfileRef.value && !userProfileRef.value.contains(event.target)) {
    showUserMenu.value = false;
  }
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style scoped>



.sidebar-sessions {
  scrollbar-width: thin;
  scrollbar-color: #d4d4d4 #f5f5f5; 
}

.sidebar-sessions::-webkit-scrollbar {
  width: 6px;
}

.sidebar-sessions::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-sessions::-webkit-scrollbar-thumb {
  background-color: #d4d4d4; 
  border-radius: 10px;
}

.sidebar-sessions::-webkit-scrollbar-thumb:hover {
  background-color: #a3a3a3; 
}


.sidebar-main {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar-overlay {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>