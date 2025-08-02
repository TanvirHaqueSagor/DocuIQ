# =============================
# 📄 File: README.md
# =============================

# 🚀 DocuIQ - RAG-Powered Document Intelligence Platform

DocuIQ is an end-to-end intelligent document processing platform powered by AI + RAG (Retrieval-Augmented Generation).

## 🧱 Project Structure

- `frontend/` – Vue 3 + Vite + Tailwind
- `backend/` – Django (API, JWT, Upload handling)
- `ai_engine/` – FastAPI app for RAG-based search/QA
- `docker-compose.yml` – Full stack orchestration

---

## ✅ Prerequisites

- Docker & Docker Compose
- GitHub SSH setup (optional)

---

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone git@github.com-personal:TanvirHaqueSagor/DocuIQ.git
cd DocuIQ
```

### 2. Create `.env` File

Copy the example and fill in secrets:

```bash
cp .env.example .env
```

### 3. Start All Services

```bash
docker compose up --build
```

### 4. Access Your App

| Service   | URL                     |
|-----------|--------------------------|
| Frontend  | http://localhost:3000    |
| Backend   | http://localhost:8890    |
| AI Engine | http://localhost:9000    |

---

## 🔐 Authentication

JWT-based login/logout is built-in.

---

## 📄 Features (Roadmap)

- ✅ Upload PDF/Doc
- ✅ Extract & Embed content
- ✅ Ask AI / search inside documents
- ⏳ Email/document sync
- ⏳ PDF viewer with highlights
- ⏳ SaaS: Org-wise document segmentation

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Make changes and commit
4. Push and create a PR

---

## 📝 License
MIT

---

## 👨‍💻 Author
Built with ❤️ by [Tanvir Haque](https://github.com/TanvirHaqueSagor)