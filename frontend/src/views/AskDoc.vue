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
  border: 1px solid var(--line);
  background: var(--card);
  color: var(--txt);
  outline: none;
  box-shadow: 0 2px 7px 0 rgba(63, 81, 181, 0.03);
  transition: border .13s;
}
.upload-btn {
  background: var(--blue);
  color: #fff;
  border-radius: 7px;
  font-weight: 600;
  font-size: 1.02rem;
  border: none;
  padding: 10px 19px;
  cursor: pointer;
  transition: background .14s;
}
.upload-btn:hover { filter: brightness(1.1); }
.qa-area { margin-top: 22px; }
.qa-block { margin-bottom: 24px; }
.q-label {
  display: inline-block;
  background: rgba(96,165,250,.15);
  color: var(--blue);
  border-radius: 4px;
  font-weight: 600;
  font-size: 1.02rem;
  padding: 4px 12px;
  margin-bottom: 5px;
}
.question { font-weight: 600; margin-bottom: 7px; }
.answer-card {
  background: var(--card);
  border-radius: 10px;
  border: 1px solid var(--line);
  padding: 18px 18px 15px 18px;
  margin-top: 7px;
  color: var(--txt);
}
.answer-label {
  color: var(--blue);
  font-weight: 500;
  margin-bottom: 7px;
  font-size: 0.98rem;
}
.page-btn {
  margin-top: 10px;
  background: var(--blue);
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 6px 15px;
  font-size: 0.99rem;
  cursor: pointer;
}
.empty-state { margin: 50px 0; }
</style>
