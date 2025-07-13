<template>
  <div>
    <label class="block text-sm font-medium text-gray-700">{{ label }}</label>
    <input 
      type="password" 
      :value="modelValue" 
      @input="$emit('update:modelValue', $event.target.value)" 
      class="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
    >
  </div>
</template>

<script setup>
defineProps({
  label: String,
  modelValue: String,
});
defineEmits(['update:modelValue']);
</script> 