import { reactive } from 'vue'
export const importWizardBus = reactive({
  open: false,
  preset: null,  // e.g., { tab: 'files' | 'web' | 's3' ... }
})
export function openImportWizard(preset = null) {
  importWizardBus.open = true
  importWizardBus.preset = preset
}
export function closeImportWizard() {
  importWizardBus.open = false
  importWizardBus.preset = null
}
