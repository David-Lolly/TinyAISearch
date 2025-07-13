<template>
  <div class="border-t border-gray-200 pt-6">
    <h3 class="text-lg leading-6 font-medium text-gray-900">{{ title }}</h3>
    <p class="mt-1 text-sm text-gray-500">{{ description }}</p>
    <div class="mt-4 space-y-4">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    required: true,
  }
});
</script> 