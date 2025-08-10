<template>
  
  <div ref="messageEl" class="message-container py-3 px-6"
       :class="{ 'bg-background-secondary border-t border-b border-gray-100': isUser }">
    <div class="max-w-4xl mx-auto flex items-start space-x-4">
      
      <div class="flex-shrink-0">
        <div class="w-8 h-8 rounded-full flex items-center justify-center text-white font-semibold shadow-md transition-all duration-200 hover:scale-105"
             :class="isUser ? 'bg-gradient-to-br from-blue-500 to-blue-600' : 'bg-red-500'">
          <span v-if="isUser" class="text-xs">{{ userInitial }}</span>
          <span v-else>T</span>
        </div>
      </div>

      
      <div class="flex-grow pt-0">
        
        <div v-if="isUser" class="text-text-primary leading-relaxed pt-1">
          <p>{{ message.content }}</p>
        </div>

        
        <div v-else class="space-y-4">
          
          <div v-if="searchSteps.length > 0 && !message.content.trim()" class="space-y-2">
            
            <div
              v-for="(step, index) in searchSteps"
              :key="index"
              class="search-step-card group flex items-center space-x-3 p-3 bg-white rounded-lg border border-gray-100 shadow-sm hover:shadow-md transition-all duration-300 animate-fade-in"
              :style="{ animationDelay: `${index * 150}ms` }">
               <div class="flex-shrink-0 w-6 h-6 rounded-full bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center group-hover:from-blue-100 group-hover:to-blue-200 transition-all duration-300">
                <span class="text-sm">{{ step.icon }}</span>
              </div>
              <div class="flex-1 min-w-0 flex justify-between items-center">
                <p class="text-text-primary text-xs font-medium">{{ step.text }}</p>
                <p class="text-text-secondary text-xs">{{ step.timestamp }}</p>
              </div>
              <div class="flex-shrink-0">
                <div class="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse-gentle"></div>
              </div>
            </div>
            <div v-if="isStreaming" class="flex items-center mt-2">
              <div class="flex items-center space-x-2 px-2 py-1 bg-blue-50 rounded-full">
                <div class="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></div>
                <span class="text-blue-600 text-xs font-medium">AI正在思考中...</span>
              </div>
            </div>
          </div>

          
          <div v-if="message.content.trim()" class="space-y-4">
            
            <div class="prose prose-base prose-slate max-w-3xl" v-html="formattedContent"></div>

            
            <div v-if="message.content.trim() && !isStreaming" class="flex items-center justify-start -mt-2">
                <button @click="copyFullResponse" class="copy-full-response-button">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    <span>{{ copyButtonText }}</span>
                </button>
            </div>


            
            <div v-if="flattenedReferences.length > 0" class="reference-section mt-4 p-3 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg border border-gray-200 shadow-sm">
              
               <div class="flex items-center mb-2">
                <div class="w-5 h-5 bg-blue-500 rounded-md flex items-center justify-center mr-2">
                  <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path>
                  </svg>
                </div>
                <h4 class="font-semibold text-text-primary text-sm">参考资料</h4>
                <span class="ml-2 px-1.5 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">{{ flattenedReferences.length }}</span>
              </div>
               <div class="grid gap-2">
                <a v-for="(item, index) in flattenedReferences" :key="index" :href="item.url" target="_blank" rel="noopener noreferrer" class="reference-link group flex items-start space-x-2 p-2 bg-white rounded-md border border-gray-200 hover:border-blue-300 hover:shadow-sm transition-all duration-200">
                  <div class="flex-shrink-0 w-4 h-4 bg-blue-50 rounded-full flex items-center justify-center group-hover:bg-blue-100 transition-colors duration-200 mt-0.5">
                    <svg class="w-2 h-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-text-primary text-xs font-medium leading-relaxed group-hover:text-blue-700 transition-colors duration-200 line-clamp-1">{{ item.title }}</p>
                  </div>
                   <div class="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                    <svg class="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                  </div>
                </a>
              </div>
            </div>
          </div>

          
          <div v-if="isStreaming && message.content.trim()" class="flex items-center mt-2">
            <div class="flex items-center space-x-2 px-2 py-1 bg-blue-50 rounded-full">
              <div class="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></div>
              <span class="text-blue-600 text-xs font-medium">正在生成回复...</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUpdated, ref } from 'vue';
import { marked } from 'marked';
import hljs from 'highlight.js';
import 'highlight.js/styles/atom-one-light.css';
import katex from 'katex';
import 'katex/dist/katex.min.css';

const props = defineProps({
  message: { type: Object, required: true },
  userId: { type: String, required: true },
  isStreaming: { type: Boolean, default: false },
  searchSteps: { type: Array, default: () => [] },
});

const messageEl = ref(null);
const copyButtonText = ref('复制');

const isUser = computed(() => props.message.role === 'user');
const userInitial = computed(() => props.userId ? props.userId.charAt(0).toUpperCase() : 'Y');

// 数学公式渲染函数
const processMathFormulas = (text) => {
  if (!text) return text;
  
  const mathPlaceholders = [];
  let processedText = text;
  
  // 首先处理块级公式 $$...$$
  processedText = processedText.replace(/\$\$([\s\S]*?)\$\$/g, (match, formula) => {
    try {
      const rendered = katex.renderToString(formula.trim(), {
        displayMode: true,
        throwOnError: false,
        strict: false,
        output: 'html'
      });
      const placeholder = `MATH_PLACEHOLDER_${mathPlaceholders.length}`;
      mathPlaceholders.push(rendered);
      return placeholder;
    } catch (e) {
      console.warn('LaTeX render error:', e);
      return match; // 如果渲染失败，返回原文
    }
  });
  
  // 然后处理行内公式 $...$
  processedText = processedText.replace(/\$([^$\n]+?)\$/g, (match, formula) => {
    try {
      const rendered = katex.renderToString(formula.trim(), {
        displayMode: false,
        throwOnError: false,
        strict: false,
        output: 'html'
      });
      const placeholder = `MATH_PLACEHOLDER_${mathPlaceholders.length}`;
      mathPlaceholders.push(rendered);
      return placeholder;
    } catch (e) {
      console.warn('LaTeX render error:', e);
      return match; // 如果渲染失败，返回原文
    }
  });
  
  return { processedText, mathPlaceholders };
};

marked.setOptions({
  gfm: true,
  breaks: true,
  highlight: (code, lang) => {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
    return hljs.highlight(code, { language }).value;
  },
});

const formattedContent = computed(() => {
  if (isUser.value) return props.message.content;
  if (typeof props.message.content !== 'string') return '';
  let cleanContent = props.message.content
    .replace(/^提示：.*\n?/gm, '')
    .replace(/参考信息：.*$/s, '');
  
  // 先提取并渲染数学公式，用占位符替代
  const { processedText, mathPlaceholders } = processMathFormulas(cleanContent);
  
  // 处理markdown
  let htmlContent = marked(processedText);
  
  // 最后将占位符替换为渲染好的数学公式
  mathPlaceholders.forEach((mathHtml, index) => {
    const placeholder = `MATH_PLACEHOLDER_${index}`;
    htmlContent = htmlContent.replace(new RegExp(placeholder, 'g'), mathHtml);
  });
  
  return htmlContent;
});

const flattenedReferences = computed(() => {
    if (!props.message.references) return [];
    const references = [];
    for (const item of props.message.references) {
        if (typeof item === 'object' && item !== null) {
            for (const [title, url] of Object.entries(item)) {
                references.push({ title, url });
            }
        }
    }
    return references;
});

const copyFullResponse = () => {
    if (navigator.clipboard && props.message.content) {
        navigator.clipboard.writeText(props.message.content).then(() => {
            copyButtonText.value = '已复制!';
            setTimeout(() => {
                copyButtonText.value = '复制';
            }, 2000);
        });
    }
};

const setupCodeBlocks = () => {
  if (!messageEl.value) return;
  messageEl.value.querySelectorAll('pre').forEach(preEl => {
    if (preEl.closest('.code-block-container')) return;
    const codeEl = preEl.querySelector('code');
    if (!codeEl) return;
    const languageClass = Array.from(codeEl.classList).find(cls => cls.startsWith('language-'));
    const languageName = languageClass ? languageClass.replace('language-', '') : null;
    const container = document.createElement('div');
    container.className = 'code-block-container';
    const header = document.createElement('div');
    header.className = 'code-block-header';
    const langSpan = document.createElement('span');
    langSpan.className = 'language-name';
    langSpan.textContent = languageName || 'Code';
    const copyIconSVG = `
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
      </svg>`;
    const successIconSVG = `
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="text-green-500" viewBox="0 0 16 16">
        <path d="M12.736 3.97a.733.733 0 0 1 1.047 0c.286.289.29.756.01 1.05L7.88 12.01a.733.733 0 0 1-1.065.02L3.217 8.384a.757.757 0 0 1 0-1.06.733.733 0 0 1 1.047 0l3.052 3.093 5.4-6.425a.247.247 0 0 1 .02-.022Z"/>
      </svg>`;
    const copyButton = document.createElement('button');
    copyButton.className = 'copy-code-button';
    copyButton.innerHTML = copyIconSVG;
    let copyTimeout;
    copyButton.onclick = () => {
      navigator.clipboard.writeText(codeEl.innerText).then(() => {
        copyButton.innerHTML = successIconSVG;
        clearTimeout(copyTimeout);
        copyTimeout = setTimeout(() => {
          copyButton.innerHTML = copyIconSVG;
        }, 2000);
      });
    };
    header.appendChild(langSpan);
    header.appendChild(copyButton);
    container.appendChild(header);
    preEl.parentNode.insertBefore(container, preEl);
    container.appendChild(preEl);
  });
};

onMounted(setupCodeBlocks);
onUpdated(setupCodeBlocks);
</script>

<style>

.prose {
  --tw-prose-body: theme('colors.text-primary');
  --tw-prose-headings: theme('colors.text-primary');
  --tw-prose-lead: theme('colors.text-secondary');
  --tw-prose-links: theme('colors.blue.600');
  --tw-prose-bold: theme('colors.text-primary');
  --tw-prose-counters: theme('colors.text-secondary');
  --tw-prose-bullets: theme('colors.text-secondary');
  --tw-prose-hr: theme('colors.gray.200');
  --tw-prose-quotes: theme('colors.text-primary');
  --tw-prose-quote-borders: theme('colors.gray.200');
  --tw-prose-captions: theme('colors.text-secondary');
  --tw-prose-code: theme('colors.text-primary');
  --tw-prose-pre-code: theme('colors.gray.800');
  --tw-prose-pre-bg: #f6f8fa;
  --tw-prose-th-borders: theme('colors.gray.300');
  --tw-prose-td-borders: theme('colors.gray.200');
}

.prose table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1.25em;
  margin-bottom: 1.25em;
  border: 1px solid theme('colors.gray.300');
  display: table !important;
}

.prose th,
.prose td {
  border: 1px solid theme('colors.gray.300');
  padding: 0.75rem 1rem;
}

.prose th {
  font-weight: 600;
  background-color: theme('colors.gray.50');
}

.prose tbody tr:nth-child(even) {
  background-color: theme('colors.gray.50');
}

.code-block-container {
  background-color: #f6f8fa;
  border-radius: 8px;
  border: 1px solid #d0d7de;
  margin-top: 1.5em;
  margin-bottom: 1.5em;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.code-block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.875rem;
  background-color: #eef2f5;
  border-bottom: 1px solid #d0d7de;
}

.language-name {
  color: #24292f;
  font-size: 0.8125rem;
  font-family: sans-serif;
  text-transform: capitalize;
}

.copy-code-button {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #24292f;
  background: none;
  border: none;
  padding: 4px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.copy-code-button:hover {
  background-color: #d0d7de;
}

.copy-code-button svg {
  width: 16px;
  height: 16px;
}

.code-block-container pre {
    margin: 0;
    border-radius: 0;
    border: none;
    background: transparent !important;
}

.code-block-container pre code {
    font-size: 0.875rem;
    line-height: 1.5;
}

.prose h1,
.prose h2,
.prose h3,
.prose h4,
.prose h5,
.prose h6 {
  font-size: 1em !important;
  font-weight: 600 !important;
  margin-top: 1.5em;
  margin-bottom: 0.75em;
}

.prose :where(h1, h2, h3, h4, h5, h6):first-child {
  margin-top: 0;
}

.prose :where(p) {
    margin-top: 0.75em;
    margin-bottom: 0.75em;
}
</style>

<style scoped>

.copy-full-response-button {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  background-color: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 9999px;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

.copy-full-response-button:hover {
  background-color: #e5e7eb;
  color: #1f2937;
}

.prose {
  color: #24292f;
}

.prose :where(p) {
  margin-top: 0;
  margin-bottom: 1rem;
}

.prose :where(code):not(:where(pre *)) {
  background-color: rgba(175, 184, 193, 0.2);
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  border-radius: 6px;
}

.prose :where(blockquote) {
  border-left: 0.25em solid #d0d7de;
  padding: 0 1em;
  color: #57606a;
}

.prose :where(blockquote p):last-of-type {
  margin-bottom: 0;
}

/* 分隔线样式优化 */
.prose :where(hr) {
  max-width: 100%;
  margin: 1.5rem 0;
  border: none;
  height: 1px;
  background: #d1d5db;
  opacity: 0.8;
}

/* 确保列表和其他元素也有合适的宽度 */
.prose :where(ul, ol) {
  max-width: 100%;
}

.prose :where(li) {
  margin-top: 0.25em;
  margin-bottom: 0.25em;
}

/* 数学公式样式 */
.prose .katex {
  font-size: 1.1em;
}

.prose .katex-display {
  margin: 1.5em 0;
  text-align: center;
  overflow-x: auto;
  overflow-y: hidden;
}

.prose .katex-display > .katex {
  display: inline-block;
  white-space: nowrap;
  max-width: 100%;
}

/* 行内数学公式 */
.prose .katex-inline {
  margin: 0 0.1em;
}

/* 数学公式在移动端的适配 */
@media (max-width: 768px) {
  .prose .katex-display {
    margin: 1em 0;
    padding: 0 0.5em;
  }
  
  .prose .katex {
    font-size: 1em;
  }
}

.animate-fade-in {
  animation: fadeIn 0.6s ease-out forwards;
  opacity: 0;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.search-step-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.search-step-card:hover {
  transform: translateY(-1px);
}

.reference-link {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.reference-link:hover {
  transform: translateY(-0.5px);
}

.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.animate-pulse-gentle {
  animation: pulseGentle 2s ease-in-out infinite;
}

@keyframes pulseGentle {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

@media (max-width: 768px) {
  .message-container {
    padding: 0.75rem;
  }

  .max-w-4xl {
    max-width: 100%;
  }

  .space-x-4 > :not([hidden]) ~ :not([hidden]) {
    margin-left: 0.75rem;
  }
}
</style>
