<template>
  <MainLayout>
    <div class="ask-doc-main">
      <div class="top-bar">
        <input
          v-model="question"
          class="search-input"
          :placeholder="$t('askSomething')"
          @keyup.enter="onAsk"
        />
        <button class="upload-btn" @click="triggerFileUpload">{{ $t('uploadDoc') }}</button>
        <input ref="fileInput" type="file" class="file-upload" style="display: none" @change="onFileUpload"/>
      </div>
      <div class="qa-area">
        <div v-if="qa.length" v-for="(item, i) in qa" :key="i" class="qa-block">
          <div class="q-label">Q</div>
          <div class="question">{{ item.q }}</div>
          <div v-if="item.a" class="answer-card">
            <div class="answer-label">{{ $t('answer') }}</div>
            <blockquote>{{ item.a }}</blockquote>
            <button v-if="item.page" class="page-btn">{{ $t ? $t('viewPage') : 'View Page' }} {{ item.page }}</button>
          </div>
        </div>
        <!-- Example Empty State -->
        <div v-else class="empty-state">
          <UploadBox />
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref } from 'vue'
import MainLayout from '../layouts/MainLayout.vue'
import UploadBox from '../components/UploadBox.vue'

const question = ref('')
const qa = ref([
  // Demo data, replace with your API response
  {
    q: "What is poilcy on confidentiality?",
    a: "According to Page 3 of the Code of Conduct: “Confidential information must be protected and should not disclosed, except to individuals with a legitimate need to know.”",
    page: 3
  },
  {
    q: "When was the policy updated?",
    a: "",
    page: null
  }
])

const fileInput = ref(null)
function triggerFileUpload() {
  fileInput.value.click()
}
function onFileUpload(e) {
  // handle your file upload logic here
}
function onAsk() {
  // handle your Ask logic here (API call)
}
</script>

<style scoped>
.ask-doc-main {
  max-width: 900px;
  margin: 35px auto;
  padding: 0 18px;
}
.top-bar {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 28px;
}
.search-input {
  flex: 1;
  padding: 11px 16px;
  font-size: 1.09rem;
  border-radius: 8px;
  border: 1.6px solid #e0e5f1;
  background: #fff;
  outline: none;
  box-shadow: 0 2px 7px 0 rgba(63, 81, 181, 0.03);
  transition: border .13s;
}
.upload-btn {
  background: #195ebf;
  color: #fff;
  border-radius: 7px;
  font-weight: 600;
  font-size: 1.02rem;
  border: none;
  padding: 10px 19px;
  cursor: pointer;
  transition: background .14s;
}
.upload-btn:hover { background: #1675da; }
.qa-area { margin-top: 22px; }
.qa-block { margin-bottom: 24px; }
.q-label {
  display: inline-block;
  background: #eaf3ff;
  color: #2788df;
  border-radius: 4px;
  font-weight: 600;
  font-size: 1.02rem;
  padding: 4px 12px;
  margin-bottom: 5px;
}
.question { font-weight: 600; margin-bottom: 7px; }
.answer-card {
  background: #f6f9fd;
  border-radius: 10px;
  border: 1.2px solid #e7effc;
  padding: 18px 18px 15px 18px;
  margin-top: 7px;
}
.answer-label {
  color: #0d8de7;
  font-weight: 500;
  margin-bottom: 7px;
  font-size: 0.98rem;
}
.page-btn {
  margin-top: 10px;
  background: #0d8de7;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 6px 15px;
  font-size: 0.99rem;
  cursor: pointer;
}
.empty-state { margin: 50px 0; }
</style>
