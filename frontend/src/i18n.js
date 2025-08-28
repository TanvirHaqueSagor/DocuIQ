// src/i18n.js
import { createI18n } from 'vue-i18n'

import en from './locales/en.json'
import ja from './locales/ja.json'
import bn from './locales/bn.json'
import hi from './locales/hi.json'
import ko from './locales/ko.json'
import zh from './locales/zh.json'
import es from './locales/es.json'

const i18n = createI18n({
  locale: localStorage.getItem('locale') || 'en',
  fallbackLocale: 'en',
  messages: { en, ja, bn, hi, ko, zh, es }
})

export default i18n