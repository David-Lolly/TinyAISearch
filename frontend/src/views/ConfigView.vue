<template>
  <div class="min-h-screen bg-gray-50 p-4 sm:p-8">
    <div class="max-w-4xl w-full bg-white shadow-lg rounded-lg p-8 space-y-8 mx-auto">
      <div class="text-center">
        <h1 class="text-3xl font-bold text-gray-800">欢迎使用 Tiny AI Search</h1>
        <p class="text-gray-500 mt-2">首次使用，请完成以下基础配置以启动服务。</p>
      </div>

      <ConfigSection title="检索模式配置" description="选择不同的检索策略。V2更智能，V1提供更多控制。">
          <div class="mt-4 space-y-4">
              <div class="flex items-center">
                  <input id="retrieval_v2" name="retrieval_version" type="radio" value="v2" v-model="config.retrieval_version" class="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300">
                  <label for="retrieval_v2" class="ml-3 block text-sm font-medium text-gray-700">V2 模式 (推荐)</label>
              </div>
              <div class="flex items-center">
                  <input id="retrieval_v1" name="retrieval_version" type="radio" value="v1" v-model="config.retrieval_version" class="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300">
                  <label for="retrieval_v1" class="ml-3 block text-sm font-medium text-gray-700">V1 模式 (高级)</label>
              </div>
          </div>
          <template v-if="config.retrieval_version === 'v1'">
              <div class="mt-4">
                  <label for="retrieval_quality" class="block text-sm font-medium text-gray-700">V1 检索质量</label>
                  <div class="relative mt-1">
                      <select id="retrieval_quality" v-model="config.retrieval_quality" 
                              class="block w-full appearance-none bg-white border border-gray-300 rounded-md py-2 pl-4 pr-10 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500">
                          <option value="high">High</option>
                          <option value="higher">Higher</option>
                      </select>
                      <span class="pointer-events-none absolute inset-y-0 right-3 flex items-center">
                        <ChevronDownIcon class="w-4 h-4 text-gray-500" />
                      </span>
                  </div>
              </div>
          </template>
      </ConfigSection>

      
      <ConfigSection title="LLM 大语言模型配置" description="负责生成对话回复的核心模型。">
        <TextInput label="模型名称" v-model="config.llm_model_name" placeholder="e.g., qwen-turbo" />
        <TextInput label="API Base URL" v-model="config.llm_base_url" placeholder="e.g., https://dashscope.aliyuncs.com/compatible-mode/v1" />
        <PasswordInput label="API Key" v-model="config.llm_api_key" />
        <TestButton :status="testStatus.llm" @click="testConnection('llm')" />
      </ConfigSection>

      
      <ConfigSection title="Embedding 模型配置" description="负责将文本转换为向量，用于相似度检索。">
        <TextInput label="模型名称" v-model="config.embedding_model_name" placeholder="e.g., text-embedding-v4" />
        <TextInput label="API Base URL" v-model="config.embedding_base_url" placeholder="e.g., https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings" />
        <PasswordInput label="API Key" v-model="config.embedding_api_key" />
        <TestButton :status="testStatus.embedding" @click="testConnection('embedding')" />
      </ConfigSection>

      
      <template v-if="config.retrieval_version === 'v1'">
        <ConfigSection title="Rerank 模型配置" description="负责对初步检索结果进行精排序，提升答案质量。">
          <TextInput label="模型名称" v-model="config.rerank_model_name" placeholder="e.g., BAAI/bge-reranker-v2-m3" />
          <TextInput label="API Base URL" v-model="config.rerank_base_url" placeholder="e.g., https://api.siliconflow.cn/v1/rerank" />
          <PasswordInput label="API Key" v-model="config.rerank_api_key" />
          <TestButton :status="testStatus.rerank" @click="testConnection('rerank')" />
        </ConfigSection>
      </template>

      
      <ConfigSection title="辅助搜索引擎 (可选)" description="启用Google作为备用的搜索引擎，防止DuckDuckGo被封。">
        <div class="flex items-center">
          <input type="checkbox" id="google_enabled" v-model="config.google_search_enabled" class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded">
          <label for="google_enabled" class="ml-2 block text-sm text-gray-900">启用 Google 搜索</label>
        </div>
        <template v-if="config.google_search_enabled">
          <PasswordInput label="Google API Key" v-model="config.google_api_key" />
          <TextInput label="Google CSE ID" v-model="config.google_cse_id" placeholder="请输入你的可编程搜索引擎ID" />
          <TestButton :status="testStatus.google" @click="testConnection('google')" />
        </template>
      </ConfigSection>
      
      
      <div class="pt-5">
        <button 
          @click="saveConfiguration" 
          :disabled="!canSave || isSaving"
          class="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-400">
          {{ isSaving ? '正在保存...' : '保存配置并启动' }}
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import api from '../services/api';


import ConfigSection from '../components/ConfigSection.vue';
import TextInput from '../components/TextInput.vue';
import PasswordInput from '../components/PasswordInput.vue';
import TestButton from '../components/TestButton.vue';
import { ChevronDownIcon } from '@heroicons/vue/24/outline';

const router = useRouter();
const userId = ref(sessionStorage.getItem('userId') || '');


const config = reactive({
  llm_model_name: '',
  llm_base_url: '',
  llm_api_key: '',
  embedding_model_name: '',
  embedding_base_url: '',
  embedding_api_key: '',
  rerank_model_name: '',
  rerank_base_url: '',
  rerank_api_key: '',
  google_search_enabled: false,
  google_api_key: '',
  google_cse_id: '',
  retrieval_version: 'v2',
  retrieval_quality: 'high',
});

const testStatus = reactive({
  llm: { testing: false, message: '', success: false },
  embedding: { testing: false, message: '', success: false },
  rerank: { testing: false, message: '', success: false },
  google: { testing: false, message: '', success: false },
});

const isSaving = ref(false);


watch(() => config.retrieval_version, (newVal) => {
  if (newVal === 'v2') {
    
    testStatus.rerank.testing = false;
    testStatus.rerank.message = '';
    testStatus.rerank.success = false;
  }
});


const canSave = computed(() => {
  if (config.retrieval_version === 'v1') {
    return testStatus.llm.success && testStatus.embedding.success && testStatus.rerank.success;
  } else {
    return testStatus.llm.success && testStatus.embedding.success;
  }
});

onMounted(async () => {
  
  if (!userId.value) {
    router.push('/login');
    return;
  }
  try {
    const response = await api.get('/api/settings');
    if (response.data && Object.keys(response.data).length > 0) {
      Object.assign(config, response.data);
      
      config.google_search_enabled = String(config.google_search_enabled).toLowerCase() === 'true';
    }
    
    if (!config.retrieval_version) config.retrieval_version = 'v2';
    if (!config.retrieval_quality) config.retrieval_quality = 'high';
  } catch (error) {
    console.error("Failed to load initial settings:", error);
  }
});

async function testConnection(type) {
  const status = testStatus[type];
  status.testing = true;
  status.message = '';

  let payload = {};
  let url = `/api/test/${type}`;

  switch(type) {
    case 'llm':
      payload = { model_name: config.llm_model_name, base_url: config.llm_base_url, api_key: config.llm_api_key };
      break;
    case 'embedding':
      payload = { model_name: config.embedding_model_name, base_url: config.embedding_base_url, api_key: config.embedding_api_key };
      break;
    case 'rerank':
      payload = { model_name: config.rerank_model_name, base_url: config.rerank_base_url, api_key: config.rerank_api_key };
      break;
    case 'google':
      payload = { api_key: config.google_api_key, cse_id: config.google_cse_id };
      break;
  }

  
  console.log(`[DEBUG] Preparing to send request...`);
  console.log(`[DEBUG] URL: ${url}`);
  console.log(`[DEBUG] Payload:`, JSON.parse(JSON.stringify(payload)));
  

  try {
    const response = await api.post(url, payload);
    status.success = response.data.success;
    status.message = response.data.message;
  } catch (error) {
    status.success = false;
    status.message = error.response?.data?.message || '请求失败，请检查后端服务是否运行。';
  } finally {
    status.testing = false;
  }
}

async function saveConfiguration() {
  isSaving.value = true;
  try {
    const settingsToSave = { ...config, google_search_enabled: String(config.google_search_enabled) };
    await api.post('/api/settings', { settings: settingsToSave });
    alert('配置已成功保存！即将进入对话界面。');
    router.push({ name: 'Chat', query: { fromConfigSave: 'true' } }); 
  } catch (error) {
    alert('保存失败: ' + (error.response?.data?.message || '未知错误'));
  } finally {
    isSaving.value = false;
  }
}
</script> 