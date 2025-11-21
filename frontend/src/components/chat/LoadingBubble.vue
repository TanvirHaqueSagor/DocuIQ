<template>
  <div class="loading-bubble" aria-live="polite" aria-label="Thinking">
    <span class="dot" />
    <span class="dot" />
    <span class="dot" />
  </div>
</template>

<style scoped>
.loading-bubble {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 12px 16px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #9fb4ff;
  animation: pulse 1.2s infinite ease-in-out;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes pulse {
  0%, 80%, 100% { opacity: 0.3; transform: translateY(0); }
  40% { opacity: 1; transform: translateY(-3px); }
}
</style>
