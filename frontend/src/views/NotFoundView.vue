<template>
  <div class="min-h-screen flex flex-col justify-center items-center bg-gray-100">
    <div class="text-center">
      <h1 class="text-6xl font-bold text-gray-800 mb-4">404</h1>
      <h2 class="text-2xl font-semibold text-gray-600 mb-6">页面未找到</h2>
      <p class="text-gray-500 mb-8">您访问的页面不存在，请检查URL是否正确</p>
      
      <div class="space-x-4">
        <button 
          @click="goHome"
          class="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          返回首页
        </button>
        <button 
          @click="goBack"
          class="px-6 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
        >
          返回上页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function goHome() {
  router.push('/')
}

function goBack() {
  router.go(-1)
}
</script> 