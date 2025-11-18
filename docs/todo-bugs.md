# DocuIQ TODO & Bug Tracker

Use this doc as the running checklist for outstanding work. Add new entries under the relevant section so they are visible for future sprints or prompt engineering.

## Feature TODOs
- [ ] **Connector automations** – Ship the planned email/document sync connectors (Gmail, Outlook, SharePoint, etc.) so teams no longer rely on manual uploads.
- [ ] **Inline PDF viewer with highlights** – Embed a PDF reader that anchors AI answers to highlighted passages for trust and quick audits.
- [ ] **SaaS-ready multi-tenancy** – Finish the org segmentation, billing hooks, and role-based access control needed for hosted plans.
- [ ] **Celery task coverage** – Add deterministic unit tests (or mocks) for ingestion jobs (`process_web_job`, `process_item`) once the runner story is solid.
- [ ] **Dashboard/UI tests** – Expand Vitest coverage to the new dashboard visual components (UsageSparkline, RecentDocumentsTable, router guards).
- [ ] **Continuous Integration** – Stand up a GitHub Actions workflow that runs backend Django tests and frontend Vitest on every PR.
- [ ] **Observability & usage analytics** – Wire the usage sparkline + metrics API into Mixpanel/Sentry (or equivalent) for customer-facing insights.

## Bugs

### Open
- [ ] **Chat composer send-preference toggle missing** – `sendPrefLabel`, `sendPrefTitle`, and `saveSendPref` exist in `frontend/src/views/Home.vue` but there is no UI control to flip the preference, so users are stuck with “Enter to send.”

### Resolved (current iteration)
- [x] **Stats card delta strings lost their units** – `StatsCard.vue` tried to `parseFloat` any string delta, stripping `%`/unit suffixes and showing `+12` instead of `+12%` (or even `NaN` for textual labels). The component now preserves string props and formats numeric props consistently (see `frontend/src/components/dashboard/StatsCard.vue`).
- [x] **Documents page search query not persisted** – Clicking the search icon or pressing Enter called an empty `applySearch` handler, so the `?q=term` parameter never updated and filters were lost on reload. `frontend/src/views/Documents.vue` now syncs the search term into the router query.
- [x] **Connector setup forms missing** – Navigating to `/connect/:kind` for sources like Google Drive, Slack, Jira, etc. showed an empty panel with no fields, making the integrations unusable. `frontend/src/views/SourceSetup.vue` now ships schema definitions for each connector so every application exposes the right inputs and descriptions.
- [x] **Browser OAuth flow hit 404** – The new “Connect via browser” button opened `/api/ingest/oauth/start`, which didn’t exist. Added `OAuthStartView` and a placeholder template so every connector can complete authorization before the real provider integration is ready (`backend/ingest/urls.py`, `backend/ingest/views.py`, `backend/templates/ingest/oauth_stub.html`).
- [x] **Connector success state unclear** – After authorizing via browser/manual setup the UI gave little feedback. The setup page now shows a success banner with CTA to Documents and the header back button always appears with an arrow (`frontend/src/views/SourceSetup.vue`).
