<template>
  <div class="upload-box">
    <div class="icon">&#8682;</div>
    <div>
      {{ $t ? $t('dragDropDocs') : 'Drag and drop a PDF, DOCX, or TXT here' }}<br>
      <span class="or">{{ $t ? $t('orClickUpload') : 'or click to upload' }}</span>
    </div>
  </div>
</template>
<style scoped>
.upload-box {
  border: 2px dashed #0d8de7;
  background: #f9fcff;
  border-radius: 10px;
  color: #0d8de7;
  padding: 50px 30px;
  text-align: center;
  cursor: pointer;
  font-size: 1.09rem;
  max-width: 350px;
  margin: 0 auto;
}
.icon {
  font-size: 2.5rem;
  margin-bottom: 10px;
}
.or { color: #4c6287; font-size: 0.99rem; }
</style>
