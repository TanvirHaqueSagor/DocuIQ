#!/usr/bin/env bash
set -euo pipefail

echo "Running backend test suite..."
(
  cd backend
  export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-core.settings_test}
  python3 manage.py test "$@"
)

echo "Running frontend test suite..."
(
  cd frontend
  npm test
)
