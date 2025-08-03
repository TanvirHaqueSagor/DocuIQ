<template>
  <select v-model="currentLang" @change="changeLang" style="padding: 4px 8px; border-radius:6px;">
    <option value="en">EN</option>
    <option value="ja">日本語</option>
    <option value="zh">中文</option>
    <option value="ko">한국어</option>
    <option value="es">ES</option>
    <option value="hi">हिन्दी</option>
    <option value="bn">বাংলা</option>
  </select>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
const { locale } = useI18n()
const currentLang = ref(locale.value)
function changeLang() {
  locale.value = currentLang.value
}
</script>
