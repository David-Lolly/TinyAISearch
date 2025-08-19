<template>
  <div class="flex w-full h-full bg-background-main">
    <ChatSidebar
      :sessions="sessions"
      :current-session-id="currentSessionId"
      :user-id="userId"
      :is-open="isSidebarOpen"
      @toggle="toggleSidebar"
      @new-chat="createNewSession"
      @session-select="selectSession"
      @logout="handleLogout" 
      @edit-config="navigateToConfig" />

    <main class="relative flex-1 flex flex-col transition-all duration-300 ease-in-out"
          :style="{
            marginLeft: isSidebarOpen ? '288px' : '0px'
          }">

      <div class="flex-1 overflow-y-auto px-6 pt-4" ref="messagesContainer">
        <div v-if="!currentSessionId" class="flex items-center justify-center h-full">
          <div class="text-center max-w-md animate-fade-in">
            <img src="@/assets/TinyAISearchLOGO.jpg" alt="TinyAISearch Logo" class="w-20 h-20 rounded-2xl mx-auto mb-6 shadow-floating">
            <h1 class="text-4xl font-bold mb-3 text-text-primary">TinyAISearch</h1>
            <p class="text-text-secondary text-lg leading-relaxed">
              智能搜索助手，随时为您答疑解惑<br>
              <span class="text-sm opacity-75">输入内容，开始你的第一次对话吧！</span>
            </p>
          </div>
        </div>

        <div v-else class="max-w-4xl mx-auto pb-40">
          <ChatMessage
            v-for="(msg, index) in messages"
            :key="index"
            :message="msg"
            :user-id="userId"
            :is-streaming="index === messages.length - 1 && isLoading"
            :search-steps="index === messages.length - 1 ? currentSearchSteps : []"
            class="mb-2 animate-slide-in"
            />
        </div>
      </div>

      
      <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-background-main via-background-main to-transparent pt-4 pb-4 px-6">
        <div class="max-w-4xl mx-auto">
          <div class="bg-background-card rounded-xl shadow-input-card border border-gray-100 overflow-hidden">

            <div class="px-4 pt-3 pb-2 border-b border-gray-50">
              <div class="flex items-center space-x-3">
                <button
                  type="button"
                  @click="useWeb = !useWeb"
                  class="flex items-center space-x-2 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all duration-200"
                  :class="{
                    'bg-function-selected text-blue-500 hover:bg-blue-200': useWeb,
                    'text-text-secondary hover:text-text-primary hover:bg-gray-100': !useWeb
                  }"
                >
                  <GlobeAltIcon class="w-3.5 h-3.5" />
                  <span>联网搜索</span>
                </button>

                <button
                  type="button"
                  class="flex items-center space-x-2 px-2.5 py-1.5 rounded-lg text-xs font-medium text-text-secondary hover:text-text-primary hover:bg-gray-50 transition-all duration-200"
                >
                  <DocumentPlusIcon class="w-3.5 h-3.5" />
                  <span>上传文件</span>
                </button>

                <button
                  type="button"
                  class="flex items-center space-x-2 px-2.5 py-1.5 rounded-lg text-xs font-medium text-text-secondary hover:text-text-primary hover:bg-gray-50 transition-all duration-200"
                >
                  <PhotoIcon class="w-3.5 h-3.5" />
                  <span>上传图片</span>
                </button>
              </div>
            </div>

            <form @submit.prevent="sendMessage" class="relative flex items-end p-4">
              <div class="flex-1 relative">
                <textarea
                  v-model="userInput"
                  @input="autoGrowTextarea"
                  @keydown.enter="handleEnter"
                  ref="textareaRef"
                  :disabled="isLoading"
                  class="w-full resize-none border-none outline-none bg-transparent text-text-primary placeholder-text-secondary text-sm leading-relaxed max-h-20"
                  rows="1"
                  placeholder="输入你的问题..."
                ></textarea>

                <div class="absolute bottom-0 left-0 right-12 h-0.5 bg-gradient-to-r from-transparent via-gray-200 to-transparent opacity-30"></div>
              </div>

              
              <button
                :type="isLoading ? 'button' : 'submit'"
                @click="isLoading ? handleStop() : null"
                :disabled="!isLoading && !userInput.trim()"
                class="ml-3 flex-shrink-0 w-8 h-8 rounded-lg font-semibold transition-all duration-200 hover:scale-105 active:scale-95 relative flex items-center justify-center"
                :class="[
                  isLoading
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : (!userInput.trim() ? 'bg-button-disabled text-white cursor-not-allowed' : 'bg-button-active hover:bg-red-600 text-white shadow-lg hover:shadow-xl')
                ]"
              >
                  
                  <svg v-if="isLoading" class="w-3 h-3" viewBox="0 0 12 12" fill="currentColor">
                      <rect width="12" height="12" rx="1.5" />
                  </svg>
                  
                  <ArrowUpIcon v-else class="w-4 h-4" />
              </button>
            </form>
          </div>

          <div class="text-center mt-3">
            <p class="text-xs text-text-secondary">
              TinyAISearch 可能会出错，请核实重要信息。
              <button class="text-blue-600 hover:text-blue-700 underline transition-colors duration-200">
                了解更多
              </button>
            </p>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue';
import api from '@/services/api';
import ChatSidebar from '@/components/ChatSidebar.vue';
import ChatMessage from '@/components/ChatMessage.vue';
import IconSpinner from '@/components/IconSpinner.vue';
import {
  GlobeAltIcon,
  ArrowUpIcon,
  Bars3Icon,
  DocumentPlusIcon,
  PhotoIcon
} from '@heroicons/vue/24/outline';
import { useRouter } from 'vue-router';


const userId = sessionStorage.getItem('userId') || '';

defineEmits(['logout']);

const sessions = ref([]);
const currentSessionId = ref(null);
const messages = ref([]);
const userInput = ref('');
const useWeb = ref(false);
const isLoading = ref(false);
const isSidebarOpen = ref(true);
const currentSearchSteps = ref([]);
const messagesContainer = ref(null);
const textareaRef = ref(null);

const router = useRouter();


const abortController = ref(null);

const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value;
};

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  });
};

const autoGrowTextarea = () => {
  nextTick(() => {
    const textarea = textareaRef.value;
    if (textarea) {
      textarea.style.height = 'auto';
      const maxHeight = 80;
      if (textarea.scrollHeight <= maxHeight) {
        textarea.style.height = `${textarea.scrollHeight}px`;
      } else {
        textarea.style.height = `${maxHeight}px`;
      }
    }
  });
};

const fetchMessages = async (sessionId) => {
  try {
    const response = await api.getMessages(sessionId);
    messages.value = response.data.map(m => {
      if (m.role !== 'assistant') return m;
      try {
        let content = typeof m.content === 'string' ? JSON.parse(m.content) : m.content;
        if (typeof content.text === 'string') {
          try {
            const nestedContent = JSON.parse(content.text);
            if (typeof nestedContent.text !== 'undefined') content = nestedContent;
          } catch (e) {  }
        }
        return { role: 'assistant', content: content.text || '', references: content.references || [] };
      } catch (e) {
        return { role: 'assistant', content: String(m.content), references: [] };
      }
    });
    scrollToBottom();
  } catch (error) {
    console.error("加载消息时出错:", error);
    messages.value = [{ role: 'assistant', content: '加载历史消息失败。' }];
  }
};

const selectSession = async (sessionId) => {
  if (isLoading.value || currentSessionId.value === sessionId) return;
  currentSessionId.value = sessionId;
  messages.value = [];
  isLoading.value = true;
  await fetchMessages(sessionId);
  isLoading.value = false;
  try {
    await fetchMessages(sessionId);
  } finally {
    isLoading.value = false;
  }
};

const fetchSessions = async () => {
  try {
    const response = await api.getSessions(userId);
    sessions.value = response.data;
    if (sessions.value.length > 0 && !currentSessionId.value) {
      await selectSession(sessions.value[0].session_id);
    }
  } catch (error) {
    console.error("加载会话列表时出错:", error);
  }
};

const createNewSession = async () => {
  if (isLoading.value) return;
  currentSessionId.value = null;
  useWeb.value = false
  messages.value = [];
  nextTick(() => textareaRef.value?.focus());
};

const handleStop = () => {
  if (abortController.value) {
    abortController.value.abort();
    abortController.value = null;
  }
};

const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return;

  let sessionIdToUse = currentSessionId.value;

  if (!sessionIdToUse) {
    try {
      const title = userInput.value.trim().substring(0, 10);
      const response = await api.createSession(userId, title || '新对话');
      sessionIdToUse = response.data.session_id;
      currentSessionId.value = sessionIdToUse;
      await fetchSessions();
    } catch (error) {
      console.error("创建新会话时出错:", error);
      messages.value.push({ role: 'assistant', content: '创建新会话失败，请重试。' });
      return;
    }
  }

  const query = userInput.value;
  messages.value.push({ role: 'user', content: query });
  messages.value.push({ role: 'assistant', content: '', references: [] });

  currentSearchSteps.value = [];
  userInput.value = '';
  autoGrowTextarea();
  isLoading.value = true;
  scrollToBottom();

  abortController.value = new AbortController();

  const payload = {
    query,
    session_id: sessionIdToUse,
    user_id: userId,
    use_web: useWeb.value
  };

  try {
    let buffer = '';

    await api.searchStream(
      payload,
      async (chunk) => {
        buffer += chunk;
      let newlineIndex;
      while ((newlineIndex = buffer.indexOf('\n')) !== -1) {
        const line = buffer.slice(0, newlineIndex);
        buffer = buffer.slice(newlineIndex + 1);
        if (line.trim()) {
          processStreamChunk(line);
          await nextTick();
        }
      }
      },
      () => {},
      (error) => {
    if (error.name === 'AbortError') {
      console.log('Fetch aborted by user.');
      const lastMsg = messages.value[messages.value.length - 1];
      if (lastMsg && lastMsg.role === 'assistant' && !lastMsg.content) {
         lastMsg.content = '回答已停止。';
      }
    } else {
      console.error('流处理错误:', error);
      const lastMsg = messages.value[messages.value.length - 1];
      if (lastMsg && lastMsg.role === 'assistant') {
        lastMsg.content = `发生错误: ${error.message}`;
      }
    }
      },
      abortController.value.signal
    );
  } finally {
    isLoading.value = false;
    abortController.value = null;
  }
};

const processStreamChunk = (line) => {
  try {
    const chunk = JSON.parse(line);
    const { type, payload } = chunk;
    const currentMessage = messages.value[messages.value.length - 1];

    switch (type) {
      case 'process': {
        let icon = '⏳'; 
        if (payload.includes("正在分析问题")) {
          icon = '🤔';
        } else if (payload.includes("不需要搜索")) {
          icon = '💬';
        } else if (payload.includes("搜索关键词")) {
          icon = '🔍';
        } else if (payload.includes("搜索完成")) {
          icon = '✅';
        }

        currentSearchSteps.value.push({
          text: payload,
          icon: icon,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        });
        scrollToBottom();
        break;
      }
      case 'answer_chunk':
        if (currentMessage && currentMessage.role === 'assistant') {
          currentMessage.content += payload;
          scrollToBottom();
        }
        break;
      case 'reference':
        if (currentMessage && currentMessage.role === 'assistant') {
          currentMessage.references = payload;
        }
        break;
      case 'error':
        if (currentMessage && currentMessage.role === 'assistant') {
          currentMessage.content = `后端错误: ${payload}`;
        }
        break;
    }
  } catch (error) {
    console.error('解析JSON块时出错:', error, '原始数据:', line);
  }
};

const handleEnter = (e) => {
  if (!e.shiftKey && !e.isComposing) {
    e.preventDefault();
    sendMessage();
  }
};

const handleLogout = () => {
  sessionStorage.clear();
  router.push('/login');
};

const navigateToConfig = () => {
  router.push('/config');
};

onMounted(() => {
  fetchSessions();
});

watch(userInput, autoGrowTextarea);
</script>

<style scoped>

.overflow-y-auto {
  scrollbar-width: thin;
  scrollbar-color: rgba(156, 163, 175, 0.5) transparent;
}
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}
.overflow-y-auto::-webkit-scrollbar-track {
  background: transparent;
}
.overflow-y-auto::-webkit-scrollbar-thumb {
  background: rgba(156, 163, 175, 0.5);
  border-radius: 3px;
}
.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: rgba(156, 163, 175, 0.8);
}
.animate-fade-in {
  animation: fadeIn 0.6s ease-out;
}
.animate-slide-in {
  animation: slideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
textarea:focus + .absolute {
  background: linear-gradient(90deg, transparent, theme('colors.blue.400'), transparent);
  opacity: 0.6;
  transition: opacity 0.3s ease;
}
@media (max-width: 768px) {
  .absolute.bottom-0 {
    padding-left: 1rem;
    padding-right: 1rem;
  }
}
</style>