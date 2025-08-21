<template>
  <div class="home-wrapper">
    <main class="main-content">
      <div class="ask-doc-header">
        <h1>Ask-Doc</h1>
        <button class="upload-btn">
          {{ $t('uploadDoc') }}
        </button>
      </div>
      <div class="ask-box">
        <input class="ask-input" :placeholder="$t('askSomething')" />
      </div>

      <div class="qa-block">
        <div class="q-row">
          <span class="q-icon">Q</span>
          <span class="q-text">What is policy on confidentiality?</span>
        </div>
        <div class="a-row">
          <div class="a-card">
            <div class="a-source">
              According to Page 3 of the Code of Conduct:
            </div>
            <blockquote class="a-quote">
              “Confidential information must be protected and should not disclosed, except to individuals with a legitimate need to know.”
            </blockquote>
            <button class="view-page-btn">{{ $t('viewPage') }} 3</button>
          </div>
        </div>
      </div>
      <div class="qa-block">
        <div class="q-row">
          <span class="q-icon">Q</span>
          <span class="q-text">When was the policy updated?</span>
        </div>
      </div>
      <div class="upload-zone">
        <div class="upload-drag">
          <span class="upload-icon">☁️</span>
          <p>{{ $t('dragDropDocs') }} <br/> <span class="upload-link">{{ $t('orClickUpload') }}</span></p>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
// i18n এর কোন ইমপোর্ট প্রয়োজন নাই, গ্লোবালেই কাজ করবে।
</script>

<style scoped>
.home-wrapper {
  display: flex;
  min-height: 100vh;
  background: #f6f9fc;
}
.sidebar {
  width: 235px;
  background: #fff;
  border-right: 1px solid #ebebeb;
  padding: 26px 18px 16px 18px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.logo {
  font-size: 1.55rem;
  font-weight: 700;
  color: #2945a6;
  margin-bottom: 36px;
  letter-spacing: -1.5px;
}
.brand-title { color: #2945a6; }
.brand-highlight { color: #2788df; }
.nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.nav-link {
  color: #212b44;
  padding: 11px 14px;
  border-radius: 9px;
  text-decoration: none;
  font-size: 1rem;
  font-weight: 500;
  transition: background 0.12s;
}
.nav-link.active,
.nav-link.router-link-exact-active {
  background: #e8f1ff;
  color: #2788df;
  font-weight: 600;
}
.sidebar-footer {
  margin-top: 28px;
  color: #6b7797;
  font-size: 0.98rem;
  text-align: center;
  opacity: .95;
}
.main-content {
  flex: 1;
  padding: 36px 36px 24px 36px;
  max-width: 920px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 26px;
}
.ask-doc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 13px;
}
.ask-doc-header h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #212b44;
  letter-spacing: -1px;
}
.upload-btn {
  background: #2788df;
  color: #fff;
  border: none;
  padding: 8px 19px;
  border-radius: 7px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 9px 0 rgba(33, 150, 243, 0.08);
  transition: background 0.15s;
}
.upload-btn:hover { background: #185fa5; }
.ask-box {
  margin-bottom: 7px;
}
.ask-input {
  width: 100%;
  border: 1.2px solid #d7e3fc;
  border-radius: 8px;
  font-size: 1.06rem;
  padding: 12px 16px;
  background: #fff;
  transition: border 0.18s;
}
.ask-input:focus {
  border: 1.7px solid #2788df;
  outline: none;
}
.qa-block {
  background: #fff;
  border-radius: 13px;
  box-shadow: 0 2px 10px 0 rgba(44, 67, 116, 0.05);
  padding: 20px 22px 16px 22px;
  margin-bottom: 16px;
}
.q-row {
  display: flex;
  align-items: center;
  gap: 11px;
  font-weight: 600;
  color: #272f44;
  font-size: 1.08rem;
}
.q-icon {
  background: #e8f1ff;
  color: #2788df;
  border-radius: 50%;
  width: 27px; height: 27px;
  display: inline-flex;
  align-items: center; justify-content: center;
  font-weight: 700;
  font-size: 1rem;
}
.a-row {
  margin-top: 9px;
}
.a-card {
  background: #f6f9fc;
  border-radius: 9px;
  padding: 17px 16px 13px 16px;
}
.a-source {
  font-size: 0.98rem;
  color: #5b6e97;
  margin-bottom: 8px;
}
.a-quote {
  font-size: 1.05rem;
  margin-bottom: 10px;
  color: #212b44;
  background: #e8f1ff;
  border-radius: 7px;
  padding: 10px 12px;
}
.view-page-btn {
  background: #fff;
  border: 1px solid #2788df;
  color: #2788df;
  padding: 5px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.96rem;
  font-weight: 600;
  transition: background 0.13s;
}
.view-page-btn:hover { background: #f1f7ff; }
.upload-zone {
  border: 2px dashed #2788df;
  background: #eaf2fc;
  border-radius: 13px;
  margin: 14px 0 0 0;
  padding: 40px 10px;
  text-align: center;
  min-height: 158px;
  max-width: 350px;
  align-self: flex-end;
}
.upload-icon {
  font-size: 2.1rem;
  color: #2788df;
  display: block;
  margin-bottom: 12px;
}
.upload-link {
  color: #185fa5;
  cursor: pointer;
  text-decoration: underline;
}
@media (max-width: 900px) {
  .main-content { padding: 20px 7px; }
  .sidebar { width: 170px; padding: 19px 8px; }
  .logo { font-size: 1.1rem; }
}
@media (max-width: 600px) {
  .home-wrapper { flex-direction: column; }
  .sidebar { width: 100%; flex-direction: row; justify-content: flex-start; align-items: center; border: none; border-bottom: 1px solid #ebebeb; }
  .main-content { padding: 10px 2px; }
}
</style>
