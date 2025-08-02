# 📘 DocuIQ Setup Guide (Docker-based)

Welcome to **DocuIQ** — an intelligent RAG-powered document assistant powered by Django, FastAPI, Vue 3, and Docker.

---

## 🚀 Project Structure

```
.
├── .env.example           # Environment template
├── docker-compose.yml     # Orchestration for all services
├── backend/               # Django + DRF + JWT
├── ai_engine/             # FastAPI service for AI search & indexing
└── frontend/              # Vue 3 + Vite + Tailwind
```

---

## ⚙️ Prerequisites

- Docker & Docker Compose (v2+)
- Git (optional)

---

## 🛠️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/your-username/docuiq.git
cd docuiq
```

### 2. Create `.env` file
```bash
cp .env.example .env
```
You can adjust PostgreSQL credentials, Django secret key, and service URLs inside this file.

### 3. Build and Start the Services
```bash
docker compose up --build
```

⏳ First time may take a few minutes to download and install everything.

### 4. Create Django Superuser (Optional)
```bash
docker compose exec backend python manage.py createsuperuser
```
Use this to access Django admin at: [http://localhost:8888/admin](http://localhost:8888/admin)

---

## 🔗 URLs to Access

| Service        | URL                          |
|----------------|-------------------------------|
| Frontend (Vue) | http://localhost:3000        |
| Backend (Django) | http://localhost:8888      |
| AI Engine (FastAPI) | http://localhost:9000   |

---

## 🔐 JWT Auth (Sample Flow)
- Login: `POST /api/token/` with `{ username, password }`
- Refresh: `POST /api/token/refresh/`
- Use access token in `Authorization: Bearer <token>`

---

## 📤 AI Document Upload
```
POST /upload (FastAPI)
File Upload -> Stored in memory and indexed (demo only)
```

## 🔍 Ask a Question
```
POST /ask
{
  "question": "What is revenue?",
  "document_id": "sample.txt"
}
```

---

## 🧹 Clean Up
```bash
docker compose down -v
```

---

## ✅ Next Steps
- Add PDF reader to AI service (PyMuPDF)
- Connect AI response to frontend
- Multi-user support & workspace
- SaaS billing module (Stripe)

---

Made with ❤️ for intelligent document operations.
