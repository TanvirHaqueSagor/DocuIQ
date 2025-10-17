# Testing Specification

## Overview
- **Backend**: Django + Django REST Framework, token auth via Simple JWT. New tests target key account, document, ingest, metrics, middleware, and docuapi behaviours.
- **Frontend**: Vue 3 (Vite). Vitest + Vue Test Utils provide component-level and service-level coverage for auth flows and ingest UI.

## Backend Test Coverage
- `core.settings_test`: SQLite-backed, in-memory friendly settings with eager Celery tasks, relaxed logging, and `.example.com` host support. Enables isolated tests without Postgres, Redis, Celery, or pdfminer at runtime.
- `accounts.tests.test_auth`: Validates individual/org registration rules, login token payloads, and organization employee creation (permission enforcement).
- `documents.tests.test_documents_api`: Confirms per-tenant filtering, automatic tenant assignment on create, and scoped delete permissions.
- `docuapi.tests.test_views`: Exercises protected health endpoint and authenticated upload semantics through the DRF request factory.
- `ingest.tests.test_ingest_api`: Verifies source CRUD scoping, web job queuing (`process_web_job.delay`), and upload queuing (`process_item.delay`).
- `metrics.tests.test_metrics_api`: Asserts dashboard summary counts/deltas and usage time-series generation for tenant requests.
- `core.tests.test_middleware`: Unit coverage for `extract_subdomain`.

## Frontend Test Coverage
- `LoginView.spec`: Mocks router + i18n to ensure failed logins surface validation messaging and successful logins persist tokens then navigate to `/dashboard`.
- `ImportWizard.spec`: Confirms preset tab activation and that the web connector posts to ingest jobs, surfacing success feedback.
- `dashboard.service.spec`: Verifies fetch wrappers attach bearer headers, propagate errors, and honour limiting arguments.
- `vite.config.js` now embeds Vitest config; `src/tests/setup.js` resets mocks/localStorage between tests.
- `package.json` adds `npm test` alias for Vitest (requires `npm install` to pull `vitest`, `@vue/test-utils`, and `jsdom`).

## How To Run
1. **Install dependencies**
   - Backend: `pip install -r backend/requirements.txt`
   - Frontend: `cd frontend && npm install` (network access required for new dev deps)
2. **Unified runner**: `bash run_tests.sh`
   - Backend executes with `DJANGO_SETTINGS_MODULE=core.settings_test`
   - Frontend runs `npm test` (Vitest). Ensure the script is executable (`chmod +x run_tests.sh`).
3. **Manual commands**
   - Backend only: `cd backend && python3 manage.py test --settings=core.settings_test`
   - Frontend only: `cd frontend && npm test`

## Future Enhancements
- Add Celery task unit tests once a deterministic workflow runner or mocks for `requests.post` are acceptable for deeper job coverage.
- Expand frontend coverage to dashboard visual components (Charts) and router guards using an in-memory router.
- Integrate CI (GitHub Actions) with job matrix: Python (backend) + Node (frontend) using the new settings/script.
