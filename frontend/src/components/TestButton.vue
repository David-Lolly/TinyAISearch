<template>
  <div class="flex items-center justify-start mt-2">
    <button @click="$emit('click')" :disabled="status.testing" class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-400">
        {{ status.testing ? '测试中...' : '测试连接' }}
    </button>
    <span v-if="status.message" :class="['ml-4 text-sm', status.success ? 'text-green-600' : 'text-red-600']">
        {{ status.success ? '✅' : '❌' }} {{ status.message }}
    </span>
  </div>
</template>

<script setup>
defineProps({
  status: {
    type: Object,
    required: true,
  }
});
defineEmits(['click']);
</script> 